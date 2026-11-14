"""Compatible one-command entry point for the local FastAPI demo."""
import argparse
import sys
import webbrowser
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args()
    url=f'http://127.0.0.1:{args.port}'
    print('Day 7 demo: '+url,flush=True)
    if args.open: webbrowser.open(url)
    import uvicorn
    uvicorn.run('src.api:app',host='127.0.0.1',port=args.port,log_level='warning')
