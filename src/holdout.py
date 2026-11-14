"""Validate approved holdout versions and reserve one independent execution."""
import hashlib
import json
from datetime import datetime, timezone

from .evaluation import read_cases, read_json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_holdout(root, args, settings):
    approval = read_json(root/'benchmarks/fresh_holdout_manifest.json')
    if not approval.get('approved') or not approval.get('reviewer') or not approval.get('approved_at'):
        raise ValueError('Fresh benchmark requires H1/H2 human approval')
    if approval.get('executed') or (root/'benchmarks/fresh_holdout_execution.json').exists():
        raise ValueError('Holdout already started; preserve its results. Use diagnostic mode only for an exposed replay.')
    config_path = root/'configs/final_tool_agent.json'
    if sha(args.questions)!=approval['benchmark_sha256'] or sha(config_path)!=approval['config_sha256']:
        raise ValueError('Approved benchmark/config fingerprint mismatch')
    if sha(settings.corpus)!=approval['corpus_sha256']:
        raise ValueError('Corpus changed after H1/H2 approval')
    cases = read_cases(args.questions)
    if any(c.get('gold_status')!='human_verified' or not c.get('reviewer') or not c.get('review_timestamp') for c in cases):
        raise ValueError('Every fresh gold/scope label requires human verification')
    if len({c['id'] for c in cases})!=len(cases) or any(c['split']!='test' for c in cases):
        raise ValueError('Fresh benchmark must have unique test-only cases')
    if (sum(c['answerability']=='answerable' for c in cases)<5
            or sum(c['answerability']=='insufficient_evidence' for c in cases)<2):
        raise ValueError('Fresh test requires at least 5 answerable and 2 insufficient cases')
    config = read_json(config_path)
    fixed = {'candidate_k':10,'rrf_k':60,'final_top_k':3,'context_budget_chars':6000,
             'context_expansion_max':6,'max_retrieval_rounds':1,'max_tool_calls':4,'max_repairs':1,
             'max_completion_tokens':1000,'max_query_tokens':32000,'temperature':0,'seed':None}
    if any(config.get(key)!=value for key,value in fixed.items()):
        raise ValueError('Frozen parameters differ from implemented controlled pipeline')
    if (settings.model!=config['model'] or len(args.modes)!=len(set(args.modes))
            or set(args.modes)!=set(config['test_modes'])):
        raise ValueError('Test model/modes differ from frozen selection')
    if settings.max_cost_usd!=config['max_query_estimated_usd'] or args.max_run_cost_usd!=config['max_eval_run_estimated_usd']:
        raise ValueError('Test budgets differ from frozen selection')
    for runtime, expected in config['runtime_sha256'].items():
        if sha(root/runtime)!=expected: raise ValueError('Runtime changed after freeze: '+runtime)
    index = config.get('index_manifest')
    if not index or sha(root/index['path'])!=index['sha256']:
        raise ValueError('Frozen index manifest is unavailable or changed')
    return approval, config


def validate_diagnostic(root, questions):
    approval = read_json(root/'benchmarks/fresh_holdout_manifest.json')
    if sha(questions)==approval['benchmark_sha256'] and not approval.get('executed'):
        raise ValueError('Cannot diagnose an unopened fresh holdout; complete H1/H2 first')


def validate_index(pipeline, config):
    collection = pipeline.dense_search.collection
    metadata = collection.metadata
    if (metadata.get('model')!=config['embedding_model'] or metadata.get('dimensions')!=config['dimensions']
            or collection.name!=config['index_collection'] or str(collection.id)!=config['index_collection_id']
            or collection.count()!=len(pipeline.chunks)):
        raise ValueError('Live index differs from frozen embedding/collection/count')
    if collection.configuration.get('hnsw',{}).get('space')!=config['metric']:
        raise ValueError('Live index metric differs from frozen selection')
    if collection.configuration.get('hnsw')!=config['index_hnsw_configuration']:
        raise ValueError('Live HNSW configuration changed after freeze')


def reserve_holdout(root, args, settings, output):
    approval, _ = validate_holdout(root,args,settings)
    record = {'started_at_utc':datetime.now(timezone.utc).isoformat(),
              'run_directory':output.relative_to(root).as_posix(),
              'benchmark_sha256':approval['benchmark_sha256'],'config_sha256':approval['config_sha256']}
    # Exclusive creation also prevents two CLI processes reserving the same holdout.
    with (root/'benchmarks/fresh_holdout_execution.json').open('x',encoding='utf8') as stream:
        json.dump(record,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    approval.update(executed=True,execution_status='running',run_directory=record['run_directory'],
                    execution_started_at=record['started_at_utc'])
    (root/'benchmarks/fresh_holdout_manifest.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def finish_holdout(root, status):
    path = root/'benchmarks/fresh_holdout_manifest.json'
    approval = read_json(path)
    approval.update(execution_status=status,execution_finished_at=datetime.now(timezone.utc).isoformat())
    path.write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
