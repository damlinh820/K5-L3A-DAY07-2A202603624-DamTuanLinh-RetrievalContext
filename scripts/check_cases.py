"""LEGACY fixed-generation diagnostic on selected, already exposed cases.

No gold is sent to retrieval/generation. Labels are inspected only afterwards
to audit evidence placement; semantic grades stay pending human review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.agent import OpenRouterAgent
from src.pipeline import Day6DenseBackend, LegalPipeline, normalize_chunk


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_audit(case: dict, result: dict, chunks: dict) -> dict:
    norm = lambda s: ' '.join(s.split())
    expected = []
    for g in case.get('gold', []):
        for c in chunks.values():
            pages = {p['page'] for p in c.get('provenance', [])} | {c['page']}
            if c['source_id'] == g['source_id'] and g['page'] in pages and norm(g['evidence_quote']) in norm(c['text']):
                expected.append(c['id'])
    ranked = [c['id'] for c in result.get('events', [{}])[0].get('results', [])]
    supplied = result.get('context_ids', [])
    return {'gold_chunk_ids': sorted(set(expected)),
            'gold_in_top3': bool(set(expected) & set(ranked[:3])),
            'gold_in_context': any(cid in supplied and any(norm(g['evidence_quote']) in norm(result.get('context', ''))
                                   for g in case.get('gold', [])) for cid in expected),
            'semantic_support': 'pending_human_review'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--chunks', type=Path, required=True)
    p.add_argument('--questions', type=Path, required=True)
    p.add_argument('--env', type=Path, required=True)
    p.add_argument('--chroma', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--ids', nargs='+', required=True)
    p.add_argument('--mode', choices=['dense', 'bm25', 'hybrid_rrf', 'hybrid_improved'], default='hybrid_improved')
    a = p.parse_args()
    cases = [json.loads(line) for line in a.questions.read_text(encoding='utf8').splitlines() if line.strip()]
    selected = [c for c in cases if c['id'] in a.ids]
    if set(a.ids) != {c['id'] for c in selected}: raise ValueError('Unknown case IDs')
    # Existing artifacts must never be overwritten by a replay.
    a.output.mkdir(parents=True, exist_ok=False)
    load_dotenv(a.env)
    raw = [json.loads(line) for line in a.chunks.read_text(encoding='utf8').splitlines() if line.strip()]
    chunks = [normalize_chunk(c) for c in raw]
    backend = Day6DenseBackend(a.chroma, a.chunks, a.output)
    pipeline = LegalPipeline(chunks, backend)
    config = {'mode': a.mode, 'candidate_k': 10, 'rrf_k': 60, 'top_k': 3,
              'context_budget_chars': 6000, 'context_expansion_max': 6, 'max_chat_calls_per_case': 2,
              'max_completion_tokens_per_call': 1000, 'model': 'gpt-4o-mini', 'temperature': 0}
    manifest = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'running',
                'evaluation_type': 'diagnostic_replay_exposed_test', 'case_ids': a.ids,
                'corpus_sha256': digest(a.chunks), 'benchmark_sha256': digest(a.questions),
                'config': config, 'config_sha256': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
                'code_hashes': {f: digest(ROOT/f) for f in ['src/agent.py', 'src/pipeline.py', 'src/context.py',
                                                         'src/citation.py', 'prompts/grounded_answer_v2.txt']},
                'semantic_review_status': 'pending_human_review', 'chat_cost_usd': None}
    def save(name, data):
        (a.output/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    save('manifest.json', manifest)
    output = []
    for case in selected:
        pipeline.last_trace = {}
        try:
            agent = OpenRouterAgent(pipeline.search, model='gpt-4o-mini', provider='openai', max_rounds=1,
                                    context_expander=pipeline.expand_context if a.mode=='hybrid_improved' else None)
            result = agent.run(case['question'], mode=a.mode)
        except Exception as exc:
            result = {'status': 'error', 'error_type': type(exc).__name__}
        row = {'query_id': case['id'], 'question': case['question'], 'result': result,
               'retrieval_trace': pipeline.last_trace,
               'evidence_audit': evidence_audit(case, result, {c['id']: c for c in chunks})}
        output.append(row)
        save(case['id']+'.json', row)
        print(json.dumps({'id': case['id'], 'status': result['status'],
                          'gold_in_context': row['evidence_audit']['gold_in_context'],
                          'attempts': len(result.get('attempts', []))}), flush=True)
    save('all_traces.json', output)
    manifest.update(status='finished', completed_at_utc=datetime.now(timezone.utc).isoformat(),
                    embedding_usage=backend.usage, trace_sha256=digest(a.output/'all_traces.json'),
                    chat_usage={k: sum(r['result'].get('usage', {}).get(k, 0) for r in output)
                                for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')})
    save('manifest.json', manifest)


if __name__ == '__main__':
    main()
