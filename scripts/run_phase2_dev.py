"""LEGACY: original dev retrieval and page-start metrics; use src.cli for new runs."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import chromadb
import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.retrieval import BM25Retriever, DenseRetriever, reciprocal_rank_fusion, transform_legal_query, metadata_aware_rerank, expand_neighbors
from src.rerank import lexical_rerank


MODEL = "openai/text-embedding-3-small"


def embed_queries(client, key, queries):
    response = client.post("https://openrouter.ai/api/v1/embeddings",
                           json={"model": MODEL, "input": queries},
                           headers={"Authorization": f"Bearer {key}"})
    response.raise_for_status()
    rows = sorted(response.json()["data"], key=lambda row: row["index"])
    return [row["embedding"] for row in rows], response.json().get("usage", {})


def common_chunk(row, doc, meta):
    return {"id": row, "text": doc, "source_id": meta["document_id"], "source": meta["source"],
            "page": meta["page"], "metadata": {"part": meta["part"], "article": meta.get("article", ""),
            "clause": meta.get("clause", "")}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks", type=Path, required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--chroma", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    args = parser.parse_args()
    if args.split=='test': raise ValueError('Legacy test execution disabled; use src.cli eval with its approval guards')
    if args.output.exists(): raise ValueError('Preserve existing artifacts; choose a new output directory')
    load_dotenv(args.env)
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is missing")
    chunks = [json.loads(line) for line in args.chunks.read_text(encoding="utf-8").splitlines() if line.strip()]
    questions = [json.loads(line) for line in args.questions.read_text(encoding="utf-8").splitlines() if line.strip()]
    dev = [q for q in questions if q["split"] == args.split and q.get("answerability") == "answerable"]
    if any(q["answerability"] if "answerability" in q else "answerable" for q in []):
        raise RuntimeError("unexpected benchmark schema")
    bm_chunks = [{"id": c["chunk_id"], "text": c["text"], "source_id": c["document_id"], "source": c["source"],
                  "page": c["page"], "metadata": {"part": c["part"], "article": c.get("article"), "clause": c.get("clause")}}
                 for c in chunks]
    bm25 = BM25Retriever(bm_chunks)
    chroma = chromadb.PersistentClient(path=str(args.chroma), settings=chromadb.config.Settings(anonymized_telemetry=False))
    collection = chroma.get_collection("day6_c_dense")
    traces = []
    usage = None
    with httpx.Client(timeout=httpx.Timeout(120, connect=30)) as client:
        vectors, usage = embed_queries(client, key, [q["question"] for q in dev])
        for q, vector in zip(dev, vectors):
            started = time.perf_counter()
            raw = collection.query(query_embeddings=[vector], n_results=10,
                                   include=["documents", "metadatas", "distances"])
            dense = []
            for rank, (cid, doc, meta, distance) in enumerate(zip(raw["ids"][0], raw["documents"][0], raw["metadatas"][0], raw["distances"][0]), 1):
                dense.append({**common_chunk(cid, doc, meta), "score": 1 - float(distance), "rank": rank, "strategy": "dense"})
            bm = bm25.search(q["question"], top_k=10)
            hybrid = reciprocal_rank_fusion({"dense": dense, "bm25": bm}, top_k=3)
            transformed = []
            for variant in transform_legal_query(q["question"]):
                transformed.extend(bm25.search(variant, top_k=10))
            transformed = sorted({str(x["id"]): x for x in transformed}.values(), key=lambda x: (-float(x.get("score", 0)), str(x["id"])))
            improved_pool = reciprocal_rank_fusion({"dense": dense, "bm25_transformed": transformed}, top_k=10)
            improved = metadata_aware_rerank(q["question"], improved_pool, top_k=3)
            improved = expand_neighbors(improved, bm_chunks, window=1, top_k=3)
            hybrid20 = reciprocal_rank_fusion({"dense": dense, "bm25": bm25.search(q["question"], top_k=20)}, top_k=20)
            reranked = lexical_rerank(q["question"], hybrid20, top_k=3)
            gold = q["gold"]
            def hit(row):
                return any(row["source_id"] == g["source_id"] and row["page"] == g["page"] and
                           " ".join(row["text"].split()).find(" ".join(g["evidence_quote"].split())) >= 0 for g in gold)
            results = {"dense": dense[:3], "bm25": bm[:3], "hybrid_rrf": hybrid,
                       "hybrid_rrf_candidate20": hybrid20[:3],
                       "hybrid_rrf_lexical_rerank": reranked,
                       "hybrid_improved_all5": improved}
            traces.append({"query_id": q["id"], "question": q["question"], "gold": gold,
                           "results": results, "hit1": {m: bool(rows and hit(rows[0])) for m, rows in results.items()},
                           "hit3": {m: any(hit(row) for row in rows) for m, rows in results.items()},
                           "elapsed_ms": (time.perf_counter() - started) * 1000})
    summary = {"split": args.split, "n": len(traces), "answerable_n": len(traces),
               "usage": usage, "metrics": {}}
    for mode in ("dense", "bm25", "hybrid_rrf", "hybrid_rrf_candidate20", "hybrid_rrf_lexical_rerank", "hybrid_improved_all5"):
        summary["metrics"][mode] = {"hit1": sum(t["hit1"][mode] for t in traces),
                                     "hit3": sum(t["hit3"][mode] for t in traces),
                                     "hit1_rate": sum(t["hit1"][mode] for t in traces) / len(traces),
                                     "hit3_rate": sum(t["hit3"][mode] for t in traces) / len(traces)}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
