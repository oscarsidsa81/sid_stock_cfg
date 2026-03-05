# -*- coding: utf-8 -*-
"""Validation helpers for XMLID plan entries."""


def validate_xmlid_plan(plan):
    """Return validation issues for an XMLID plan.

    Returns a dict with:
      - errors: fatal issues that should block execution
      - duplicate_names: map of name -> indexes where repeated
    """
    required_fields = ("model", "res_id", "name")
    errors = []
    names = {}

    for idx, item in enumerate(plan):
        if not isinstance(item, dict):
            errors.append(f"index {idx}: expected dict, got {type(item).__name__}")
            continue

        for field in required_fields:
            if field not in item:
                errors.append(f"index {idx}: missing field '{field}'")

        if "res_id" in item and not isinstance(item["res_id"], int):
            errors.append(f"index {idx}: res_id must be int (got {type(item['res_id']).__name__})")

        name = item.get("name")
        if isinstance(name, str) and name:
            names.setdefault(name, []).append(idx)
        else:
            errors.append(f"index {idx}: name must be a non-empty string")

    duplicate_names = {name: idxs for name, idxs in names.items() if len(idxs) > 1}

    return {
        "errors": errors,
        "duplicate_names": duplicate_names,
    }


def summarize_duplicate_names(duplicate_names, max_items=5):
    """Build a compact and stable summary for duplicate-name warnings."""
    if not duplicate_names:
        return ""

    ordered = sorted(duplicate_names.items(), key=lambda item: item[0])
    snippets = [f"{name}@{idxs}" for name, idxs in ordered[:max_items]]
    remaining = len(ordered) - len(snippets)
    if remaining > 0:
        snippets.append(f"... +{remaining} more")
    return "; ".join(snippets)
