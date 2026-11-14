"""Structural citation checks; semantic support remains human-reviewed."""
from __future__ import annotations

import re


def validate_citations(answer: str, citations: list[str], context_ids: list[str], context: str) -> dict:
    supplied = set(context_ids)
    structural = []
    for cid in citations:
        present = cid in supplied
        marked = f"[{cid}]" in answer
        excerpt_present = present and cid in context
        structural.append({"id": cid, "in_context": present, "marked_in_answer": marked,
                           "excerpt_present": excerpt_present,
                           "syntactically_valid": present and marked and excerpt_present})
    return {"all_structurally_valid": bool(citations) and all(x["syntactically_valid"] for x in structural),
            "citations": structural, "semantic_support": "human_review_required"}


def extract_citation_ids(answer: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\[([^\[\]]+)\]", answer)))
