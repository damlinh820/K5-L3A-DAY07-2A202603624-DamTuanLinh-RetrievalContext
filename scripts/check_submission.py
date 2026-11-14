"""Read-only checks for required artifacts, data fingerprints and accidental keys."""
import csv
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation import holdout_status, load_dashboard, read_cases, read_json
from scripts.export_artifacts import selected_files
REQUIRED=['README.md','requirements.txt','requirements.lock.txt','.env.example','src/tool_agent.py','src/api.py',
          'src/cli.py','docs/runbook.md','docs/requirement_matrix.md','docs/day6_inventory.md',
          'report/individual/2A202603624_DamTuanLinh.md','reports/metrics.json','configs/final_tool_agent.json',
          'benchmarks/fresh_holdout_candidates.jsonl','benchmarks/fresh_holdout_manifest.json',
          'prompts/grounded_answer_v2.txt','docs/USER_CONFIRMATIONS.md']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ready',action='store_true',help='Fail unless independent test, reviews and inventory are complete')
    args=parser.parse_args()
    missing=[p for p in REQUIRED if not (ROOT/p).is_file()]
    if missing:
        print(json.dumps({'missing':missing,'ready_to_submit':False},indent=2))
        sys.exit(1)
    secret_files=[]
    pattern=re.compile(r'\bsk-(?:or-v1-|proj-)?[A-Za-z0-9_-]{25,}')
    for parent in ['src','scripts','docs','reports','reviews','report','configs','benchmarks','web','data','runs']:
        for p in (ROOT/parent).rglob('*'):
            if p.is_file() and p.name!='query_vectors.jsonl' and p.suffix in {'.py','.js','.html','.md','.json','.jsonl','.csv','.yaml'}:
                if pattern.search(p.read_text(encoding='utf8')): secret_files.append(str(p.relative_to(ROOT)))
    manifest=json.loads((ROOT/'data/benchmark_day7/benchmark_manifest.json').read_text(encoding='utf8'))
    actual=hashlib.sha256((ROOT/'data/benchmark_day7/lab7_benchmark.jsonl').read_bytes()).hexdigest()
    rows=list(csv.DictReader((ROOT/'reviews/review_log.csv').open(encoding='utf8')))
    keys=[(r['run_id'],r['case_id']) for r in rows]
    inventory=read_json(ROOT/'reports/submission_artifacts.json') if (ROOT/'reports/submission_artifacts.json').exists() else {'files':[]}
    listed={item['path']:item for item in inventory['files']}
    expected={p.relative_to(ROOT).as_posix() for p in selected_files()}
    stale=[name for name,item in listed.items() if not (ROOT/name).is_file()
           or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=item['sha256']]
    approval=read_json(ROOT/'benchmarks/fresh_holdout_manifest.json')
    config=read_json(ROOT/'configs/final_tool_agent.json')
    version_mismatches=[]
    for name,expected_hash in [(approval['benchmark'],approval['benchmark_sha256']),
                               (approval['config'],approval['config_sha256']),*config['runtime_sha256'].items()]:
        if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected_hash:
            version_mismatches.append(name)
    if config.get('index_manifest'):
        item=config['index_manifest']
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()!=item['sha256']:
            version_mismatches.append(item['path'])
    else: version_mismatches.append('config.index_manifest_missing')
    dashboard=load_dashboard(ROOT)
    holdout=dashboard['holdout']
    if holdout['executed'] and holdout.get('run_directory'):
        run_manifest=read_json(ROOT/holdout['run_directory']/'manifest.json')
        for key in ['corpus_sha256','benchmark_sha256']:
            if run_manifest.get(key)!=approval.get(key): version_mismatches.append('run.'+key)
    pending=[]
    if not holdout['approved']: pending.append('H1/H2: benchmark and final configuration approval')
    if not holdout['executed']: pending.append('Independent Dense + selected-mode holdout execution')
    if holdout['status']!='complete': pending.append('H3: trace-bound case and per-citation reviews for both modes')
    if stale or expected-set(listed): pending.append('Refresh artifact inventory after the final edits')
    if version_mismatches: pending.append('Resolve configuration/benchmark/runtime fingerprint mismatches')
    if dashboard['artifact_issues']: pending.append('Resolve run/benchmark artifact issues')
    finalization_path=ROOT/'reports/finalization.json'
    finalization=read_json(finalization_path) if finalization_path.exists() else {}
    sealed=finalization.get('status')=='complete' and finalization.get('final_test_run')==holdout.get('run_directory')
    for field in ['report','metrics']:
        path=ROOT/finalization.get(field,'__missing__')
        sealed &= path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==finalization.get(field+'_sha256')
    if not sealed: pending.append('Update and seal the final report/metrics in reports/finalization.json')
    if approval.get('approved') and any(c.get('gold_status')!='human_verified' for c in read_cases(ROOT/approval['benchmark'])):
        pending.append('Approved manifest has unverified gold/scope records')
    report={'check_mode':'ready' if args.ready else 'structural','missing':missing,'possible_secret_files':secret_files,'original_benchmark_hash_valid':actual==manifest['output_sha256'],
            'review_run_case_ids_unique':len(keys)==len(set(keys)),
            'holdout':holdout,'inventory':{'listed':len(listed),'missing_from_inventory':sorted(expected-set(listed)),'stale':stale},
            'version_mismatches':version_mismatches,'artifact_issues':dashboard['artifact_issues'],
            'pending':pending,'ready_to_submit':not pending and not missing and not secret_files
              and actual==manifest['output_sha256'] and len(keys)==len(set(keys))}
    print(json.dumps(report,indent=2))
    if missing or secret_files or not report['original_benchmark_hash_valid'] or not report['review_run_case_ids_unique']: sys.exit(1)
    if args.ready and not report['ready_to_submit']: sys.exit(2)


if __name__=='__main__':main()
