"""Recompute stored retrieval rankings against page provenance; no API calls."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.settings import ROOT,Settings
from src.pipeline import normalize_chunk
from src.evaluation import supports_gold


def main():
    settings=Settings.load()
    chunks={c['id']:c for c in [normalize_chunk(json.loads(x)) for x in settings.corpus.read_text(encoding='utf8').splitlines()]}
    cases={c['id']:c for c in map(json.loads,(ROOT/'data/benchmark_day7/lab7_benchmark.jsonl').read_text(encoding='utf8').splitlines())}
    out={}
    for run in ['phase2_dev','phase3_dev_improvements','phase3_dev_all5','phase2_test_frozen','phase3_test_all5']:
        path=ROOT/'runs'/run/'traces.json'
        if not path.exists():continue
        traces=json.loads(path.read_text(encoding='utf8'));methods={}
        for t in traces:
            for mode,ranking in t['results'].items():
                ids=[c['id'] for c in ranking]
                if any(c['text']!=chunks[c['id']]['text'] for c in ranking):raise ValueError('Stored text differs from corpus')
                hits=[supports_gold(chunks[cid],cases[t['query_id']]['gold']) for cid in ids]
                m=methods.setdefault(mode,{'n':0,'hit1':0,'hit3':0,'per_case':[]})
                m['n']+=1;m['hit1']+=bool(hits and hits[0]);m['hit3']+=any(hits[:3])
                m['per_case'].append({'query_id':t['query_id'],'hit1':bool(hits and hits[0]),'hit3':any(hits[:3])})
        out[run]={'source_artifact':str(path.relative_to(ROOT)),'calculation':'source + normalized quote + original page provenance',
                  'methods':methods,'semantic_review':'not inferred from exact match'}
    target=ROOT/'reports/recomputed_retrieval.json'
    target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for name,r in out.items():
        print(name,{m:(v['hit1'],v['hit3'],v['n']) for m,v in r['methods'].items()})


if __name__=='__main__':main()
