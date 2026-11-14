"""Evidence context construction with deterministic budget handling."""
from __future__ import annotations


def build_context(chunks: list[dict], *, budget_chars: int = 6000) -> tuple[str, list[str], list[str]]:
    if budget_chars < 1:
        raise ValueError("budget_chars không hợp lệ")
    blocks, ids, dropped, seen = [], [], [], set()
    ordered = sorted(enumerate(chunks), key=lambda pair: (-float(pair[1].get("score", 0)), pair[0]))
    for _, chunk in ordered:
        cid = str(chunk["id"])
        if cid in seen:
            continue
        seen.add(cid)
        block = (f"[{cid}] {chunk.get('source', 'unknown')} | page {chunk.get('page', 'unknown')}"
                 f" | Điều {chunk.get('metadata', {}).get('article', '')}"
                 f" | Khoản {chunk.get('metadata', {}).get('clause', '')}\n{chunk['text']}")
        candidate = "\n\n".join(blocks + [block])
        if len(candidate) <= budget_chars:
            blocks.append(block)
            ids.append(cid)
        else:
            dropped.append(cid)
    return "\n\n".join(blocks), ids, dropped
