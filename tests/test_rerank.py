import unittest

from src.rerank import lexical_rerank


class RerankTests(unittest.TestCase):
    def test_exact_article_bonus_and_determinism(self):
        base = {"source_id": "law", "source": "law.pdf", "page": 1, "metadata": {"article": "45"}}
        rows = [
            {**base, "id": "z", "text": "Điều 45 điều kiện giấy chứng nhận", "score": 0.1},
            {**base, "id": "a", "text": "Điều kiện giấy chứng nhận", "metadata": {"article": "46"}, "score": 0.9},
        ]
        result = lexical_rerank("điểm a khoản 1 Điều 45 giấy chứng nhận", rows)
        self.assertEqual(result[0]["id"], "z")
        self.assertEqual(result[0]["strategy"], "hybrid_lexical_rerank")


if __name__ == "__main__":
    unittest.main()
