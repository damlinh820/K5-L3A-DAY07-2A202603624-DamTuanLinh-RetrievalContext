import unittest
from src.evaluation import agent_metrics, fraction, supports_gold


class EvaluationTests(unittest.TestCase):
    def test_multipage_provenance_matches_gold_page(self):
        chunk={'source_id':'s','page':1,'text':'Trích đoạn cần tìm.', 'provenance':[{'page':1},{'page':2}]}
        gold=[{'source_id':'s','page':2,'evidence_quote':'Trích đoạn cần tìm.'}]
        self.assertTrue(supports_gold(chunk,gold))
        self.assertFalse(supports_gold({**chunk,'source_id':'wrong'},gold))
        self.assertIsNone(fraction(0,0)['rate'])

    def test_reviews_do_not_transfer_between_runs(self):
        rows=[{'query_id':'q','result':{'status':'answered','citations':[],'events':[]}}]
        cases=[{'id':'q','answerability':'answerable'}]
        labels=[{'case_id':'q','run_id':'old','status':'human_verified','grounded_answer_0_2':'2'}]
        metric=agent_metrics(rows,cases,labels,'new')
        self.assertEqual(metric['grounded']['reviewed'],0)
        self.assertIsNone(metric['grounded']['mean_out_of_2'])
        self.assertIsNone(metric['citation_support']['rate'])


if __name__=='__main__':unittest.main()
