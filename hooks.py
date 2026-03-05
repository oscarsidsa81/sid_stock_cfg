# -*- coding: utf-8 -*-
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# This module does NOT create or modify stock records.
# It only creates stable external IDs (ir.model.data) pointing to EXISTING records,
# so that other custom modules can safely reference them via xml_id.
#
# Naming convention used in this database export:
#   sid_stock_cfg.<model_prefix>__<human_slug>__c<company_id>
#
from .xmlid_plan import XMLID_PLAN

def _ensure_imd(env, model, res_id, name, key=None):
    """Ensure ir.model.data has (sid_stock_cfg, name) -> (model, res_id).

    We never delete or overwrite an existing ir.model.data with the same (module, name)
    that points elsewhere; instead we create a suffixed name to avoid collisions.
    """
    key = key or {}
    imd = env["ir.model.data"].sudo()

    rec = env[model].sudo().browse(res_id).exists()
    if not rec:
        _logger.warning(
            "XMLID_PLAN: target record missing: model=%s res_id=%s name=%s key=%s",
            model, res_id, name, key
        )
        return ("missing_record", None)

    existing = imd.search([("module", "=", "sid_stock_cfg"), ("name", "=", name)], limit=1)
    if existing:
        if existing.model == model and existing.res_id == res_id:
            return ("exists", "sid_stock_cfg." + name)

        # Collision: keep existing untouched, create a suffixed one.
        name2 = "%s__id_%s" % (name, res_id)
        existing2 = imd.search([("module", "=", "sid_stock_cfg"), ("name", "=", name2)], limit=1)
        if existing2:
            if existing2.model == model and existing2.res_id == res_id:
                return ("exists_suffixed", "sid_stock_cfg." + name2)
            _logger.warning(
                "XMLID_PLAN: suffixed name collision too: %s.%s points to %s,%s (wanted %s,%s). key=%s",
                "sid_stock_cfg", name2, existing2.model, existing2.res_id, model, res_id, key
            )
            return ("collision", None)

        imd.create({
            "module": "sid_stock_cfg",
            "name": name2,
            "model": model,
            "res_id": res_id,
            "noupdate": True,
        })
        _logger.info(
            "XMLID_PLAN: created (collision-safe) %s.%s -> %s,%s (original name %s was taken). key=%s",
            "sid_stock_cfg", name2, model, res_id, name, key
        )
        return ("created_suffixed", "sid_stock_cfg." + name2)

    imd.create({
        "module": "sid_stock_cfg",
        "name": name,
        "model": model,
        "res_id": res_id,
        "noupdate": True,
    })
    return ("created", "sid_stock_cfg." + name)


def _validate_xmlid_plan(plan):
    """Validate required fields and duplicated names before applying the plan."""
    required_fields = ("model", "res_id", "name")
    missing = []
    invalid = []
    names = {}

    for idx, item in enumerate(plan):
        if not isinstance(item, dict):
            invalid.append(f"index {idx}: expected dict, got {type(item).__name__}")
            continue

        for field in required_fields:
            if field not in item:
                missing.append(f"index {idx}: missing field '{field}'")

        if "res_id" in item and not isinstance(item["res_id"], int):
            invalid.append(f"index {idx}: res_id must be int (got {type(item['res_id']).__name__})")

        name = item.get("name")
        if isinstance(name, str) and name:
            names.setdefault(name, []).append(idx)
        else:
            invalid.append(f"index {idx}: name must be a non-empty string")

    duplicates = [name for name, idxs in names.items() if len(idxs) > 1]
    for name in duplicates:
        _logger.warning("XMLID_PLAN validation: name '%s' is duplicated at indexes %s", name, names[name])

    errors = missing + invalid
    if errors:
        raise ValueError("Invalid XMLID_PLAN:\n- " + "\n- ".join(errors))



def post_init_hook(cr, registry):
    _validate_xmlid_plan(XMLID_PLAN)
    env = api.Environment(cr, SUPERUSER_ID, {})
    counts = {
        "created": 0,
        "created_suffixed": 0,
        "exists": 0,
        "exists_suffixed": 0,
        "missing_record": 0,
        "collision": 0,
    }

    for item in XMLID_PLAN:
        status, _xmlid = _ensure_imd(
            env,
            item["model"],
            item["res_id"],
            item["name"],
            key=item.get("key"),
        )
        if status in counts:
            counts[status] += 1

    _logger.info("sid_stock_cfg: XMLID plan applied. stats=%s", counts)
