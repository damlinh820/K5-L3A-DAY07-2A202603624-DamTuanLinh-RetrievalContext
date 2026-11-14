"""Transparent, offline reranking improvement for dev experiments.

This is not a neural cross-encoder. It is deliberately labelled lexical
reranking: query-term coverage plus a small exact article-number bonus.
"""
from __future__ import annotations

import re

from .retrieval import tokenize_vietnamese


def lexical_rerank(query: str, candidates: list[dict], *, top_k: int = 3) -> list[dict]:
    terms = set(tokenize_vietnamese(query))
    article = next(iter(re.findall(r"điều\s+(\d+)", query.casefold())), None)
    scored = []
    for item in candidates:
        text_terms = set(tokenize_vietnamese(item["text"]))
        overlap = len(terms & text_terms) / max(len(terms), 1)
        article_bonus = 0.05 if article and str(item.get("metadata", {}).get("article", "")) == article else 0.0
        score = overlap + article_bonus
        scored.append((score, str(item["id"]), item))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [{**item, "score": score, "rank": rank, "strategy": "hybrid_lexical_rerank",
             "rerank_score": score, "rerank_reason": "query term coverage + exact article bonus"}
            for rank, (score, _, item) in enumerate(scored[:top_k], 1)]
