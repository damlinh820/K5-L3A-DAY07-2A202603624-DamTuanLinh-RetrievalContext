"""Localhost-only FastAPI demo with real retrieval, tools and artifact metrics."""
import json
import threading
import time
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .evaluation import load_dashboard
from .settings import ROOT, Settings
from .tool_agent import MODES, ToolAgent


def with_context_chunks(result, corpus=None):
    """Expose whole final context chunks, including expansion, without a search call."""
    ids = result.get('context_ids',[])
    chunks = {c['id']:c for event in result.get('events',[]) for c in event.get('results',[])}
    if set(ids)-set(chunks) and corpus and corpus.is_file():
        from .pipeline import normalize_chunk
        for line in corpus.read_text(encoding='utf8').splitlines():
            if line.strip():
                chunk = normalize_chunk(json.loads(line))
                if chunk['id'] in ids and chunk['id'] not in chunks: chunks[chunk['id']] = chunk
    return {**result,'context_chunks':[chunks[cid] for cid in ids if cid in chunks]}


class Query(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    question: str = Field(min_length=1,max_length=2000)
    mode: str = 'hybrid_improved'
    autonomous: bool = False

    @field_validator('question')
    @classmethod
    def nonempty(cls,v):
        if not v.strip(): raise ValueError('Câu hỏi không được rỗng')
        return v.strip()

    @field_validator('mode')
    @classmethod
    def mode_allowed(cls,v):
        if v not in MODES: raise ValueError('Mode không hợp lệ')
        return v


def create_app(*, root=ROOT, pipeline_factory=None, agent_factory=None):
    app=FastAPI(title='Day 7 Agentic RAG',docs_url=None,redoc_url=None)
    lock=threading.Lock()
    state={'pipeline':None,'last_query_at':0}

    @app.middleware('http')
    async def local_only(request: Request, call_next):
        host=request.url.hostname
        if host not in {'localhost','127.0.0.1','::1'}:
            return JSONResponse({'detail':'Localhost only'},403)
        origin=request.headers.get('origin')
        if origin and origin != f'{request.url.scheme}://{request.headers.get("host")}':
            return JSONResponse({'detail':'Cross-origin requests are not allowed'},403)
        length=request.headers.get('content-length','0')
        if not length.isdigit() or int(length)>8192: return JSONResponse({'detail':'Request too large'},413)
        response=await call_next(request)
        response.headers.update({'X-Content-Type-Options':'nosniff','Cache-Control':'no-store',
                                 'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'"})
        return response

    def pipeline():
        if state['pipeline'] is None:
            state['pipeline']=pipeline_factory() if pipeline_factory else Settings.load().pipeline()
        return state['pipeline']

    @app.get('/')
    def index(): return FileResponse(root/'web/index.html')

    @app.get('/app.js')
    def js(): return FileResponse(root/'web/app.js',media_type='text/javascript')

    @app.get('/style.css')
    def css(): return FileResponse(root/'web/style.css',media_type='text/css')

    @app.get('/api/health')
    def health():
        settings=Settings.load()
        import os
        return {'status':'ok','corpus_available':settings.corpus.is_file(),'index_available':settings.chroma.is_dir(),
                'chat_configured':bool(os.getenv('OPENAI_API_KEY')),'embedding_configured':bool(os.getenv('OPENROUTER_API_KEY'))}

    @app.get('/api/dashboard')
    def dashboard(): return load_dashboard(root)

    @app.get('/api/example/{case_id}')
    def example(case_id: str):
        # Deliberately allowlisted paths; no path supplied by the browser is opened.
        choices={'q01':('agent_dev_fixed','q01'),'q23':('case_diagnostic_final','q23'),
                 'q17':('case_diagnostic_final','q17'),'q17_old':('agent_test_frozen','q17'),
                 'q16':('case_diagnostic_final','q16'),'q19':('case_diagnostic_final','q19')}
        if case_id not in choices: raise HTTPException(404,'Example not found')
        run,cid=choices[case_id]
        path=root/'runs'/run/(cid+'.json')
        if not path.exists(): raise HTTPException(404,'Artifact unavailable')
        trace=json.loads(path.read_text(encoding='utf8'))
        trace['result']=with_context_chunks(trace['result'],Settings.load().corpus)
        return {'run_id':run,'trace':trace}

    @app.post('/api/compare')
    def compare(query: Query):
        with lock:
            try:
                p=pipeline(); rows=[]
                for mode in ('dense','bm25','hybrid_rrf'):
                    started=time.perf_counter(); results=p.search(query.question,mode=mode,top_k=3)
                    rows.append({'mode':mode,'results':results,'elapsed_ms':(time.perf_counter()-started)*1000,
                                 'score_type':{'dense':'cosine similarity','bm25':'BM25 score','hybrid_rrf':'RRF score'}[mode]})
                return {'question':query.question,'comparison':rows}
            except Exception as exc:
                raise HTTPException(503,'Retrieval unavailable: '+type(exc).__name__) from None

    @app.post('/api/query')
    def answer(query: Query):
        if not lock.acquire(blocking=False): raise HTTPException(429,'Đang xử lý một câu hỏi khác, vui lòng chờ.')
        try:
            if time.monotonic()-state['last_query_at']<1: raise HTTPException(429,'Vui lòng đợi một giây giữa hai câu hỏi.')
            state['last_query_at']=time.monotonic()
            p=pipeline()
            agent=agent_factory(p) if agent_factory else ToolAgent(p,model=Settings.load().model,
                max_rounds=2 if query.autonomous else 1,max_cost_usd=Settings.load().max_cost_usd)
            result=agent.run(query.question,mode=query.mode,autonomous=query.autonomous)
            trace_id=result['tool_trace_id']
            destination=root/'runs/demo_queries'
            destination.mkdir(parents=True,exist_ok=True)
            (destination/(trace_id+'.json')).write_text(json.dumps({'question':query.question,'result':result},ensure_ascii=False,indent=2),encoding='utf8')
            return with_context_chunks(result,Settings.load().corpus)
        except HTTPException: raise
        except Exception as exc:
            raise HTTPException(503,'Agent unavailable: '+type(exc).__name__+'. Kiểm tra .env, corpus và Chroma theo runbook.') from None
        finally: lock.release()

    return app


app=create_app()
