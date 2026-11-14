"""Create a checksum inventory of safe submission artifacts (no binary indices/keys)."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXTENSIONS={'.py','.html','.css','.js','.md','.json','.jsonl','.csv','.txt','.yaml','.yml'}


def selected_files(root=ROOT):
    """Include evidence for every retained run, not a hand-maintained whitelist."""
    selected=set()
    for parent in ['src','scripts','tests','web','docs','report','reports','reviews','configs',
                   'benchmarks','prompts','data','starter','runs']:
        for path in (root/parent).rglob('*'):
            relative=path.relative_to(root)
            if (path.is_file() and path.suffix in EXTENSIONS and '__pycache__' not in path.parts
                    and 'chroma' not in relative.parts and path.name!='query_vectors.jsonl'
                    and relative.as_posix()!='reports/submission_artifacts.json'
                    and not relative.as_posix().startswith(('starter/data/','starter/results/'))):
                selected.add(path)
    selected.update(path for path in root.glob('*.md') if path.is_file())
    selected.update(root/name for name in ['requirements.txt','requirements.lock.txt','.env.example','.gitignore','.gitattributes']
                    if (root/name).is_file())
    return sorted(selected)


def main():
    items=[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in selected_files()]
    target=ROOT/'reports/submission_artifacts.json'
    target.write_text(json.dumps({'files':items,'includes_binary_index':False,'includes_api_keys':False,
                                 'requires_day6_snapshot':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'{len(items)} artifacts inventoried; Chroma and query vector caches excluded.')


if __name__=='__main__':main()
