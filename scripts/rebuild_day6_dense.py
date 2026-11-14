"""Rebuild a Day 7-local Chroma index from the immutable Day 6 C snapshot.

Uses the Day 6 locked OpenRouter embedding model and records actual usage. The
script never writes to the Day 6 repository and refuses missing credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import chromadb
import httpx
from dotenv import load_dotenv


MODEL = "openai/text-embedding-3-small"
DIMENSIONS = 1536


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def embed(client: httpx.Client, key: str, texts: list[str]) -> tuple[list[list[float]], dict]:
    response = client.post(
        "https://openrouter.ai/api/v1/embeddings",
        json={"model": MODEL, "input": texts},
        headers={"Authorization": f"Bearer {key}"},
    )
    response.raise_for_status()
    body = response.json()
    if body.get("model") not in {MODEL, MODEL.split("/", 1)[-1]}:
        raise RuntimeError("Embedding response model differs from locked model")
    rows = sorted(body.get("data", []), key=lambda row: row["index"])
    if len(rows) != len(texts) or [r['index'] for r in rows]!=list(range(len(texts))):
        raise RuntimeError("Embedding response count mismatch")
    vectors = [row["embedding"] for row in rows]
    if any(len(vector) != DIMENSIONS or not all(math.isfinite(float(v)) for v in vector) or not any(vector) for vector in vectors):
        raise RuntimeError("Embedding dimension mismatch")
    return vectors, body.get("usage", {})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-input-tokens", type=int, default=1000000)
    args = parser.parse_args()
    load_dotenv(args.env)
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is missing")

    chunks = [json.loads(line) for line in args.chunks.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not chunks or len({c["chunk_id"] for c in chunks}) != len(chunks):
        raise ValueError("Invalid or duplicate Day 6 chunk IDs")
    if sum(c['n_tokens'] for c in chunks)>args.max_input_tokens:
        raise ValueError('Corpus exceeds configured input token budget')
    args.output.mkdir(parents=True, exist_ok=False)
    chroma_path = args.output / "chroma"
    client = chromadb.PersistentClient(path=str(chroma_path), settings=chromadb.config.Settings(anonymized_telemetry=False))
    collection = client.get_or_create_collection(
        "day6_c_dense", configuration={"hnsw": {"space": "cosine"}},
        metadata={"model": MODEL, "dimensions": DIMENSIONS, "corpus_sha256": sha256(args.chunks)},
    )

    usage_rows = []
    all_vectors = []
    with httpx.Client(timeout=httpx.Timeout(120, connect=30)) as http:
        for start in range(0, len(chunks), 32):
            batch = chunks[start:start + 32]
            vectors, usage = embed(http, key, [c["text"] for c in batch])
            all_vectors.extend(vectors)
            usage_rows.append({"batch_start": start, "inputs": len(batch), "usage": usage})
            with (args.output/'embedding_usage.jsonl').open('a',encoding='utf8') as stream:
                stream.write(json.dumps(usage_rows[-1])+'\n')
            print(f"embedded {start + len(batch)}/{len(chunks)}", flush=True)
            time.sleep(0.05)
    for start in range(0, len(chunks), 128):
        batch = chunks[start:start + 128]
        collection.upsert(
            ids=[c["chunk_id"] for c in batch], documents=[c["text"] for c in batch],
            embeddings=all_vectors[start:start + 128],
            metadatas=[{"document_id": c["document_id"], "source": c["source"], "part": c["part"],
                        "page": c["page"], "page_end": c["page_end"], "article": str(c.get("article") or ""),
                        "clause": str(c.get("clause") or "")} for c in batch],
        )
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "status": "built",
        "model": MODEL, "dimensions": DIMENSIONS, "metric": "cosine",
        "chunks": len(chunks), "collection": "day6_c_dense", "chroma_path": str(chroma_path),
        "corpus_path": str(args.chunks), "corpus_sha256": sha256(args.chunks),
        "usage": usage_rows, "actual_usage_total": {
            "total_tokens": sum(row['usage']['total_tokens'] for row in usage_rows) if all('total_tokens' in row['usage'] for row in usage_rows) else None,
            "cost_usd": sum(row['usage']['cost'] for row in usage_rows) if all('cost' in row['usage'] for row in usage_rows) else None,
        },
        "count_persisted": collection.count(),
    }
    (args.output / "dense_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("chunks", "count_persisted", "actual_usage_total")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
