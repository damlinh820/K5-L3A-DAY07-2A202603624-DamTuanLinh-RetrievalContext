"""Deterministic Day 7 retrieval primitives.

The module deliberately keeps the dense backend as an adapter: the Day 6
Chroma index and embedding provider are external dependencies and must not be
silently replaced. BM25 is implemented transparently with the same frozen
chunk records, and RRF combines ranked results without comparing incompatible
score scales.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence


_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def tokenize_vietnamese(text: str) -> list[str]:
    """Return deterministic Unicode-aware tokens, preserving accents/numbers."""
    return _TOKEN_RE.findall(unicodedata.normalize("NFC", text).casefold())


def _validate_chunk(chunk: Mapping) -> None:
    for key in ("id", "text", "source_id", "source", "page", "metadata"):
        if key not in chunk:
            raise ValueError(f"chunk thiếu {key}")
    if not isinstance(chunk["id"], str) or not chunk["id"].strip():
        raise ValueError("chunk id phải là chuỗi không rỗng")
    if not isinstance(chunk["text"], str) or not chunk["text"].strip():
        raise ValueError("chunk text phải là chuỗi không rỗng")


def _with_result(chunk: Mapping, *, score: float, rank: int, strategy: str) -> dict:
    return {**chunk, "score": float(score), "rank": rank, "strategy": strategy}


class BM25Retriever:
    """Small transparent BM25 implementation over frozen chunk records."""

    def __init__(self, chunks: Sequence[Mapping], *, k1: float = 1.5, b: float = 0.75):
        if not chunks:
            raise ValueError("chunks không được rỗng")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("BM25 k1/b không hợp lệ")
        for chunk in chunks:
            _validate_chunk(chunk)
        ids = [str(chunk["id"]) for chunk in chunks]
        if len(ids) != len(set(ids)):
            raise ValueError("chunk ID bị trùng")
        self.chunks = list(chunks)
        self.k1, self.b = k1, b
        self.tokens = [tokenize_vietnamese(str(c["text"])) for c in self.chunks]
        self.lengths = [len(row) for row in self.tokens]
        self.avgdl = sum(self.lengths) / len(self.lengths) or 1.0
        self.tf = [Counter(row) for row in self.tokens]
        df = Counter(term for row in self.tf for term in row)
        n = len(self.chunks)
        self.idf = {term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}

    def search(self, query: str, *, top_k: int = 3, filters: Mapping | None = None) -> list[dict]:
        if not isinstance(query, str) or not query.strip() or top_k < 1:
            raise ValueError("query/top_k không hợp lệ")
        query_terms = tokenize_vietnamese(query)
        results = []
        for chunk, counts, dl in zip(self.chunks, self.tf, self.lengths):
            if filters and any(chunk.get("metadata", {}).get(k) != v for k, v in filters.items()):
                continue
            score = 0.0
            for term in query_terms:
                if term not in counts:
                    continue
                freq = counts[term]
                denom = freq + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += self.idf.get(term, 0.0) * freq * (self.k1 + 1) / denom
            if score > 0:
                results.append((score, str(chunk["id"]), chunk))
        results.sort(key=lambda row: (-row[0], row[1]))
        return [_with_result(chunk, score=score, rank=rank, strategy="bm25")
                for rank, (score, _, chunk) in enumerate(results[:top_k], 1)]


class DenseUnavailable(RuntimeError):
    """Raised when the approved Day 6 dense backend is not configured."""


class DenseRetriever:
    """Adapter around an approved Day 6 search function.

    ``search_fn`` receives ``(query, top_k, filters)`` and must return records
    with the common chunk schema plus a numeric score. No mock fallback exists.
    """

    def __init__(self, search_fn: Callable | None = None):
        self.search_fn = search_fn

    def search(self, query: str, *, top_k: int = 3, filters: Mapping | None = None) -> list[dict]:
        if self.search_fn is None:
            raise DenseUnavailable("Day 6 Chroma/embedding adapter is not configured")
        raw = self.search_fn(query, top_k, filters)
        if len(raw) > top_k:
            raise ValueError("dense backend trả quá top_k")
        seen = set()
        output = []
        for rank, item in enumerate(raw, 1):
            _validate_chunk(item)
            if item["id"] in seen:
                raise ValueError("dense backend trả chunk ID trùng")
            seen.add(item["id"])
            output.append(_with_result(item, score=float(item["score"]), rank=rank, strategy="dense"))
        return output


def reciprocal_rank_fusion(result_sets: Mapping[str, Sequence[Mapping]], *, rrf_k: int = 60,
                           top_k: int = 3) -> list[dict]:
    """Fuse ranked results; preserve source ranks/scores and deterministic ties."""
    if rrf_k < 1 or top_k < 1:
        raise ValueError("rrf_k/top_k không hợp lệ")
    merged: dict[str, dict] = {}
    for strategy, results in result_sets.items():
        for position, item in enumerate(results, 1):
            _validate_chunk(item)
            chunk_id = str(item["id"])
            entry = merged.setdefault(chunk_id, {**item, "rrf_score": 0.0, "source_ranks": {}, "source_scores": {}})
            entry["rrf_score"] += 1.0 / (rrf_k + position)
            entry["source_ranks"][strategy] = position
            entry["source_scores"][strategy] = float(item.get("score", 0.0))
    ordered = sorted(merged.values(), key=lambda item: (-item["rrf_score"], str(item["id"])))
    return [{**item, "score": item["rrf_score"], "rank": rank, "strategy": "hybrid_rrf"}
            for rank, item in enumerate(ordered[:top_k], 1)]


class HybridRetriever:
    def __init__(self, dense: DenseRetriever, bm25: BM25Retriever, *, candidate_k: int = 10, rrf_k: int = 60):
        self.dense, self.bm25 = dense, bm25
        self.candidate_k, self.rrf_k = candidate_k, rrf_k

    def search(self, query: str, *, top_k: int = 3, filters: Mapping | None = None) -> list[dict]:
        dense_results = self.dense.search(query, top_k=self.candidate_k, filters=filters)
        bm25_results = self.bm25.search(query, top_k=self.candidate_k, filters=filters)
        return reciprocal_rank_fusion({"dense": dense_results, "bm25": bm25_results},
                                     rrf_k=self.rrf_k, top_k=top_k)


def transform_legal_query(query: str) -> list[str]:
    """Generate deterministic legal query variants without using gold data."""
    variants = [query.strip()]
    normalized = re.sub(r"\s+", " ", query).strip()
    if normalized not in variants:
        variants.append(normalized)
    article = re.search(r"điều\s+(\d+)", normalized, re.IGNORECASE)
    clause = re.search(r"khoản\s+(\d+)", normalized, re.IGNORECASE)
    if article:
        locator = "Điều " + article.group(1)
        if clause:
            locator += " khoản " + clause.group(1)
        variants.append(locator)
    return list(dict.fromkeys(v for v in variants if v))


def metadata_aware_rerank(query: str, candidates: Sequence[Mapping], *, top_k: int = 3) -> list[dict]:
    """Boost exact article/clause locators while preserving evidence scores."""
    article = re.search(r"điều\s+(\d+)", query, re.IGNORECASE)
    clause = re.search(r"khoản\s+(\d+)", query, re.IGNORECASE)
    scored = []
    for item in candidates:
        meta = item.get("metadata", {})
        bonus = 0.0
        if article and str(meta.get("article", "")) == article.group(1): bonus += 0.15
        if clause and str(meta.get("clause", "")) == clause.group(1): bonus += 0.08
        scored.append((float(item.get("score", 0)) + bonus, str(item["id"]), item, bonus))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [{**item, "score": score, "metadata_bonus": bonus, "rank": rank,
             "strategy": "metadata_aware"} for rank, (score, _, item, bonus) in enumerate(scored[:top_k], 1)]


def expand_neighbors(results: Sequence[Mapping], chunks: Sequence[Mapping], *, window: int = 1,
                     top_k: int = 3) -> list[dict]:
    """Add adjacent chunks from the same document/article for legal conditions."""
    by_doc = {}
    for c in chunks:
        by_doc.setdefault((c.get("source_id"), str(c.get("metadata", {}).get("article", ""))), []).append(c)
    for group in by_doc.values(): group.sort(key=lambda c: (int(c.get("page", 0)), str(c["id"])))
    chosen = {str(r["id"]): dict(r) for r in results}
    for r in list(results):
        group = by_doc.get((r.get("source_id"), str(r.get("metadata", {}).get("article", ""))), [])
        try: pos = next(i for i, c in enumerate(group) if str(c["id"]) == str(r["id"]))
        except StopIteration: continue
        for neighbor in group[max(0, pos-window):pos+window+1]:
            chosen.setdefault(str(neighbor["id"],), {**neighbor, "score": float(r.get("score", 0)) - 0.01,
                                                        "strategy": "neighbor_expansion", "rank": 999})
    ordered = sorted(chosen.values(), key=lambda x: (-float(x.get("score", 0)), str(x["id"])))
    return [{**x, "rank": i} for i, x in enumerate(ordered[:top_k], 1)]
