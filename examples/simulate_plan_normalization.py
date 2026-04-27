#!/usr/bin/env python3
"""Simula validación/normalización del XMLID_PLAN con ejemplos pequeños."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from plan_validation import (  # noqa: E402
    build_safe_xmlid_plan,
    summarize_duplicate_names,
    summarize_non_ascii_names,
    summarize_renamed_entries,
    validate_xmlid_plan,
)


def main():
    sample_plan = [
        {"model": "stock.rule", "res_id": 101, "name": "stock_rule__vendor_madrid_cliente__seq20__mad_stock_customers__c1"},
        {"model": "stock.rule", "res_id": 102, "name": "stock_rule__vendor_madrid_cliente__seq20__mad_stock_customers__c1"},
        {"model": "stock.rule", "res_id": 103, "name": "stock_rule__madrid_preparación__seq20__devolución__c1"},
        {"model": "stock.rule", "res_id": 104, "name": "stock_rule__madrid-preparacion__seq20__devolucion__c1"},
    ]

    report = validate_xmlid_plan(sample_plan)
    execution_plan, rename_map = build_safe_xmlid_plan(sample_plan)

    print("=== INPUT PLAN ===")
    print(json.dumps(sample_plan, indent=2, ensure_ascii=False))

    print("\n=== VALIDATION REPORT ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    print("\n=== SUMMARIES ===")
    print("duplicate_names:", summarize_duplicate_names(report["duplicate_names"]))
    print("non_ascii_names:", summarize_non_ascii_names(report["non_ascii_names"]))
    print("renamed_entries:", summarize_renamed_entries(rename_map))

    print("\n=== NORMALIZED EXECUTION PLAN (name) ===")
    for item in execution_plan:
        print(f"res_id={item['res_id']}: {item['name']}")


if __name__ == "__main__":
    main()
