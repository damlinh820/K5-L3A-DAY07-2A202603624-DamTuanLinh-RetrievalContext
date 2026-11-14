"""Synthetic checks for output repair, source quotes and incidental locators."""
import json
import os
import unittest
from unittest.mock import patch

from src.agent import OpenRouterAgent, normalize_answer, validate_answer
from src.pipeline import LegalPipeline, query_variants


def chunk(cid, text, article='12'):
    return {'id': cid, 'text': text, 'source_id': 'fixture', 'source': 'fixture.pdf', 'page': 1,
            'page_end': 1, 'body_start': 0, 'metadata': {'article': article, 'clause': '1', 'part': 1}}


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.row = chunk('e1', 'Thông tin minh họa chỉ dùng trong unit test.')
        self.context = '[e1] fixture.pdf | page 1\n'+self.row['text']
        self.payload = {'answer': 'Thông tin minh họa [e1].', 'citations': ['e1'],
                        'abstained': False, 'reason': 'evidence',
                        'evidence_quotes': [{'id': 'e1', 'quote': self.row['text']}]}

    def test_citation_only_and_unlisted_markers_rejected(self):
        self.assertTrue(validate_answer({**self.payload, 'answer': '[e1]'}, ['e1'], self.context)[0])
        self.assertTrue(validate_answer({**self.payload, 'answer': 'Thông tin [other].'}, ['e1'], self.context)[0])

    def test_quote_must_belong_to_its_citation(self):
        payload = {**self.payload, 'evidence_quotes': [{'id': 'e1', 'quote': 'nội dung khối khác'}]}
        self.assertTrue(validate_answer(payload, ['e1'], self.context+'\n[e2] fixture\nnội dung khối khác')[0])

    def test_format_error_is_repaired_once_and_raw_output_kept(self):
        def response(payload):
            return {'choices': [{'message': {'content': json.dumps(payload)}, 'finish_reason': 'stop'}],
                    'usage': {'total_tokens': 10}}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic'}):
            agent = OpenRouterAgent(lambda *a, **kw: [self.row], provider='openai')
            with patch.object(agent, '_chat', side_effect=[response({**self.payload, 'answer': '[e1]'}), response(self.payload)]):
                result = agent.run('Câu hỏi minh họa')
        self.assertEqual(result['status'], 'answered')
        self.assertEqual(len(result['attempts']), 2)
        self.assertTrue(result['attempts'][0]['validation_errors'])
        self.assertEqual(result['usage']['total_tokens'], 20)

    def test_invalid_output_is_error_not_missing_evidence(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic'}):
            agent = OpenRouterAgent(lambda *a, **kw: [self.row], provider='openai', max_repairs=0)
            with patch.object(agent, '_chat', return_value={'choices': [{'message': {'content': '{}'}}]}):
                result = agent.run('Câu hỏi minh họa')
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['reason'], 'output_validation_failed')

    def test_incidental_article_is_removed_from_focus_query(self):
        variants = query_variants('Trong hạn mức Điều 99 có thời hạn bao lâu; có phải gia hạn không?')
        self.assertNotIn('Điều 99', variants[-1])
        self.assertIn('gia hạn', variants[-1])

    def test_area_is_not_duration_evidence(self):
        context = '[e1] fixture\nDiện tích không quá 03 ha.'
        payload = {**self.payload, 'answer': 'Thời hạn là 03 ha [e1].',
                   'evidence_quotes': [{'id': 'e1', 'quote': 'Diện tích không quá 03 ha.'}]}
        errors, _ = validate_answer(payload, ['e1'], context, 'Thời hạn bao lâu, có gia hạn không?')
        self.assertTrue(any('duration' in e for e in errors))

    def test_render_only_model_selected_citation_with_matching_quote(self):
        payload = {**self.payload, 'answer': 'Thông tin minh họa.'}
        normalized, changes = normalize_answer(payload, ['e1'], self.context)
        self.assertIn('[e1]', normalized['answer'])
        self.assertTrue(changes)
        payload['citations'] = ['invented']
        normalized, _ = normalize_answer(payload, ['e1'], self.context)
        self.assertNotIn('[invented]', normalized['answer'])

    def test_abbreviated_quote_expands_from_exact_original_only(self):
        context = '[e1] fixture\nNội dung đầu; điều kiện bắt buộc; nội dung cuối;'
        payload = {**self.payload, 'evidence_quotes': [{'id': 'e1', 'quote': 'Nội dung đầu... nội dung cuối.'}]}
        normalized, _ = normalize_answer(payload, ['e1'], context)
        self.assertIn('điều kiện bắt buộc', normalized['evidence_quotes'][0]['quote'])
        self.assertFalse(validate_answer(normalized, ['e1'], context)[0])
        payload['evidence_quotes'][0]['quote'] = 'Nội dung bịa... nội dung cuối.'
        normalized, _ = normalize_answer(payload, ['e1'], context)
        self.assertTrue(validate_answer(normalized, ['e1'], context)[0])

    def test_quote_capitalization_restores_original_text(self):
        payload={**self.payload,'evidence_quotes':[{'id':'e1','quote':self.row['text'].lower()}]}
        normalized,changes=normalize_answer(payload,['e1'],self.context)
        self.assertEqual(normalized['evidence_quotes'][0]['quote'],self.row['text'])
        self.assertIn('restored_exact_source_capitalization',changes)

    def test_pipeline_does_not_force_incidental_article(self):
        rows = [chunk('e1', 'Thời hạn sử dụng nêu tại văn bản.', '12'),
                chunk('e2', 'Hạn mức diện tích.', '99')]
        calls = []
        def dense(query, k, filters):
            calls.append(query)
            return [{**rows[0], 'score': 0.9}, {**rows[1], 'score': 0.1}]
        pipeline = LegalPipeline(rows, dense)
        results = pipeline.search('Trong hạn mức Điều 99 có thời hạn sử dụng bao lâu?')
        self.assertEqual(results[0]['id'], 'e1')
        self.assertGreater(len(calls), 1)


if __name__ == '__main__': unittest.main()
