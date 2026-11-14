"""Metrics derived from stored results; human labels are joined by run + case."""
import csv
import hashlib
import json
import math
from pathlib import Path


def fraction(n, d):
    return {'n': n, 'N': d, 'rate': n/d if d else None}


def percentile(values, p):
    if not values: return None
    ordered = sorted(values)
    position = (len(ordered)-1)*p
    lower = math.floor(position)
    return ordered[lower]+(ordered[math.ceil(position)]-ordered[lower])*(position-lower)


def trace_hash(row):
    """Bind a semantic review to the exact saved output, independent of JSON spacing."""
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf8')).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf8'))


def read_cases(path):
    return [json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]


def load_reviews(root):
    path = root/'reviews/review_log.csv'
    labels = list(csv.DictReader(path.open(encoding='utf8', newline=''))) if path.exists() else []
    structured = {}
    for path in sorted((root/'reviews/verified').glob('*.json')):
        for label in read_json(path):
            key = (label['run_id'], label['case_id'])
            if key in structured: raise ValueError('Duplicate verified semantic review: '+str(key))
            structured[key] = label
    return [label for label in labels if (label['run_id'], label['case_id']) not in structured]+list(structured.values())


def supports_gold(chunk, gold):
    norm = lambda x: ' '.join(x.split())
    source = chunk.get('source_id', chunk.get('document_id'))
    pages = {p['page'] for p in chunk.get('provenance', [])} | {chunk.get('page')}
    return any(source==g['source_id'] and g['page'] in pages
               and norm(g.get('evidence_quote', g.get('evidence',''))) in norm(chunk['text']) for g in gold)


def agent_metrics(rows, cases, reviews, run_id):
    case_map = {c['id']:c for c in cases}
    labels = {r['case_id']:r for r in reviews if r['run_id']==run_id and r['status']=='human_verified'}
    stale = []
    for row in rows:
        label = labels.get(row['query_id'])
        if label and label.get('trace_sha256') and label['trace_sha256'] != trace_hash(row):
            stale.append(row['query_id'])
            del labels[row['query_id']]
    successful = [r for r in rows if r['result'].get('status') in {'answered','abstain'}]
    answerable = [r for r in rows if case_map[r['query_id']]['answerability']=='answerable']
    absent = [r for r in rows if case_map[r['query_id']]['answerability']=='insufficient_evidence']
    reviewed = [r for r in answerable if r['query_id'] in labels]
    grounds = [int(labels[r['query_id']]['grounded_answer_0_2']) for r in reviewed]
    # A row-level 0..2 legacy grade cannot identify support for each citation.
    full_supported = reviewed_citations = total_citations = 0
    for row in rows:
        res = row['result']
        per_citation = labels.get(row['query_id'], {}).get('citation_reviews', [])
        for index, cid in enumerate(res.get('citations', [])):
            total_citations += 1
            label = next((c for c in per_citation if c.get('citation_index') == index
                          and c.get('citation_id') == cid), None)
            if label is not None and isinstance(label.get('supported'), bool):
                reviewed_citations += 1
                full_supported += label['supported'] and cid in res.get('context_ids', [])
    citations = [(cid,r['result'].get('context_ids',[]),r['result'].get('answer',''))
                 for r in successful for cid in r['result'].get('citations',[])]
    latency = [r['result']['elapsed_ms'] for r in rows if 'elapsed_ms' in r['result']]
    tp = sum(r['result']['status']=='abstain' for r in absent)
    fp = sum(r['result']['status']=='abstain' for r in answerable)
    context_reviewed = [r for r in answerable if r['query_id'] in labels]
    context_grades = [int(labels[r['query_id']]['evidence_sufficiency_0_2']) for r in context_reviewed]
    answered = [r for r in rows if r['result'].get('status') == 'answered']
    absent_reviewed = [r for r in absent if r['query_id'] in labels
                       and str(labels[r['query_id']].get('abstention_correct')).lower() in {'true','false'}]
    citation_metric = fraction(full_supported, total_citations)
    citation_metric.update(reviewed=reviewed_citations, unreviewed=total_citations-reviewed_citations,
                           complete=reviewed_citations==total_citations)
    if reviewed_citations != total_citations: citation_metric['rate'] = None
    current_ids = {r['query_id'] for r in rows}
    verified = bool(rows) and current_ids.issubset(labels) and citation_metric['complete']
    return {'run_id':run_id, 'cases':len(rows), 'errors':sum(r['result']['status']=='error' for r in rows),
            'tool_use':fraction(sum(any(e.get('event')=='search' for e in r['result'].get('events',[])) for r in successful),len(successful)),
            'tool_call_distribution':{str(n):sum(sum(e.get('event')=='search' for e in r['result'].get('events',[]))==n for r in rows) for n in range(5)},
            'grounded':{'reviewed':len(grounds),'total':len(answerable),'counts':{str(g):grounds.count(g) for g in range(3)},
                        'mean_out_of_2':sum(grounds)/len(grounds) if grounds else None},
            'citation_id_validity':fraction(sum(cid in ids and f'[{cid}]' in answer for cid,ids,answer in citations),len(citations)),
            'citation_support':citation_metric,
            'answers_with_citations':fraction(sum(bool(r['result'].get('citations')) for r in answered),len(answered)),
            'abstention_recall':fraction(tp,len(absent)), 'abstention_precision':fraction(tp,tp+fp),
            'false_abstention':fraction(fp,len(answerable)),
            'abstention_confusion':{'true_abstention':tp,'false_abstention':fp,
                                   'false_answer_on_absent':sum(r['result']['status']=='answered' for r in absent)},
            'reviewed_context_evidence_rate':fraction(context_grades.count(2),len(context_reviewed)),
            'context_grades':{'reviewed':len(context_grades),'total':len(answerable),
                              'counts':{str(g):context_grades.count(g) for g in range(3)}},
            'human_abstention_correct':fraction(sum(str(labels[r['query_id']]['abstention_correct']).lower()=='true'
                                                       for r in absent_reviewed),len(absent_reviewed)),
            'stale_review_case_ids':stale,
            'latency_ms':{'p50':percentile(latency,.5),'p95':percentile(latency,.95)},
            'tokens':{k:sum(r['result'].get('usage',{}).get(k,0) for r in rows) for k in ('prompt_tokens','completion_tokens','total_tokens')},
            'estimated_chat_cost_usd':sum(r['result'].get('estimated_chat_cost_usd',0) for r in rows),
            'actual_chat_cost_usd':None,'semantic_review_status':'human_verified' if verified else 'partial' if labels else 'pending'}


def run_artifacts(root, directory):
    """Resolve the benchmark belonging to one agent mode, not a global case map."""
    directory = directory.resolve()
    run_id = directory.relative_to((root/'runs').resolve()).as_posix()
    rows = read_json(directory/'all_traces.json')
    group = directory if (directory/'manifest.json').is_file() else directory.parent
    manifest = read_json(group/'manifest.json') if (group/'manifest.json').is_file() else {}
    if manifest.get('benchmark_file'):
        benchmark = (group/manifest['benchmark_file']).resolve()
        if not benchmark.is_relative_to(group.resolve()): raise ValueError('Benchmark must stay inside run directory')
    else:
        benchmark = root/'data/benchmark_day7/lab7_benchmark.jsonl'
    if manifest.get('benchmark_sha256') and hashlib.sha256(benchmark.read_bytes()).hexdigest()!=manifest['benchmark_sha256']:
        raise ValueError('Run benchmark fingerprint mismatch: '+run_id)
    cases = read_cases(benchmark)
    if not {r['query_id'] for r in rows}.issubset({c['id'] for c in cases}):
        raise ValueError('Run case IDs do not belong to its benchmark: '+run_id)
    return rows, cases, run_id, group, manifest


def holdout_status(root):
    path = root/'benchmarks/fresh_holdout_manifest.json'
    approval = read_json(path) if path.exists() else {}
    status = 'pending_human_approval'
    if approval.get('approved'):
        status = 'approved_not_run'
        if approval.get('executed'):
            status = approval.get('execution_status', 'pending_human_review')
            run = root/approval.get('run_directory', 'runs/final_holdout_v1')
            if (run/'manifest.json').exists() and read_json(run/'manifest.json').get('status') == 'finished':
                status = 'pending_human_review'
                config = read_json(root/'configs/final_tool_agent.json')
                expected = {c['id'] for c in read_cases(root/approval['benchmark']) if c['split']=='test'}
                labels = load_reviews(root)
                complete = True
                for mode in config['test_modes']:
                    if not (run/mode/'all_traces.json').exists():
                        complete = False
                        continue
                    rows, cases, run_id, _, _ = run_artifacts(root, run/mode)
                    from .reviews import validate_reviews
                    selected = [l for l in labels if l['run_id']==run_id]
                    try: validate_reviews(rows,cases,selected,run_id)
                    except (ValueError, KeyError, TypeError):
                        complete = False
                        continue
                    metric = agent_metrics(rows, cases, labels, run_id)
                    complete &= (len(rows)==len(expected) and {r['query_id'] for r in rows}==expected
                                 and metric['semantic_review_status']=='human_verified'
                                 and all(any(l['run_id']==run_id and l['case_id']==r['query_id']
                                             and l.get('trace_sha256')==trace_hash(r) for l in labels) for r in rows))
                if complete: status = 'complete'
    return {'status':status,'approved':bool(approval.get('approved')),'executed':bool(approval.get('executed')),
            'run_directory':approval.get('run_directory'),'ready':status=='complete'}


def load_dashboard(root: Path):
    reviews = load_reviews(root)
    retrieval = []
    audit_path=root/'reports/recomputed_retrieval.json'
    audited=json.loads(audit_path.read_text(encoding='utf8')) if audit_path.exists() else {}
    for name in ['phase2_dev','phase3_dev_improvements','phase3_dev_all5','phase2_test_frozen','phase3_test_all5']:
        path=root/'runs'/name/'summary.json'
        if path.exists():
            data=json.loads(path.read_text(encoding='utf8'))
            original_metrics=data.get('metrics',{})
            if name in audited:
                data['metrics']={mode:{'hit1':v['hit1'],'hit3':v['hit3'],'hit1_rate':v['hit1']/v['n'],
                                       'hit3_rate':v['hit3']/v['n']} for mode,v in audited[name]['methods'].items()}
            retrieval.append({'run_id':name,'artifact':f'runs/{name}/summary.json','data':data,
                              'stored_original_metrics':original_metrics,'audit_artifact':'reports/recomputed_retrieval.json' if name in audited else None,
                              'evaluation_type':'dev' if 'test' not in name else 'original_test' if name=='phase2_test_frozen' else 'exposed_test_replay'})
    agents=[]
    paths = {root/'runs'/name/'all_traces.json' for name in ['agent_dev_fixed','agent_test_frozen','case_diagnostic_final']}
    paths.update(p for p in (root/'runs').rglob('all_traces.json') if (p.parent.parent/'manifest.json').exists())
    grouped = {}
    issues = []
    correction_path = root/'reviews/pending/context_corrections.json'
    corrections = read_json(correction_path) if correction_path.exists() else []
    for path in sorted(paths):
        if not path.exists(): continue
        try:
            rows, run_cases, name, group, manifest = run_artifacts(root,path.parent)
            metric = agent_metrics(rows,run_cases,reviews,name)
            metric['review_warnings'] = [c['case_id'] for c in corrections if c['run_id']==name
                and not any(l['run_id']==name and l['case_id']==c['case_id'] and l.get('trace_sha256')==c['trace_sha256']
                            and l.get('status')=='human_verified' for l in reviews)]
            saved = read_json(path.parent/'metrics.json') if (path.parent/'metrics.json').exists() else {}
            if 'retrieval' in saved:
                metric['retrieval'] = saved['retrieval']
                entry = grouped.setdefault(group.relative_to(root).as_posix(), {'run_id':group.name,
                    'artifact':(group/'metrics.json').relative_to(root).as_posix(),
                    'evaluation_type':manifest.get('evaluation_type','historical'), 'data':{'metrics':{}}})
                entry['data']['n'] = saved['retrieval']['n']
                entry['data']['metrics'][path.parent.name] = saved['retrieval']
            agents.append(metric)
        except (ValueError, KeyError, OSError) as exc:
            issues.append({'artifact':path.relative_to(root).as_posix(),'error':str(exc)})
    retrieval.extend(grouped.values())
    holdout = holdout_status(root)
    return {'retrieval':retrieval,'agents':agents,'scope':'Day 6 fixed snapshot',
            'fresh_holdout_status':holdout['status'],'holdout':holdout,'artifact_issues':issues,
            'example_ids':['q01','q23','q17']}
