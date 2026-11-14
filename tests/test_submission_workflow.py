"""Regression tests for cross-run labels, new case IDs and one-time test gates."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.api import with_context_chunks
from src.evaluation import agent_metrics, holdout_status, load_dashboard, trace_hash
from src.holdout import reserve_holdout, sha, validate_diagnostic, validate_holdout
from src.reviews import finalize_reviews, prepare_reviews, validate_reviews, write_json


class SubmissionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = [{'id':'h01','split':'test','question':'fixture','answerability':'answerable','gold':[]},
                      {'id':'h06','split':'test','question':'absent','answerability':'insufficient_evidence','gold':[]}]
        self.rows = [{'query_id':'h01','result':{'status':'answered','answer':'[one] [two]',
                      'context_ids':['one'],'citations':['one','two'],'events':[]}},
                     {'query_id':'h06','result':{'status':'abstain','citations':[],'events':[]}}]
        self.run_id = 'fresh/dense'

    def label(self, row):
        return {'run_id':self.run_id,'case_id':row['query_id'],'status':'human_verified',
                'trace_sha256':trace_hash(row),'reviewer':'fixture reviewer','reviewed_at':'2026-11-14T12:00:00Z',
                'source_verified':True,'notes':'fixture verified','evidence_sufficiency_0_2':2,
                'grounded_answer_0_2':2,'abstention_correct':row['result']['status']=='abstain',
                'citation_reviews':[{'citation_index':i,'citation_id':cid,'supported':True,'reason':'fixture'}
                                     for i,cid in enumerate(row['result']['citations'])]}

    def make_run(self):
        group = self.root/'runs/fresh'
        mode = group/'dense'
        mode.mkdir(parents=True)
        benchmark = group/'benchmark.jsonl'
        benchmark.write_text(''.join(json.dumps(c)+'\n' for c in self.cases),encoding='utf8')
        write_json(group/'manifest.json',{'benchmark_file':'benchmark.jsonl','benchmark_sha256':sha(benchmark),
                                          'status':'finished','evaluation_type':'fresh_holdout'})
        write_json(mode/'all_traces.json',self.rows)
        return mode

    def test_citation_support_requires_context_and_excludes_abstentions_from_answer_denominator(self):
        metric = agent_metrics(self.rows,self.cases,[self.label(r) for r in self.rows],self.run_id)
        self.assertEqual(metric['citation_support']['n'],1)
        self.assertEqual(metric['citation_support']['N'],2)
        self.assertEqual(metric['citation_support']['rate'],0.5)
        self.assertEqual(metric['answers_with_citations']['N'],1)
        self.assertEqual(metric['context_grades']['counts']['2'],1)

    def test_partial_citation_review_keeps_full_denominator_and_unknown_rate(self):
        label = self.label(self.rows[0])
        label['citation_reviews'].pop()
        metric = agent_metrics(self.rows,self.cases,[label],self.run_id)
        self.assertEqual(metric['citation_support']['N'],2)
        self.assertEqual(metric['citation_support']['unreviewed'],1)
        self.assertIsNone(metric['citation_support']['rate'])
        self.assertEqual(metric['semantic_review_status'],'partial')

    def test_legacy_grade_does_not_imply_per_citation_support(self):
        label = self.label(self.rows[0])
        del label['citation_reviews']
        label['citation_support_0_2']='2'
        metric = agent_metrics(self.rows,self.cases,[label],self.run_id)
        self.assertEqual(metric['citation_support']['unreviewed'],2)

    def test_changed_trace_invalidates_review(self):
        label = self.label(self.rows[0])
        self.rows[0]['result']['answer']='changed'
        metric = agent_metrics(self.rows,self.cases,[label],self.run_id)
        self.assertEqual(metric['grounded']['reviewed'],0)
        self.assertEqual(metric['stale_review_case_ids'],['h01'])

    def test_new_benchmark_ids_resolve_from_snapshot_and_finalize_without_model(self):
        mode = self.make_run()
        paths = prepare_reviews(self.root,mode)
        pending = json.loads((self.root/paths[0]).read_text(encoding='utf8'))
        with self.assertRaises(ValueError): validate_reviews(self.rows,self.cases,pending,self.run_id)
        review = self.root/'confirmed.json'
        write_json(review,[self.label(r) for r in self.rows])
        finalize_reviews(self.root,mode,review)
        dashboard = load_dashboard(self.root)
        self.assertEqual(dashboard['artifact_issues'],[])
        self.assertEqual(dashboard['agents'][0]['run_id'],self.run_id)
        self.assertEqual(dashboard['agents'][0]['semantic_review_status'],'human_verified')
        with self.assertRaises(ValueError): prepare_reviews(self.root,mode)

    def test_positive_grounded_grade_for_abstention_is_rejected(self):
        self.rows[0]['result']['status']='abstain'
        with self.assertRaises(ValueError):
            validate_reviews(self.rows,self.cases,[self.label(r) for r in self.rows],self.run_id)

    def test_partial_review_stays_partial_until_other_cases_are_confirmed(self):
        mode = self.make_run()
        review = self.root/'subset.json'
        write_json(review,[self.label(self.rows[0])])
        with self.assertRaises(ValueError): finalize_reviews(self.root,mode,review)
        finalize_reviews(self.root,mode,review,partial=True)
        self.assertEqual(load_dashboard(self.root)['agents'][0]['semantic_review_status'],'partial')

    def test_holdout_complete_requires_both_modes_and_exact_current_traces(self):
        dense = self.make_run()
        hybrid = dense.parent/'hybrid_improved'
        hybrid.mkdir()
        write_json(hybrid/'all_traces.json',self.rows)
        write_json(self.root/'configs/final_tool_agent.json',{'test_modes':['dense','hybrid_improved']})
        write_json(self.root/'benchmarks/fresh_holdout_manifest.json',{
            'approved':True,'executed':True,'run_directory':'runs/fresh','benchmark':'runs/fresh/benchmark.jsonl'})
        review = self.root/'confirmed.json'
        write_json(review,[self.label(r) for r in self.rows])
        finalize_reviews(self.root,dense,review)
        self.assertEqual(holdout_status(self.root)['status'],'pending_human_review')
        labels=[{**self.label(r),'run_id':'fresh/hybrid_improved'} for r in self.rows]
        write_json(review,labels)
        finalize_reviews(self.root,hybrid,review)
        self.assertTrue(holdout_status(self.root)['ready'])
        self.rows[0]['result']['answer']='changed'
        write_json(hybrid/'all_traces.json',self.rows)
        self.assertFalse(holdout_status(self.root)['ready'])

    def test_context_card_includes_neighbor_missing_from_search_results(self):
        corpus = self.root/'corpus.jsonl'
        corpus.write_text(json.dumps({'chunk_id':'neighbor','document_id':'s','source':'https://example.test',
                                     'page':2,'page_end':2,'text':'neighbor','article':'1','clause':'2'})+'\n')
        result = with_context_chunks({'context_ids':['neighbor'],'events':[]},corpus)
        self.assertEqual(result['context_chunks'][0]['id'],'neighbor')

    def make_approval(self):
        config_source = Path(__file__).resolve().parents[1]/'configs/final_tool_agent.json'
        config = json.loads(config_source.read_text(encoding='utf8'))
        config['runtime_sha256']={}
        config['index_manifest']={'path':'index.json','sha256':''}
        write_json(self.root/'index.json',{'fixture':True})
        config['index_manifest']['sha256']=sha(self.root/'index.json')
        write_json(self.root/'configs/final_tool_agent.json',config)
        questions = self.root/'questions.jsonl'
        cases = [{'id':f'h{i}','split':'test','answerability':'answerable' if i<5 else 'insufficient_evidence',
                  'gold_status':'human_verified','reviewer':'fixture','review_timestamp':'2026-11-14'} for i in range(7)]
        questions.write_text(''.join(json.dumps(c)+'\n' for c in cases),encoding='utf8')
        corpus = self.root/'corpus.jsonl'
        corpus.write_text('fixture')
        write_json(self.root/'benchmarks/fresh_holdout_manifest.json',{
            'approved':True,'reviewer':'fixture reviewer','approved_at':'2026-11-14','executed':False,
            'benchmark_sha256':sha(questions),'config_sha256':sha(self.root/'configs/final_tool_agent.json'),
            'corpus_sha256':sha(corpus)})
        args = SimpleNamespace(questions=questions,modes=config['test_modes'],max_run_cost_usd=.2)
        settings = SimpleNamespace(corpus=corpus,model=config['model'],max_cost_usd=.1)
        return args,settings

    def test_corpus_change_blocks_test_before_execution(self):
        args,settings = self.make_approval()
        validate_holdout(self.root,args,settings)
        settings.corpus.write_text('changed')
        with self.assertRaisesRegex(ValueError,'Corpus changed'): validate_holdout(self.root,args,settings)

    def test_reserved_holdout_cannot_be_repeated_with_another_output(self):
        args,settings = self.make_approval()
        reserve_holdout(self.root,args,settings,self.root/'runs/first')
        with self.assertRaisesRegex(ValueError,'already started'): validate_holdout(self.root,args,settings)

    def test_diagnostic_cannot_open_a_fresh_unexecuted_benchmark(self):
        args,settings = self.make_approval()
        with self.assertRaisesRegex(ValueError,'unopened'): validate_diagnostic(self.root,args.questions)
        reserve_holdout(self.root,args,settings,self.root/'runs/first')
        validate_diagnostic(self.root,args.questions)

    def test_unreviewed_gold_or_budget_change_blocks_execution(self):
        args,settings = self.make_approval()
        settings.max_cost_usd=.5
        with self.assertRaisesRegex(ValueError,'budgets'): validate_holdout(self.root,args,settings)
        settings.max_cost_usd=.1
        config_path=self.root/'configs/final_tool_agent.json'
        config=json.loads(config_path.read_text())
        config['context_budget_chars']=999
        write_json(config_path,config)
        approval_path=self.root/'benchmarks/fresh_holdout_manifest.json'
        approval=json.loads(approval_path.read_text())
        approval['config_sha256']=sha(config_path)
        write_json(approval_path,approval)
        with self.assertRaisesRegex(ValueError,'parameters'): validate_holdout(self.root,args,settings)


if __name__=='__main__': unittest.main()
