"""Command-line entry point: python -m src.cli --help."""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .evaluation import agent_metrics, load_dashboard, supports_gold
from .settings import ROOT, Settings
from .tool_agent import MODES, ToolAgent
from .holdout import finish_holdout, reserve_holdout, validate_diagnostic, validate_holdout, validate_index
from .reviews import finalize_reviews, prepare_reviews


def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def cases_at(path): return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]


def audit(settings):
    if not settings.corpus.is_file(): raise ValueError('Day 6 corpus unavailable')
    from .pipeline import normalize_chunk
    rows=cases_at(settings.corpus)
    ids=[c['chunk_id'] for c in rows]
    if not rows or len(ids)!=len(set(ids)): raise ValueError('Duplicate/empty corpus')
    if any(not c.get('text','').strip() or c['page']>c['page_end'] or not c.get('source') for c in rows):
        raise ValueError('Invalid text/page/source')
    return {'corpus':str(settings.corpus),'rows':len(rows),'sha256':sha(settings.corpus),
            'embedding_model':'openai/text-embedding-3-small','dimensions':1536,
            'source_ids':sorted({c['document_id'] for c in rows}),'index_available':settings.chroma.is_dir()}


def validate_benchmark(path,settings):
    from .pipeline import normalize_chunk
    chunks=[normalize_chunk(c) for c in cases_at(settings.corpus)]
    cases=cases_at(path)
    if len({c['id'] for c in cases})!=len(cases): raise ValueError('Duplicate case IDs')
    counts={s:{a:sum(c['split']==s and c['answerability']==a for c in cases)
               for a in ('answerable','insufficient_evidence')} for s in ('dev','test')}
    missing=[c['id'] for c in cases if c['answerability']=='answerable' and not any(supports_gold(x,c['gold']) for x in chunks)]
    if missing: raise ValueError('Evidence missing: '+','.join(missing))
    return {'cases':len(cases),'counts':counts,'gold_resolves':True,'sha256':sha(path),
            'human_verified_cases':sum(c.get('gold_status')=='human_verified' for c in cases)}


def run_eval(args,settings):
    if not math.isfinite(args.max_run_cost_usd) or args.max_run_cost_usd<=0: raise ValueError('Run budget must be finite and positive')
    cases=[c for c in cases_at(args.questions) if c['split']==args.split]
    if not cases: raise ValueError('Empty split')
    fresh = args.split=='test' and not args.diagnostic
    if args.split=='test' and args.diagnostic: validate_diagnostic(ROOT,args.questions)
    if fresh: _, frozen_config = validate_holdout(ROOT,args,settings)
    output=args.output.resolve()
    if not output.is_relative_to((ROOT/'runs').resolve()): raise ValueError('Evaluation output must be inside runs/')
    if output.exists(): raise ValueError('Output exists; preserve it and choose a new directory')
    pipeline=settings.pipeline()
    if fresh: validate_index(pipeline,frozen_config)
    output.mkdir(parents=True,exist_ok=False)
    if fresh: reserve_holdout(ROOT,args,settings,output)
    (output/'benchmark.jsonl').write_bytes(args.questions.read_bytes())
    config={'modes':args.modes,'split':args.split,'model':settings.model,'top_k':3,'candidate_k':10,
            'rrf_k':60,'max_rounds':1,'context_budget_chars':6000,'max_run_estimated_usd':args.max_run_cost_usd}
    manifest={'started_at_utc':datetime.now(timezone.utc).isoformat(),'evaluation_type':
              'dev' if args.split=='dev' else 'exposed_test_diagnostic' if args.diagnostic else 'fresh_holdout',
              'config':config,'corpus_sha256':sha(settings.corpus),'benchmark_sha256':sha(args.questions),
              'code_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').glob('*.py'))},
              'prompt_sha256':sha(ROOT/'prompts/grounded_answer_v2.txt'),'semantic_review_status':'pending_human_review',
              'benchmark_file':'benchmark.jsonl','status':'running'}
    write_json(output/'manifest.json',manifest)
    spent=0.;all_modes={}
    try:
      for mode in args.modes:
        rows=[];destination=output/mode;destination.mkdir()
        for case in cases:
            remaining=args.max_run_cost_usd-spent
            if remaining<=0: raise ValueError('Run cost budget reached; inspect partial artifacts')
            agent=ToolAgent(pipeline,model=settings.model,max_cost_usd=min(settings.max_cost_usd,remaining))
            result=agent.run(case['question'],mode=mode)
            spent+=result['estimated_chat_cost_usd']
            row={'query_id':case['id'],'question':case['question'],'split':args.split,
                 'answerability':case['answerability'],'result':result}
            rows.append(row)
            write_json(destination/(case['id']+'.json'),row)
            write_json(destination/'all_traces.json',rows)
            print(f'{mode}: {case["id"]} {result["status"]}',flush=True)
        write_json(destination/'all_traces.json',rows)
        summary=agent_metrics(rows,cases,[],f'{output.name}/{mode}')
        # Retrieval/context matching is mechanical and separately labelled.
        answerable=[r for r in rows if r['answerability']=='answerable']
        c_lookup={c['id']:c for c in cases}
        hits1=hits3=context_hits=0
        for row in answerable:
            gold=c_lookup[row['query_id']]['gold'];res=row['result']
            search=next((e for e in res['events'] if e.get('event')=='search'),{})
            rankings=search.get('results',[])
            hits1+=bool(rankings and supports_gold(rankings[0],gold))
            hits3+=any(supports_gold(c,gold) for c in rankings[:3])
            context_hits+=any(supports_gold(c,gold) and c['id'] in res['context_ids'] for c in pipeline.chunks)
        summary['retrieval']={'hit1':hits1,'hit3':hits3,'n':len(answerable),
                              'context_exact_evidence':context_hits,'label':'mechanical provenance-aware; semantic review separate'}
        summary['estimated_chat_cost_usd']=sum(r['result']['estimated_chat_cost_usd'] for r in rows)
        write_json(destination/'metrics.json',summary)
        all_modes[mode]=summary
    except BaseException:
        manifest.update(status='failed',completed_at_utc=datetime.now(timezone.utc).isoformat(),estimated_chat_cost_usd=spent)
        write_json(output/'manifest.json',manifest)
        if fresh: finish_holdout(ROOT,'failed')
        raise
    manifest.update(completed_at_utc=datetime.now(timezone.utc).isoformat(),status='finished',estimated_chat_cost_usd=spent,
                    embedding_usage=pipeline.dense_search.usage)
    write_json(output/'manifest.json',manifest)
    write_json(output/'metrics.json',all_modes)
    if fresh: finish_holdout(ROOT,'finished')


def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('audit-day6')
    b=sub.add_parser('validate-benchmark');b.add_argument('--questions',type=Path,default=ROOT/'data/benchmark_day7/lab7_benchmark.jsonl')
    b=sub.add_parser('build-index');b.add_argument('--output',type=Path,default=ROOT/'runs/day6_rebuild');b.add_argument('--execute',action='store_true')
    b=sub.add_parser('serve');b.add_argument('--port',type=int,default=8765);b.add_argument('--open',action='store_true')
    b=sub.add_parser('ask');b.add_argument('question');b.add_argument('--mode',choices=MODES,default='hybrid_improved');b.add_argument('--autonomous',action='store_true')
    b=sub.add_parser('summarize');b.add_argument('--output',type=Path,default=ROOT/'reports/metrics.json')
    b=sub.add_parser('prepare-reviews');b.add_argument('--run',type=Path,required=True)
    b=sub.add_parser('finalize-reviews');b.add_argument('--run',type=Path,required=True);b.add_argument('--reviews',type=Path,required=True)
    b.add_argument('--partial',action='store_true',help='Publish a confirmed subset, e.g. historical corrections; does not complete H3')
    b=sub.add_parser('eval');b.add_argument('--split',choices=['dev','test'],required=True);b.add_argument('--questions',type=Path,default=ROOT/'data/benchmark_day7/lab7_benchmark.jsonl')
    b.add_argument('--modes',nargs='+',choices=MODES,default=['dense','bm25','hybrid_rrf','hybrid_improved']);b.add_argument('--output',type=Path,required=True)
    b.add_argument('--diagnostic',action='store_true');b.add_argument('--max-run-cost-usd',type=float,default=.20)
    args=parser.parse_args();settings=Settings.load()
    if args.command=='audit-day6': print(json.dumps(audit(settings),indent=2))
    elif args.command=='validate-benchmark': print(json.dumps(validate_benchmark(args.questions,settings),indent=2))
    elif args.command=='serve':
        if args.open:
            import webbrowser
            webbrowser.open(f'http://127.0.0.1:{args.port}')
        import uvicorn
        uvicorn.run('src.api:app',host='127.0.0.1',port=args.port,log_level='warning')
    elif args.command=='ask':
        result=ToolAgent(settings.pipeline(),model=settings.model,max_rounds=2 if args.autonomous else 1,
                         max_cost_usd=settings.max_cost_usd).run(args.question,mode=args.mode,autonomous=args.autonomous)
        destination=ROOT/'runs/cli_queries'/f'{result["tool_trace_id"]}.json'
        write_json(destination,{'question':args.question,'result':result})
        print(json.dumps(result,ensure_ascii=False,indent=2))
    elif args.command=='eval':run_eval(args,settings)
    elif args.command=='summarize':
        write_json(args.output,load_dashboard(ROOT));print(str(args.output))
    elif args.command=='prepare-reviews': print(json.dumps(prepare_reviews(ROOT,args.run.resolve()),ensure_ascii=False,indent=2))
    elif args.command=='finalize-reviews':
        print(json.dumps(finalize_reviews(ROOT,args.run.resolve(),args.reviews,partial=args.partial),ensure_ascii=False,indent=2))
        write_json(ROOT/'reports/metrics.json',load_dashboard(ROOT))
    elif args.command=='build-index':
        audit(settings)
        if not args.execute:
            print('Dry run: valid corpus. Use --execute to call embedding API in a NEW output directory.');return
        if args.output.exists(): raise ValueError('Output exists; choose a new directory to preserve indices')
        from .settings import DEFAULT_DAY6
        env=ROOT/'.env' if (ROOT/'.env').exists() else settings.day6/'.env'
        subprocess.run([sys.executable,str(ROOT/'scripts/rebuild_day6_dense.py'),'--chunks',str(settings.corpus),
                        '--env',str(env),'--output',str(args.output)],check=True)


if __name__=='__main__':main()
