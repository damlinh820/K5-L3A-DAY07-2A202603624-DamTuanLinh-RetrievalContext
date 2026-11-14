"""Create a Day 7 benchmark copy without mutating Day 6 files.

The four insufficient-evidence cases are intentionally provisional until H1.
This script copies the original answerable cases and normalizes them into the
Day 7 schema while preserving original IDs, evidence and split.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day6", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = args.day6 / "benchmark/questions.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    if len(rows) != 20 or len(candidates) != 4:
        raise ValueError("Expected 20 Day 6 answerable cases and 4 provisional candidates")
    if {row["id"] for row in rows} & {row["id"] for row in candidates}:
        raise ValueError("Benchmark IDs must be unique")

    corpus_hash = sha256(args.corpus)
    converted = []
    for row in rows:
        converted.append({
            "case_id": row["id"], "id": row["id"], "split": row["split"],
            "type": row["type"], "question": row["question"],
            "answerability": "answerable", "expected_evidence_ids": [],
            "source_document_ids": [row["gold_source_id"]],
            "gold_article": row["legal_locator"], "gold_clause": None,
            "gold_pages": [row["gold_page"]],
            "reference_answer": row["expected_answer"],
            "gold_status": "pending_human_review",
            "reviewer": row.get("human_review"), "review_timestamp": None,
            "review_reason": "Copied from immutable Day 6 benchmark; semantic review status must be confirmed for Day 7.",
            "corpus_hash": corpus_hash, "gold": row["gold_evidence"],
            "filter": row.get("filter", {}), "source_day6_id": row["id"],
        })
    converted.extend({**candidate, "case_id": candidate["id"], "expected_evidence_ids": [],
                      "source_document_ids": [], "gold_article": None, "gold_clause": None,
                      "gold_pages": [], "reference_answer": None, "corpus_hash": corpus_hash}
                     for candidate in candidates)

    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output / "lab7_benchmark.jsonl"
    out.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in converted) + "\n", encoding="utf-8")
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "provisional_pending_H1", "source_day6": str(source),
        "source_day6_sha256": sha256(source), "candidate_source": str(args.candidates),
        "corpus_path": str(args.corpus), "corpus_sha256": corpus_hash,
        "output_sha256": sha256(out), "counts": {
            "total": len(converted), "answerable": sum(r["answerability"] == "answerable" for r in converted),
            "insufficient_evidence": sum(r["answerability"] == "insufficient_evidence" for r in converted),
            "dev": sum(r["split"] == "dev" for r in converted),
            "test": sum(r["split"] == "test" for r in converted)},
        "human_approval": {"h1": False, "reviewer": None, "approved_at": None, "notes": None},
    }
    (args.output / "benchmark_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
