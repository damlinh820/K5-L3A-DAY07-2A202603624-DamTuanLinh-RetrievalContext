"""Prepare review packets and finalize confirmed labels without inference calls."""
import json
from datetime import datetime
from pathlib import Path

from .evaluation import agent_metrics, load_reviews, read_json, run_artifacts, trace_hash


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def mode_directories(directory):
    if (directory/'all_traces.json').exists(): return [directory]
    return sorted(p.parent for p in directory.glob('*/all_traces.json'))


def prepare_reviews(root, directory):
    targets = []
    for mode in mode_directories(directory):
        rows, cases, run_id, _, _ = run_artifacts(root, mode)
        case_map = {c['id']:c for c in cases}
        destination = root/'reviews/pending'/(run_id.replace('/','__')+'.json')
        if destination.exists(): raise ValueError('Review packet exists; preserve edits: '+str(destination))
        packet = []
        for row in rows:
            case = case_map[row['query_id']]
            packet.append({'run_id':run_id,'case_id':row['query_id'],'trace_sha256':trace_hash(row),
                'status':'pending_human_review','reviewer':None,'reviewed_at':None,'source_verified':None,
                'evidence_sufficiency_0_2':None,'grounded_answer_0_2':None,'abstention_correct':None,'notes':'',
                'citation_reviews':[{'citation_index':i,'citation_id':cid,'supported':None,'reason':''}
                                    for i,cid in enumerate(row['result'].get('citations',[]))],
                'question':case['question'],'reference_answer':case.get('reference_answer',case.get('answer')),
                'gold':case.get('gold',[]),'absence_reason':case.get('absence_reason'),
                'trace_artifact':(mode/(row['query_id']+'.json')).relative_to(root).as_posix(),
                'answer':row['result'].get('answer'),'result_status':row['result']['status'],
                'context':row['result'].get('context','')})
        write_json(destination, packet)
        targets.append(destination.relative_to(root).as_posix())
    if not targets: raise ValueError('No saved agent traces found')
    return targets


def validate_reviews(rows, cases, labels, run_id):
    case_map = {c['id']:c for c in cases}
    keys = [label['case_id'] for label in labels]
    if len(keys)!=len(set(keys)) or set(keys)!={r['query_id'] for r in rows}:
        raise ValueError('Review must cover exactly every case in this mode')
    lookup = {label['case_id']:label for label in labels}
    for row in rows:
        label = lookup[row['query_id']]
        if (label.get('run_id')!=run_id or label.get('status')!='human_verified'
                or label.get('trace_sha256')!=trace_hash(row)):
            raise ValueError('Review is pending, belongs to another run, or trace changed: '+row['query_id'])
        if not str(label.get('reviewer') or '').strip() or not label.get('reviewed_at'):
            raise ValueError('Reviewer and review timestamp required')
        datetime.fromisoformat(label['reviewed_at'].replace('Z','+00:00'))
        if label.get('source_verified') is not True or not str(label.get('notes') or '').strip():
            raise ValueError('Source confirmation and review reason required')
        if case_map[row['query_id']]['answerability']=='answerable':
            for key in ['evidence_sufficiency_0_2','grounded_answer_0_2']:
                if type(label.get(key)) is not int or label[key] not in (0,1,2):
                    raise ValueError('Context and grounded grades must be 0, 1 or 2')
            if row['result']['status']!='answered' and label['grounded_answer_0_2']!=0:
                raise ValueError('An answerable abstention/error must have grounded grade 0')
        else:
            if type(label.get('abstention_correct')) is not bool:
                raise ValueError('Insufficient-evidence abstention needs a boolean review')
            if label['abstention_correct'] and row['result']['status']!='abstain':
                raise ValueError('An answer/error cannot be a correct abstention')
        expected = list(enumerate(row['result'].get('citations',[])))
        citations = label.get('citation_reviews',[])
        if [(c.get('citation_index'),c.get('citation_id')) for c in citations]!=expected:
            raise ValueError('Review every citation in the original order')
        if any(type(c.get('supported')) is not bool or not str(c.get('reason') or '').strip() for c in citations):
            raise ValueError('Every citation requires a support label and reason')
    return labels


def finalize_reviews(root, directory, review_file, *, partial=False):
    rows, cases, run_id, group, manifest = run_artifacts(root,directory)
    labels = read_json(review_file)
    selected = {label['case_id'] for label in labels}
    if not selected.issubset({row['query_id'] for row in rows}): raise ValueError('Review contains unknown cases')
    validate_reviews([row for row in rows if row['query_id'] in selected] if partial else rows,cases,labels,run_id)
    destination = root/'reviews/verified'/(run_id.replace('/','__')+'.json')
    previous_labels = read_json(destination) if partial and destination.exists() else []
    write_json(destination,[label for label in previous_labels if label['case_id'] not in selected]+labels)
    metric = agent_metrics(rows,cases,load_reviews(root),run_id)
    previous = read_json(directory/'metrics.json') if (directory/'metrics.json').exists() else {}
    if 'retrieval' in previous: metric['retrieval'] = previous['retrieval']
    write_json(directory/'metrics.json',metric)
    if group!=directory:
        combined = read_json(group/'metrics.json') if (group/'metrics.json').exists() else {}
        combined[directory.name] = metric
        write_json(group/'metrics.json',combined)
        states = [read_json(p/'metrics.json').get('semantic_review_status') for p in mode_directories(group)
                  if (p/'metrics.json').exists()]
        manifest['semantic_review_status'] = 'human_verified' if states and all(s=='human_verified' for s in states) else 'partial'
        write_json(group/'manifest.json',manifest)
    return {'run_id':run_id,'reviewed_cases':len(labels),'metrics':(directory/'metrics.json').relative_to(root).as_posix()}
