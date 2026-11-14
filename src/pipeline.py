"""Shared, query-only legal retrieval; no benchmark labels enter this module."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path

from .retrieval import BM25Retriever, reciprocal_rank_fusion


def normalize_chunk(c: dict) -> dict:
    return {'id': c['chunk_id'], 'text': c['text'], 'source_id': c['document_id'],
            'source': c['source'], 'page': c['page'], 'page_end': c['page_end'],
            'provenance': c.get('provenance', []), 'body_start': c.get('body_start', 0),
            'metadata': {k: c.get(k) for k in ('article', 'clause', 'part')}}


def query_variants(query: str) -> list[str]:
    """Keep original and remove incidental legal references from a focus query."""
    focus = re.sub(r'(?:trong|theo)\s+hạn mức\s+(?:quy định tại\s+)?Điều\s+\d+', '', query, flags=re.I)
    focus = re.sub(r'Chỉ (?:tra cứu|dùng) phần\s+\d+[^:]*:\s*', '', focus, flags=re.I)
    focus = re.sub(r'\s+', ' ', focus).strip()
    return list(dict.fromkeys([query, focus]))


def requested_fields(query: str) -> list[str]:
    """Infer information types from question wording, never an expected answer."""
    fields = []
    if re.search(r'bao lâu|thời hạn|thời gian|bao nhiêu (?:năm|tháng|ngày)', query, re.I): fields.append('duration')
    if re.search(r'gia hạn', query, re.I): fields.append('renewal')
    return fields


def field_coverage(text: str, fields: list[str]) -> int:
    coverage = {'duration': bool(re.search(r'(?:\d+\s*(?:năm|tháng|ngày)|ổn định lâu dài)', text, re.I)),
                'renewal': bool(re.search(r'gia hạn', text, re.I))}
    return sum(coverage.get(f, False) for f in fields)


class LegalPipeline:
    def __init__(self, chunks: list[dict], dense_search, *, candidate_k: int = 10):
        self.chunks = chunks
        self.dense_search = dense_search
        self.bm25 = BM25Retriever(chunks)
        self.candidate_k = candidate_k
        self.last_trace = {}

    def search(self, query: str, *, mode: str = 'hybrid_improved', top_k: int = 3) -> list[dict]:
        if mode not in {'dense', 'bm25', 'hybrid_rrf', 'hybrid_improved', 'hybrid_rerank'}:
            raise ValueError('Unsupported retrieval mode')
        if not query.strip() or not 1 <= top_k <= 20: raise ValueError('Invalid query/top_k')
        part = re.search(r'\bphần\s+(\d+)\b', query, re.I)
        filters = {'part': int(part.group(1))} if part else None
        variants = query_variants(query) if mode == 'hybrid_improved' else [query]
        rankings = {}
        for i, variant in enumerate(variants):
            if mode != 'bm25':
                rankings[f'dense_{i}'] = self.dense_search(variant, self.candidate_k, filters)
            if mode != 'dense':
                rankings[f'bm25_{i}'] = self.bm25.search(variant, top_k=self.candidate_k, filters=filters)
        if mode in {'dense', 'bm25'}:
            pool = next(iter(rankings.values()))
        else:
            pool = reciprocal_rank_fusion(rankings, top_k=self.candidate_k * len(rankings))
        locator = re.search(r'(?:khoản\s+(\d+)\s+)?Điều\s+(\d+)', query, re.I)
        # An incidental reference (e.g. area limit) is not a restriction on the answer article.
        incidental = bool(re.search(r'hạn mức\s+(?:quy định tại\s+)?Điều\s+\d+', query, re.I))
        if mode == 'hybrid_improved' and locator and not incidental:
            clause, article = locator.groups()
            exact = [c for c in self.chunks if str(c['metadata'].get('article')) == article
                     and (not clause or str(c['metadata'].get('clause')) == clause)
                     and (not filters or c['metadata'].get('part') == filters['part'])]
            # Fuse a separate lookup ranking rather than adding BM25 to cosine scores.
            exact = sorted(exact, key=lambda c: (-sum(t in c['text'].casefold() for t in query.casefold().split()),
                                                c['body_start'], c['id']))
            pool = reciprocal_rank_fusion({'retrieval': pool, 'explicit_locator': exact}, top_k=len(pool)+len(exact))
        fields = requested_fields(query) if mode == 'hybrid_improved' else []
        if fields:
            # A rare cross-reference must not outrank a passage containing the requested fields.
            pool = sorted(pool, key=lambda c: (-field_coverage(c['text'], fields),
                                              -float(c.get('score', 0)), c['id']))
        if mode == 'hybrid_rerank':
            from .rerank import lexical_rerank
            pool = lexical_rerank(query, pool, top_k=max(top_k, self.candidate_k))
        self.last_trace = {'original_query': query, 'variants': variants, 'filters': filters,
                           'source_rankings': rankings, 'mode': mode, 'requested_fields': fields}
        return [{**c, 'rank': i, 'strategy': mode} for i, c in enumerate(pool[:top_k], 1)]

    def expand_context(self, results: list[dict]) -> list[dict]:
        """Append adjacent source-position chunks; ranked top-3 stays first."""
        output, seen = list(results), {c['id'] for c in results}
        for seed in results:
            article = seed['metadata'].get('article')
            if not article: continue
            group = sorted([c for c in self.chunks if c['source_id'] == seed['source_id']
                            and c['metadata'].get('article') == article],
                           key=lambda c: (c['body_start'], c['id']))
            pos = next(i for i, c in enumerate(group) if c['id'] == seed['id'])
            for c in group[max(0, pos-1):pos+2]:
                if c['id'] not in seen and len(output) < 6:
                    output.append({**c, 'score': -1, 'strategy': 'neighbor_expansion', 'parent_id': seed['id']})
                    seen.add(c['id'])
        return output


class Day6DenseBackend:
    """Read existing Chroma, validate fingerprint, cache query vectors and usage."""
    MODEL = 'openai/text-embedding-3-small'

    def __init__(self, chroma_path: Path, corpus: Path, cache_dir: Path):
        import chromadb
        self.client = chromadb.PersistentClient(path=str(chroma_path), settings=chromadb.config.Settings(anonymized_telemetry=False))
        self.collection = self.client.get_collection('day6_c_dense')
        corpus_hash = hashlib.sha256(corpus.read_bytes()).hexdigest()
        if self.collection.metadata.get('corpus_sha256') != corpus_hash:
            raise ValueError('Index/corpus fingerprint mismatch')
        if self.collection.metadata.get('model') != self.MODEL:
            raise ValueError('Embedding model mismatch')
        self.lookup = {c['chunk_id']: normalize_chunk(c) for c in map(json.loads, corpus.read_text(encoding='utf8').splitlines())}
        if set(self.collection.get(include=[])['ids']) != set(self.lookup):
            raise ValueError('Index/corpus IDs mismatch')
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = cache_dir / 'query_vectors.jsonl'
        self.cache = {}
        if self.cache_path.exists():
            self.cache = {r['key']: r['vector'] for r in map(json.loads, self.cache_path.read_text(encoding='utf8').splitlines())}
        self.usage = []

    def __call__(self, query: str, top_k: int, filters: dict | None) -> list[dict]:
        import httpx
        key = hashlib.sha256((self.MODEL+'\0'+query).encode()).hexdigest()
        if key not in self.cache:
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key: raise RuntimeError('OPENROUTER_API_KEY missing')
            with httpx.Client(timeout=60) as http:
                r = http.post('https://openrouter.ai/api/v1/embeddings',
                              json={'model': self.MODEL, 'input': [query]},
                              headers={'Authorization': 'Bearer '+api_key})
                if r.is_error: raise RuntimeError(f'Embedding API HTTP {r.status_code}')
                body = r.json()
            if body.get('model') not in {self.MODEL, self.MODEL.split('/', 1)[-1]}:
                raise ValueError('Response embedding model mismatch')
            vector = body['data'][0]['embedding']
            if len(vector) != 1536 or not all(math.isfinite(float(v)) for v in vector) or not any(vector):
                raise ValueError('Invalid query embedding')
            usage = {'query_hash': key, 'usage': body.get('usage', {})}
            self.usage.append(usage)
            with (self.cache_dir/'embedding_usage.jsonl').open('a', encoding='utf8') as f:
                f.write(json.dumps(usage)+'\n')
            with self.cache_path.open('a', encoding='utf8') as f:
                f.write(json.dumps({'key': key, 'vector': vector})+'\n')
            self.cache[key] = vector
        raw = self.collection.query(query_embeddings=[self.cache[key]], n_results=min(top_k, len(self.lookup)),
                                    where=filters, include=['documents', 'metadatas', 'distances'])
        output = []
        for cid, text, meta, distance in zip(raw['ids'][0], raw['documents'][0], raw['metadatas'][0], raw['distances'][0]):
            original = self.lookup[cid]
            if text != original['text'] or meta.get('document_id') != original['source_id']:
                raise ValueError('Index text/source mismatch')
            output.append({**original, 'score': 1-float(distance), 'strategy': 'dense', 'score_type': 'cosine_similarity'})
        return output
