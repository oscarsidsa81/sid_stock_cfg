# -*- coding: utf-8 -*-
"""Validation and normalization helpers for XMLID plan entries."""

import string
import unicodedata


ASCII_XMLID_CHARS = frozenset(string.ascii_lowercase + string.digits + "_")


def _normalize_xmlid_name(name):
    """Return a lowercase ASCII-safe XMLID name candidate."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_name.lower()
    return "".join(ch if ch in ASCII_XMLID_CHARS else "_" for ch in lowered).strip("_")


def validate_xmlid_plan(plan):
    """Return validation issues for an XMLID plan.

    Returns a dict with:
      - errors: fatal issues that should block execution
      - duplicate_names: map of name -> indexes where repeated
      - non_ascii_names: map of name -> indexes containing non-ASCII chars
    """
    required_fields = ("model", "res_id", "name")
    errors = []
    names = {}
    non_ascii_names = {}

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
            if any(char not in ASCII_XMLID_CHARS for char in name):
                non_ascii_names.setdefault(name, []).append(idx)
        else:
            errors.append(f"index {idx}: name must be a non-empty string")

    duplicate_names = {name: idxs for name, idxs in names.items() if len(idxs) > 1}

    return {
        "errors": errors,
        "duplicate_names": duplicate_names,
        "non_ascii_names": non_ascii_names,
    }


def build_safe_xmlid_plan(plan):
    """Return a copy of plan with deterministic, ASCII-safe and unique names."""
    normalized_entries = []
    base_name_to_indexes = {}

    for idx, item in enumerate(plan):
        new_item = dict(item)
        base_name = _normalize_xmlid_name(item["name"])
        if not base_name:
            base_name = f"xmlid_{item['model'].replace('.', '_')}"
        normalized_entries.append((idx, new_item, base_name))
        base_name_to_indexes.setdefault(base_name, []).append(idx)

    used_names = set()
    rename_map = {}
    safe_plan = []

    for idx, new_item, base_name in normalized_entries:
        if len(base_name_to_indexes[base_name]) > 1:
            candidate = f"{base_name}__id_{new_item['res_id']}"
        else:
            candidate = base_name

        if candidate in used_names:
            candidate = f"{candidate}__idx_{idx}"

        if candidate != new_item["name"]:
            rename_map[idx] = {
                "old": new_item["name"],
                "new": candidate,
                "res_id": new_item["res_id"],
            }

        new_item["name"] = candidate
        used_names.add(candidate)
        safe_plan.append(new_item)

    return safe_plan, rename_map


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


def summarize_non_ascii_names(non_ascii_names, max_items=5):
    """Build a compact and stable summary for non-ASCII names."""
    if not non_ascii_names:
        return ""

    ordered = sorted(non_ascii_names.items(), key=lambda item: item[0])
    snippets = [f"{name}@{idxs}" for name, idxs in ordered[:max_items]]
    remaining = len(ordered) - len(snippets)
    if remaining > 0:
        snippets.append(f"... +{remaining} more")
    return "; ".join(snippets)


def summarize_renamed_entries(rename_map, max_items=5):
    """Build a compact and stable summary for renamed XML-ID names."""
    if not rename_map:
        return ""

    ordered = sorted(rename_map.items(), key=lambda item: item[0])
    snippets = [f"#{idx}:{change['old']}->{change['new']}" for idx, change in ordered[:max_items]]
    remaining = len(ordered) - len(snippets)
    if remaining > 0:
        snippets.append(f"... +{remaining} more")
    return "; ".join(snippets)
