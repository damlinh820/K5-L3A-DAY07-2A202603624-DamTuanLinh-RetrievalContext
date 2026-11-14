"""Real bounded OpenAI function calling with fixed-mode evaluation support."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid

import httpx

from .agent import ABSTENTION, ANSWER_SCHEMA, SYSTEM_PROMPT, normalize_answer, validate_answer
from .context import build_context
from .retrieval import reciprocal_rank_fusion

MODES = ('dense', 'bm25', 'hybrid_rrf', 'hybrid_improved', 'hybrid_rerank')
PRICE_SOURCE = 'https://developers.openai.com/api/docs/models/gpt-4o-mini'


def outside_jurisdiction(question):
    # Only an explicit request about a foreign jurisdiction, not an overseas
    # Vietnamese person or foreign organisation governed by Vietnamese law.
    return bool(re.search(r'(?:tại|ở|của)\s+(?:một\s+)?(?:quốc gia khác|nước khác)\b',question,re.I))


class BudgetExceeded(RuntimeError): pass


class ToolAgent:
    def __init__(self, pipeline, *, model='gpt-4o-mini', max_rounds=1, max_calls=4,
                 budget_chars=6000, budget_tokens=32000, max_cost_usd=0.10,
                 request=None):
        if not 1 <= max_rounds <= 2 or not 1 <= max_calls <= 4: raise ValueError('Invalid tool bounds')
        self.pipeline, self.model = pipeline, model
        self.max_rounds, self.max_calls = max_rounds, max_calls
        self.budget_chars, self.budget_tokens, self.max_cost_usd = budget_chars, budget_tokens, max_cost_usd
        self.request = request

    def _request(self, body):
        if self.request: return self.request(body)
        key = os.getenv('OPENAI_API_KEY')
        if not key: raise RuntimeError('OPENAI_API_KEY missing')
        with httpx.Client(timeout=httpx.Timeout(60, connect=20)) as client:
            r = client.post('https://api.openai.com/v1/chat/completions', json=body,
                            headers={'Authorization': 'Bearer '+key})
            if r.is_error: raise RuntimeError(f'OpenAI HTTP {r.status_code}')
            return r.json()

    def run(self, question: str, *, mode='hybrid_improved', autonomous=False):
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000: raise ValueError('Invalid question length')
        if mode not in MODES: raise ValueError('Invalid mode')
        import tiktoken
        # This encoding ships through tiktoken's verified cache; never estimate tokens as characters.
        encoder = tiktoken.get_encoding('cl100k_base')
        started = time.perf_counter()
        trace_id = uuid.uuid4().hex
        events, responses, rankings, candidates = [], [], {}, []
        total_tokens, estimated_usd, request_count = 0, 0.0, 0
        context, context_ids, payload, errors = '', [], {}, []
        controlled = ('Trong lần so sánh này, gọi search đúng 1 lần, giữ nguyên câu hỏi gốc và mode được cấp.'
                      if not autonomous else 'Có thể tìm thêm tối đa hai lượt nếu evidence chưa đủ.')
        scope = ('Corpus chỉ chứa snapshot Luật Đất đai 31/2024/QH15 của Việt Nam, không có pháp luật '
                 'của quốc gia khác hoặc hồ sơ hành chính riêng. Không dùng quy định Việt Nam để trả lời '
                 'thủ tục tại quốc gia khác. Với yêu cầu ngoài phạm vi này phải abstain, kể cả khi '
                 'retrieval trả về các đoạn có từ khóa giống nhau. ')
        system_prompt=SYSTEM_PROMPT+'\n'+scope+'Phải gọi tool search để tìm evidence trước khi trả lời. '+controlled
        messages = [{'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}]
        tool = {'type': 'function', 'function': {'name': 'search', 'strict': True,
            'description': 'Tìm bằng chứng trong snapshot Day 6, không tra web.',
            'parameters': {'type': 'object', 'additionalProperties': False,
                           'properties': {'query': {'type': 'string'}, 'mode': {'type': 'string', 'enum': list(MODES) if autonomous else [mode]},
                                          'top_k': {'type': 'integer', 'enum': [3]}},
                           'required': ['query', 'mode', 'top_k']}}}
        if not autonomous:
            tool['function']['parameters']['properties']['query']['enum']=[question]

        def ask(tools, required=False, feedback=''):
            nonlocal total_tokens, estimated_usd, request_count
            body = {'model': self.model, 'temperature': 0, 'max_completion_tokens': 1000,
                    'messages': messages+([{'role': 'user', 'content': feedback}] if feedback else [])}
            if tools:
                body.update(tools=[tool], tool_choice='required' if required else 'auto', parallel_tool_calls=False)
            if not required:
                body['response_format'] = {'type': 'json_schema', 'json_schema': {
                    'name': 'grounded_answer', 'strict': True, 'schema': ANSWER_SCHEMA}}
            # Reserve a conservative price bound for gpt-4o-mini, excluding caching discounts.
            if self.model not in {'gpt-4o-mini', 'gpt-4o-mini-2024-07-18'}:
                raise BudgetExceeded('Configure pricing before using a different model')
            input_tokens = len(encoder.encode(json.dumps(body, ensure_ascii=False))) + 256
            reservation = (input_tokens*0.15 + 1000*0.60)/1_000_000
            if (request_count >= self.max_rounds+2 or total_tokens+input_tokens+1000 > self.budget_tokens
                    or estimated_usd+reservation > self.max_cost_usd):
                raise BudgetExceeded('Configured request/token/cost budget reached')
            request_count += 1
            response = self._request(body)
            usage = response.get('usage', {})
            used = usage.get('total_tokens', input_tokens+1000)
            total_tokens += used
            cost = (usage.get('prompt_tokens', input_tokens)*0.15+usage.get('completion_tokens', 1000)*0.60)/1_000_000
            estimated_usd += cost
            responses.append({'response_id': response.get('id'), 'model': response.get('model'),
                              'message': response['choices'][0]['message'], 'usage': usage,
                              'estimated_cost_usd': cost, 'finish_reason': response['choices'][0].get('finish_reason')})
            return response['choices'][0]['message']

        status, error = 'error', None
        try:
            message = ask(True, required=True)
            calls_used = 0
            for round_no in range(1, self.max_rounds+1):
                calls = message.get('tool_calls', [])
                if not calls: raise ValueError('Model did not call search')
                messages.append({'role': 'assistant', 'content': message.get('content'), 'tool_calls': calls})
                for call in calls:
                    calls_used += 1
                    if calls_used > self.max_calls or call['function']['name'] != 'search': raise ValueError('Tool call limit/name invalid')
                    args = json.loads(call['function']['arguments'])
                    if set(args) != {'query', 'mode', 'top_k'} or args['top_k'] != 3 or args['mode'] not in MODES:
                        raise ValueError('Invalid tool arguments')
                    if not isinstance(args['query'], str) or not 1 <= len(args['query'].strip()) <= 2000: raise ValueError('Invalid tool query')
                    if not autonomous and args['mode'] != mode: raise ValueError('Mode restriction violated')
                    if not autonomous and args['query'] != question: raise ValueError('Controlled query restriction violated')
                    executed_query = args['query'] if autonomous else question
                    before = time.perf_counter()
                    results = self.pipeline.search(executed_query, mode=args['mode'], top_k=3)
                    rankings[call['id']] = results
                    ranked = results if len(rankings)==1 else reciprocal_rank_fusion(rankings, top_k=3)
                    candidates = self.pipeline.expand_context(ranked) if args['mode']=='hybrid_improved' else ranked
                    context, context_ids, dropped = build_context(candidates, budget_chars=self.budget_chars)
                    events.append({'event': 'search', 'tool_call_id': call['id'], 'round': round_no,
                                   'arguments': args, 'executed_query': executed_query, 'mode': args['mode'],
                                   'results': results, 'context_ids': context_ids, 'dropped_ids': dropped,
                                   'retrieval_trace': self.pipeline.last_trace, 'elapsed_ms': (time.perf_counter()-before)*1000})
                    # Preserve protocol while only the most recent cumulative context consumes budget.
                    for msg in messages:
                        if msg.get('role') == 'tool': msg['content'] = '{"context_superseded":true}'
                    messages.append({'role': 'tool', 'tool_call_id': call['id'],
                                     'content': json.dumps({'context': context, 'context_ids': context_ids,
                                                            'scope': 'fixed Day 6 snapshot'}, ensure_ascii=False)})
                message = ask(autonomous and round_no<self.max_rounds)
                if not message.get('tool_calls'): break
            if message.get('tool_calls'): raise ValueError('Model exceeded retrieval rounds')
            for repair in range(2):
                try:
                    raw = json.loads(message.get('content') or '')
                    payload, changes = normalize_answer(raw, context_ids, context)
                    errors, citation_check = validate_answer(payload, context_ids, context, question)
                    if not isinstance(payload,dict): payload={}
                except json.JSONDecodeError:
                    payload, changes, errors, citation_check = {}, [], ['Invalid JSON'], {}
                events.append({'event': 'answer_validation', 'errors': errors, 'normalizations': changes,
                               'citation_check': citation_check})
                if not errors: break
                if repair==0:
                    message = ask(False, feedback='Sửa JSON/citation từ chính evidence: '+'; '.join(errors)+'. Giữ trích đoạn đúng nguyên văn.')
            status = 'error' if errors else 'abstain' if payload.get('abstained') else 'answered'
            if status=='abstain': payload['answer']=ABSTENTION
            if errors: error='output_validation_failed'
        except Exception as exc:
            safe_http = re.fullmatch(r'(?:OpenAI|Embedding API) HTTP \d{3}',str(exc))
            error = str(exc) if isinstance(exc, BudgetExceeded) or safe_http else type(exc).__name__
            events.append({'event': 'error', 'error_type': type(exc).__name__})
        if status!='error' and any(e.get('event')=='search' for e in events) and outside_jurisdiction(question):
            status='abstain';error=None
            payload={'answer':ABSTENTION,'citations':[],'abstained':True,'evidence_quotes':[],
                     'reason':'requested_jurisdiction_outside_Vietnam_snapshot'}
            events.append({'event':'scope_guard','corpus_jurisdiction':'VN',
                           'reason':'explicit foreign-jurisdiction request'})
        return {'status': status, 'answer': payload.get('answer','') if status!='error' else '',
                'citations': payload.get('citations',[]) if status=='answered' else [],
                'abstained': status=='abstain', 'reason': error or payload.get('reason'),
                'evidence_quotes': payload.get('evidence_quotes',[]), 'context': context, 'context_ids': context_ids,
                'context_chars': len(context), 'context_tokens': len(encoder.encode(context)),
                'events': events, 'responses': responses, 'model': self.model, 'provider': 'openai',
                'mode': mode, 'autonomous': autonomous, 'tool_trace_id': trace_id,
                'prompt_version': 'grounded_answer_v2+tool_router_v2',
                'prompt_sha256': hashlib.sha256(system_prompt.encode()).hexdigest(),
                'usage': {k: sum(r['usage'].get(k,0) for r in responses) for k in ('prompt_tokens','completion_tokens','total_tokens')},
                'estimated_chat_cost_usd': estimated_usd, 'actual_chat_cost_usd': None,
                'price_source': PRICE_SOURCE, 'price_checked_on': '2026-11-14',
                'semantic_support': 'pending_human_review', 'elapsed_ms': (time.perf_counter()-started)*1000}
