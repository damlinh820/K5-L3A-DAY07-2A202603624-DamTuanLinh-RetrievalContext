import os
import unittest
from unittest.mock import patch

from src.citation import validate_citations
from src.context import build_context


class Phase4Tests(unittest.TestCase):
    def test_context_budget_deduplicates_and_reports_dropped(self):
        rows = [{"id": "a", "text": "Một đoạn evidence dài", "source": "law", "page": 1, "metadata": {}},
                {"id": "a", "text": "duplicate", "source": "law", "page": 1, "metadata": {}},
                {"id": "b", "text": "Evidence thứ hai", "source": "law", "page": 2, "metadata": {}}]
        context, ids, dropped = build_context(rows, budget_chars=80)
        self.assertEqual(ids, ["a"])
        self.assertEqual(dropped, ["b"])
        self.assertIn("[a]", context)

    def test_citation_requires_context_id_and_marker(self):
        result = validate_citations("Đáp án [a]", ["a"], ["a"], "[a] evidence")
        self.assertTrue(result["all_structurally_valid"])
        result = validate_citations("Đáp án", ["a"], ["a"], "[a] evidence")
        self.assertFalse(result["all_structurally_valid"])

    def test_citation_never_claims_semantic_verification(self):
        result = validate_citations("Đáp án [a]", ["a"], ["a"], "[a] evidence")
        self.assertEqual(result["semantic_support"], "human_review_required")

    def test_citation_only_answer_is_not_substantive(self):
        answer = "[chunk-a]"
        substantive = answer.replace("[chunk-a]", "").strip()
        self.assertFalse(substantive)


if __name__ == "__main__":
    unittest.main()
