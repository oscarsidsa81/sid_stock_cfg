import unittest

from plan_validation import summarize_duplicate_names, validate_xmlid_plan


class TestValidateXmlidPlan(unittest.TestCase):
    def test_valid_plan(self):
        plan = [{"model": "ir.sequence", "res_id": 1, "name": "x"}]
        report = validate_xmlid_plan(plan)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["duplicate_names"], {})

    def test_detects_missing_fields_and_invalid_types(self):
        plan = [
            {"model": "ir.sequence", "name": "x"},
            {"model": "ir.sequence", "res_id": "1", "name": ""},
            "bad",
        ]
        report = validate_xmlid_plan(plan)
        self.assertGreaterEqual(len(report["errors"]), 4)

    def test_detects_duplicate_names(self):
        plan = [
            {"model": "ir.sequence", "res_id": 1, "name": "dup"},
            {"model": "stock.picking.type", "res_id": 2, "name": "dup"},
        ]
        report = validate_xmlid_plan(plan)
        self.assertIn("dup", report["duplicate_names"])
        self.assertEqual(report["duplicate_names"]["dup"], [0, 1])

    def test_summarize_duplicate_names_is_compact_and_stable(self):
        duplicates = {
            "zeta": [2, 9],
            "alpha": [0, 1],
            "beta": [3, 7],
        }
        summary = summarize_duplicate_names(duplicates, max_items=2)
        self.assertEqual(summary, "alpha@[0, 1]; beta@[3, 7]; ... +1 more")


if __name__ == "__main__":
    unittest.main()
