"""LEGACY fixed-generation agent; new experiments use python -m src.cli eval."""
import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.agent import OpenRouterAgent
from src.pipeline import Day6DenseBackend, LegalPipeline, normalize_chunk


def main():
    parser = argparse.ArgumentParser()
    for flag in ('chunks', 'questions', 'env', 'chroma', 'output'):
        parser.add_argument('--'+flag, type=Path, required=True)
    parser.add_argument('--split', choices=['dev', 'test'], default='dev')
    parser.add_argument('--mode', choices=['dense', 'bm25', 'hybrid_rrf', 'hybrid_improved'], default='hybrid_rrf')
    args = parser.parse_args()
    load_dotenv(args.env)
    cases = [json.loads(x) for x in args.questions.read_text(encoding='utf8').splitlines() if x.strip()]
    selected = [c for c in cases if c['split'] == args.split]
    if not selected: raise ValueError('No cases in selected split')
    args.output.mkdir(parents=True, exist_ok=False)
    raw = [json.loads(x) for x in args.chunks.read_text(encoding='utf8').splitlines() if x.strip()]
    backend = Day6DenseBackend(args.chroma, args.chunks, args.output)
    pipeline = LegalPipeline([normalize_chunk(c) for c in raw], backend)
    rows = []
    for i, case in enumerate(selected, 1):
        try:
            agent = OpenRouterAgent(pipeline.search, model='gpt-4o-mini', provider='openai',
                                    context_expander=pipeline.expand_context if args.mode == 'hybrid_improved' else None)
            result = agent.run(case['question'], mode=args.mode)
        except Exception as exc:
            result = {'status': 'error', 'error_type': type(exc).__name__}
        row = {'query_id': case['id'], 'split': args.split, 'answerability': case.get('answerability'),
               'question': case['question'], 'result': result, 'retrieval_trace': pipeline.last_trace}
        rows.append(row)
        (args.output/(case['id']+'.json')).write_text(json.dumps(row, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        print(f'{i}/{len(selected)} {case["id"]} {result["status"]}', flush=True)
    (args.output/'all_traces.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    summary = {'split': args.split, 'mode': args.mode, 'cases': len(rows)}
    summary.update({status: sum(r['result']['status'] == status for r in rows)
                    for status in ('answered', 'abstain', 'error')})
    print(json.dumps(summary))


if __name__ == '__main__': main()
