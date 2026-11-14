"""Grounded generation with structured output, validation and auditable repair.

Retrieval is fixed by the caller for controlled comparisons. Structural checks
do not establish semantic support; output errors are distinct from abstention.
"""
from __future__ import annotations

import hashlib
import copy
import json
import os
import re
import time
from pathlib import Path
from typing import Callable

import httpx

from .citation import extract_citation_ids, validate_citations
from .context import build_context
from .pipeline import field_coverage, requested_fields

PROMPT_PATH = Path(__file__).resolve().parents[1] / 'prompts/grounded_answer_v2.txt'
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding='utf-8')
ABSTENTION = 'Không đủ bằng chứng trong bộ dữ liệu hiện có để kết luận.'
ANSWER_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'answer': {'type': 'string'},
        'citations': {'type': 'array', 'items': {'type': 'string'}},
        'abstained': {'type': 'boolean'},
        'reason': {'type': 'string'},
        'evidence_quotes': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False,
            'properties': {'id': {'type': 'string'}, 'quote': {'type': 'string'}},
            'required': ['id', 'quote']}},
    },
    'required': ['answer', 'citations', 'abstained', 'reason', 'evidence_quotes'],
}


def evidence_blocks(context: str) -> dict[str, str]:
    headers = list(re.finditer(r'^\[([^\[\]\n]+)\][^\n]*\n', context, re.MULTILINE))
    return {m.group(1): context[m.end():headers[i+1].start() if i+1<len(headers) else len(context)]
            for i, m in enumerate(headers)}


def normalize_answer(payload: dict, context_ids: list[str], context: str) -> tuple[dict, list[str]]:
    """Render model-selected citations and expand uniquely matching excerpts.

    Abbreviated quotes are expanded only by exact, ordered fragment matches in
    the selected source block. Never invent an ID, fact or missing fragment.
    """
    if not isinstance(payload, dict): return payload, []
    output, changes = copy.deepcopy(payload), []
    blocks = evidence_blocks(context)
    citations = output.get('citations')
    if not isinstance(citations, list) or any(not isinstance(c, str) for c in citations): return output, changes
    for q in output.get('evidence_quotes', []) if isinstance(output.get('evidence_quotes'), list) else []:
        if not isinstance(q, dict) or not isinstance(q.get('quote'), str): continue
        text = ' '.join(blocks.get(q.get('id'), '').split())
        quote = ' '.join(q['quote'].split())
        if quote and quote not in text:
            case_matches=list(re.finditer(re.escape(quote),text,re.IGNORECASE))
            if len(case_matches)==1:
                q['quote']=case_matches[0].group();quote=q['quote']
                changes.append('restored_exact_source_capitalization')
        if quote and quote not in text and re.search(r'\.{3}|…', quote):
            fragments = [f.strip() for f in re.split(r'\.{3}|…', quote.rstrip(' .;')) if f.strip()]
            if len(fragments) < 2: continue
            pattern = '.*?'.join(re.escape(f) for f in fragments)
            matches = list(re.finditer(pattern, text))
            if len(matches) == 1:
                q['quote'] = matches[0].group()
                changes.append('expanded_abbreviated_quote_from_exact_source_fragments')
    quotes = output.get('evidence_quotes')
    valid_quotes = (isinstance(quotes, list) and quotes and all(isinstance(q, dict) and isinstance(q.get('quote'), str)
                    and q['quote'].strip() and q.get('id') in citations
                    and ' '.join(q['quote'].split()) in ' '.join(blocks.get(q.get('id'), '').split()) for q in quotes))
    if (output.get('abstained') is False and isinstance(output.get('answer'), str) and valid_quotes
            and citations and set(citations) <= set(context_ids)
            and set(extract_citation_ids(output['answer'])) <= set(citations)):
        missing = [cid for cid in citations if f'[{cid}]' not in output['answer']]
        if missing:
            output['answer'] = output['answer'].rstrip() + ' ' + ' '.join(f'[{cid}]' for cid in missing)
            changes.append('rendered_model_selected_citation_markers')
    return output, changes


def validate_answer(payload: dict, context_ids: list[str], context: str, question: str = '') -> tuple[list[str], dict]:
    """Validate schema, substantive text, every marker and exact source quotes."""
    errors = []
    if not isinstance(payload, dict):
        return ['payload must be an object'], {}
    answer, citations = payload.get('answer'), payload.get('citations')
    abstained, quotes = payload.get('abstained'), payload.get('evidence_quotes')
    if not isinstance(answer, str) or not answer.strip(): errors.append('answer must be nonempty')
    if not isinstance(citations, list) or any(not isinstance(c, str) for c in citations):
        errors.append('citations must be strings')
    if type(abstained) is not bool: errors.append('abstained must be boolean')
    if not isinstance(quotes, list) or any(not isinstance(q, dict) for q in quotes):
        errors.append('evidence_quotes must be objects')
    if errors: return errors, {}
    check = validate_citations(answer, citations, context_ids, context)
    if abstained:
        if citations or quotes or extract_citation_ids(answer):
            errors.append('abstention cannot assert citations')
        return errors, check
    if not check['all_structurally_valid']: errors.append('citations must occur in answer and context')
    if set(extract_citation_ids(answer)) != set(citations):
        errors.append('answer markers and citations must match')
    if not re.search(r'[^\W\d_]', re.sub(r'\[[^\]]+\]', '', answer), re.UNICODE):
        errors.append('answer contains no substantive text')
    blocks = evidence_blocks(context)
    covered = set()
    for q in quotes:
        cid, quote = q.get('id'), q.get('quote')
        if not isinstance(cid, str) or not isinstance(quote, str) or not quote.strip():
            errors.append('each quote needs id and nonempty text'); continue
        if cid not in citations or ' '.join(quote.split()) not in ' '.join(blocks.get(cid, '').split()):
            errors.append('quote does not occur in its cited evidence block')
        else: covered.add(cid)
    if covered != set(citations): errors.append('each citation needs a verified excerpt')
    fields = requested_fields(question)
    cited_text = '\n'.join(blocks.get(cid, '') for cid in citations)
    if fields and field_coverage(cited_text, fields) < len(fields):
        errors.append('cited evidence lacks the requested duration/renewal fields; abstain if unavailable')
    return errors, check


class OpenRouterAgent:
    """Provider-compatible name retained for existing scripts."""

    def __init__(self, search: Callable, *, model: str = 'openai/gpt-4o-mini', max_rounds: int = 2,
                 top_k: int = 3, context_budget: int = 6000, timeout: float = 60,
                 provider: str = 'openrouter', max_repairs: int = 1, context_expander: Callable | None = None):
        if provider not in {'openai', 'openrouter'} or max_rounds < 1 or max_repairs not in {0, 1}:
            raise ValueError('Invalid provider or call bounds')
        self.search, self.model, self.provider = search, model, provider
        self.context_expander = context_expander
        self.max_rounds, self.top_k, self.context_budget = max_rounds, top_k, context_budget
        self.timeout, self.max_repairs = timeout, max_repairs
        self.base_url = 'https://api.openai.com/v1' if provider == 'openai' else 'https://openrouter.ai/api/v1'
        env_name = 'OPENAI_API_KEY' if provider == 'openai' else 'OPENROUTER_API_KEY'
        self.key = os.getenv(env_name)
        if not self.key: raise RuntimeError(env_name + ' is missing')

    def _chat(self, question: str, context: str, feedback: str = '') -> dict:
        schema_format = {'type': 'json_schema', 'json_schema': {
            'name': 'grounded_answer', 'strict': True, 'schema': ANSWER_SCHEMA}}
        body = {'model': self.model, 'temperature': 0, 'max_completion_tokens': 1000,
                'messages': [{'role': 'system', 'content': SYSTEM_PROMPT},
                             {'role': 'user', 'content': f'Câu hỏi: {question}\n<evidence>\n{context}\n</evidence>\n{feedback}'}],
                'response_format': schema_format}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.base_url + '/chat/completions', json=body,
                                   headers={'Authorization': 'Bearer ' + self.key})
            if response.is_error:
                raise RuntimeError(f'{self.provider} chat API HTTP {response.status_code}')
            return response.json()

    def run(self, question: str, *, mode: str = 'hybrid_rrf') -> dict:
        if not isinstance(question, str) or not question.strip(): raise ValueError('Empty question')
        started = time.perf_counter()
        results = self.search(question, mode=mode, top_k=self.top_k)
        context_candidates = self.context_expander(results) if self.context_expander else results
        context, context_ids, dropped = build_context(context_candidates, budget_chars=self.context_budget)
        events = [{'event': 'search', 'round': 1, 'query': question, 'mode': mode, 'results': results,
                   'context_ids': context_ids, 'dropped_ids': dropped,
                   'expanded_ids': [c['id'] for c in context_candidates if c['id'] not in {r['id'] for r in results}]}]
        attempts, payload, check, errors = [], {}, {}, []
        feedback = ''
        if context_ids:
            for attempt in range(self.max_repairs + 1):
                response = self._chat(question, context, feedback)
                message = response['choices'][0]['message']
                raw = message.get('content') or ''
                normalizations = []
                try:
                    payload = json.loads(raw)
                    payload, normalizations = normalize_answer(payload, context_ids, context)
                    errors, check = validate_answer(payload, context_ids, context, question)
                except json.JSONDecodeError:
                    payload, errors, check = {}, ['invalid JSON'], {}
                if not isinstance(payload, dict): payload = {}
                attempts.append({'attempt': attempt + 1, 'response_id': response.get('id'),
                                 'model': response.get('model'), 'raw_content': raw,
                                 'finish_reason': response['choices'][0].get('finish_reason'),
                                 'refusal': message.get('refusal'), 'validation_errors': errors,
                                 'format_normalizations': normalizations,
                                 'usage': response.get('usage', {})})
                if not errors: break
                feedback = ('Câu trả lời trước không đạt kiểm tra định dạng: ' + '; '.join(errors)
                            + '. Hãy tạo lại JSON từ evidence. Mỗi evidence_quotes.quote phải là một đoạn '
                              'LIỀN MẠCH được chép nguyên văn; không dùng ... hay … hoặc ghép câu. '
                              'Có thể dùng nhiều quote ngắn cùng ID. Không thêm claim hoặc ID ngoài context.')
        else:
            payload = {'answer': ABSTENTION, 'citations': [], 'abstained': True, 'reason': 'empty_context'}
        status = 'error' if errors else 'abstain' if payload.get('abstained') else 'answered'
        if status == 'abstain':
            # Keep the complete raw refusal in attempts; present a scoped, minimal refusal.
            payload['answer'] = ABSTENTION
        events.append({'event': 'answer', 'citation_check': check, 'validation_errors': errors})
        usage = {key: sum(a['usage'].get(key, 0) for a in attempts)
                 for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
        return {'status': status, 'answer': payload.get('answer', ''),
                'citations': payload.get('citations', []), 'abstained': payload.get('abstained', False),
                'reason': 'output_validation_failed' if errors else payload.get('reason'),
                'evidence_quotes': payload.get('evidence_quotes', []), 'attempts': attempts,
                'context': context, 'context_ids': context_ids, 'events': events,
                'model': self.model, 'provider': self.provider, 'mode': mode, 'usage': usage,
                'prompt_version': 'grounded_answer_v2',
                'prompt_sha256': hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                'semantic_support': 'pending_human_review',
                'elapsed_ms': (time.perf_counter() - started) * 1000}
