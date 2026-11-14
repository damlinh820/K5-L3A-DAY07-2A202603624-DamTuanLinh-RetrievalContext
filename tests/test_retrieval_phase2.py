import unittest

from src.retrieval import BM25Retriever, DenseRetriever, DenseUnavailable, reciprocal_rank_fusion, tokenize_vietnamese, transform_legal_query, metadata_aware_rerank


def chunk(cid, text, page=1, metadata=None):
    return {"id": cid, "text": text, "source_id": "law", "source": "law.pdf", "page": page,
            "metadata": metadata or {}}


class RetrievalPhase2Tests(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            chunk("a", "Điều 45. Người sử dụng đất được cấp giấy chứng nhận.", metadata={"part": 1}),
            chunk("b", "Điều 121. Chuyển đất nông nghiệp sang đất phi nông nghiệp.", metadata={"part": 2}),
            chunk("c", "Điều 171. Đất ở sử dụng ổn định lâu dài.", metadata={"part": 3}),
        ]

    def test_vietnamese_tokenization_preserves_accents_and_numbers(self):
        self.assertIn("đất", tokenize_vietnamese("Đất đai Điều 45"))
        self.assertIn("45", tokenize_vietnamese("Đất đai Điều 45"))

    def test_bm25_ranks_matching_clause_and_filter(self):
        index = BM25Retriever(self.chunks)
        result = index.search("chuyển đất nông nghiệp", top_k=2, filters={"part": 2})
        self.assertEqual([row["id"] for row in result], ["b"])
        self.assertEqual(result[0]["strategy"], "bm25")

    def test_rrf_merges_duplicate_and_ties_by_id(self):
        left = [self.chunks[1], self.chunks[0]]
        right = [self.chunks[0], self.chunks[1]]
        result = reciprocal_rank_fusion({"dense": left, "bm25": right}, rrf_k=1, top_k=2)
        self.assertEqual({row["id"] for row in result}, {"a", "b"})
        self.assertEqual(result[0]["source_ranks"]["dense"], 2)
        self.assertIn("bm25", result[0]["source_scores"])

    def test_dense_missing_backend_is_explicit(self):
        with self.assertRaises(DenseUnavailable):
            DenseRetriever().search("đất", top_k=3)

    def test_dense_validates_duplicate_ids(self):
        def backend(query, top_k, filters):
            return [{**self.chunks[0], "score": 1.0}, {**self.chunks[0], "score": 0.9}]
        with self.assertRaises(ValueError):
            DenseRetriever(backend).search("đất", top_k=2)

    def test_query_transform_and_metadata_boost(self):
        self.assertIn("Điều 45 khoản 1", transform_legal_query("Điều 45 khoản 1 điều kiện"))
        rows = [{**self.chunks[0], "metadata": {"article": "45"}, "score": 0.1}, {**self.chunks[1], "score": 0.2}]
        self.assertEqual(metadata_aware_rerank("Điều 45", rows)[0]["id"], "a")


if __name__ == "__main__":
    unittest.main()
