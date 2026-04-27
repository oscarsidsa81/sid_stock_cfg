import unittest

from plan_validation import (
    build_safe_xmlid_plan,
    summarize_duplicate_names,
    summarize_non_ascii_names,
    summarize_renamed_entries,
    validate_xmlid_plan,
)


class TestValidateXmlidPlan(unittest.TestCase):
    def test_valid_plan(self):
        plan = [{"model": "ir.sequence", "res_id": 1, "name": "x"}]
        report = validate_xmlid_plan(plan)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["duplicate_names"], {})
        self.assertEqual(report["non_ascii_names"], {})

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

    def test_detects_non_ascii_names(self):
        plan = [
            {"model": "ir.sequence", "res_id": 1, "name": "ascii_ok"},
            {"model": "ir.sequence", "res_id": 2, "name": "devolución"},
        ]
        report = validate_xmlid_plan(plan)
        self.assertIn("devolución", report["non_ascii_names"])
        self.assertEqual(report["non_ascii_names"]["devolución"], [1])


class TestPlanNormalization(unittest.TestCase):
    def test_build_safe_xmlid_plan_normalizes_duplicates_and_non_ascii(self):
        plan = [
            {"model": "stock.rule", "res_id": 10, "name": "Ruta_Cliente"},
            {"model": "stock.rule", "res_id": 11, "name": "Ruta_Cliente"},
            {"model": "stock.rule", "res_id": 12, "name": "devolución-final"},
        ]

        safe_plan, rename_map = build_safe_xmlid_plan(plan)

        self.assertEqual(
            [item["name"] for item in safe_plan],
            [
                "ruta_cliente__id_10",
                "ruta_cliente__id_11",
                "devolucion_final",
            ],
        )
        self.assertEqual(rename_map[0]["new"], "ruta_cliente__id_10")
        self.assertEqual(rename_map[2]["new"], "devolucion_final")

    def test_build_safe_xmlid_plan_resolves_post_normalization_collisions(self):
        plan = [
            {"model": "x.y", "res_id": 1, "name": "a-b"},
            {"model": "x.y", "res_id": 2, "name": "a_b"},
        ]

        safe_plan, _rename_map = build_safe_xmlid_plan(plan)
        self.assertEqual(safe_plan[0]["name"], "a_b__id_1")
        self.assertEqual(safe_plan[1]["name"], "a_b__id_2")


class TestSummaries(unittest.TestCase):
    def test_summarize_duplicate_names_is_compact_and_stable(self):
        duplicates = {
            "zeta": [2, 9],
            "alpha": [0, 1],
            "beta": [3, 7],
        }
        summary = summarize_duplicate_names(duplicates, max_items=2)
        self.assertEqual(summary, "alpha@[0, 1]; beta@[3, 7]; ... +1 more")

    def test_summarize_non_ascii_names_is_compact_and_stable(self):
        non_ascii = {
            "devolución": [0, 1],
            "preparación": [2],
            "recepción": [3],
        }
        summary = summarize_non_ascii_names(non_ascii, max_items=2)
        self.assertEqual(summary, "devolución@[0, 1]; preparación@[2]; ... +1 more")

    def test_summarize_renamed_entries_is_compact_and_stable(self):
        rename_map = {
            2: {"old": "b", "new": "b_2", "res_id": 22},
            0: {"old": "a", "new": "a_1", "res_id": 11},
            3: {"old": "c", "new": "c_3", "res_id": 33},
        }
        summary = summarize_renamed_entries(rename_map, max_items=2)
        self.assertEqual(summary, "#0:a->a_1; #2:b->b_2; ... +1 more")


if __name__ == "__main__":
    unittest.main()
