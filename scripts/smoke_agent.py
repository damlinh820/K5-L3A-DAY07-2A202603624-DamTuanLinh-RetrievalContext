"""LEGACY fixed-generation smoke; current tool-calling entry point is src.cli ask."""
import argparse
import json
import os
import sys
from pathlib import Path

import chromadb
import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agent import OpenRouterAgent
from src.retrieval import BM25Retriever, reciprocal_rank_fusion


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chunks", type=Path, required=True); p.add_argument("--case", type=Path, required=True)
    p.add_argument("--env", type=Path, required=True); p.add_argument("--chroma", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True); args = p.parse_args()
    load_dotenv(args.env)
    chunks = [json.loads(x) for x in args.chunks.read_text(encoding="utf-8").splitlines() if x.strip()]
    case = json.loads(args.case.read_text(encoding="utf-8"))
    bm_chunks = [{"id": c["chunk_id"], "text": c["text"], "source_id": c["document_id"], "source": c["source"],
                  "page": c["page"], "metadata": {"part": c["part"], "article": c.get("article"), "clause": c.get("clause")}} for c in chunks]
    bm = BM25Retriever(bm_chunks)
    coll = chromadb.PersistentClient(path=str(args.chroma), settings=chromadb.config.Settings(anonymized_telemetry=False)).get_collection("day6_c_dense")
    def search(query, mode="hybrid_rrf", top_k=3):
        with httpx.Client(timeout=60) as client:
            r = client.post("https://openrouter.ai/api/v1/embeddings", json={"model": "openai/text-embedding-3-small", "input": [query]}, headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]})
            r.raise_for_status(); vector = r.json()["data"][0]["embedding"]
        raw = coll.query(query_embeddings=[vector], n_results=10, include=["documents", "metadatas", "distances"])
        dense = [{"id": cid, "text": text, "source_id": meta["document_id"], "source": meta["source"], "page": meta["page"], "metadata": meta, "score": 1-float(dist)} for cid,text,meta,dist in zip(raw["ids"][0],raw["documents"][0],raw["metadatas"][0],raw["distances"][0])]
        lexical = bm.search(query, top_k=10)
        return reciprocal_rank_fusion({"dense": dense, "bm25": lexical}, top_k=top_k)
    result = OpenRouterAgent(search, model="gpt-4o-mini", provider="openai", max_rounds=1, top_k=3).run(case["question"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"query_id": case["id"], "result": result}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"query_id": case["id"], "status": result["status"], "citations": result["citations"], "usage": result["usage"]}, ensure_ascii=False))


if __name__ == "__main__": main()
