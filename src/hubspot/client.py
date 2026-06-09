"""
HubSpot data access via HubSpot CRM API v3.
Token: HS_TOKEN in .env (private app, CRM read scopes).
"""
import requests
from datetime import date
from typing import Any

from src.hubspot.models import Company, Contact, Deal
from config.settings import HS_TOKEN, ACTIVE_DEAL_PIPELINE

_BASE = "https://api.hubapi.com"
_HEADERS = {"Authorization": f"Bearer {HS_TOKEN}", "Content-Type": "application/json"}


def _get(path: str, params: dict | None = None) -> dict:
    r = requests.get(f"{_BASE}{path}", headers=_HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict) -> dict:
    r = requests.post(f"{_BASE}{path}", headers=_HEADERS, json=body, timeout=30)
    r.raise_for_status()
    return r.json()


# ── Companies ────────────────────────────────────────────────────────────────

def fetch_active_companies(
    nature: list[str] | None = None,
    tier_company: list[str] | None = None,
    macro_category: list[str] | None = None,
    beginning_date_from: date | None = None,
    beginning_date_to: date | None = None,
    arr_live_min: float | None = None,
    arr_live_max: float | None = None,
) -> tuple[list[Company], int]:
    """
    Returns (companies, total_count) — companies with arr_live > 0 matching all filters.
    Paginates automatically (100 per page).
    """
    filters = [{"propertyName": "arr_live", "operator": "GT", "value": "0"}]

    if nature:
        filters.append({"propertyName": "nature", "operator": "IN", "values": nature})
    if tier_company:
        filters.append({"propertyName": "tier_company", "operator": "IN", "values": tier_company})
    if macro_category:
        filters.append({"propertyName": "macro_category", "operator": "IN", "values": macro_category})
    if beginning_date_from:
        filters.append({"propertyName": "beginning_date", "operator": "GTE", "value": beginning_date_from.isoformat()})
    if beginning_date_to:
        filters.append({"propertyName": "beginning_date", "operator": "LTE", "value": beginning_date_to.isoformat()})
    if arr_live_min is not None:
        filters.append({"propertyName": "arr_live", "operator": "GTE", "value": str(arr_live_min)})
    if arr_live_max is not None:
        filters.append({"propertyName": "arr_live", "operator": "LTE", "value": str(arr_live_max)})

    companies: list[Company] = []
    total: int = 0
    after: str | None = None

    while True:
        body: dict = {
            "filterGroups": [{"filters": filters}],
            "properties": ["name", "nature", "tier_company", "macro_category",
                           "beginning_date", "arr_live", "country"],
            "limit": 100,
        }
        if after:
            body["after"] = after

        raw = _post("/crm/v3/objects/companies/search", body)
        if not total:
            total = raw.get("total", 0)
        companies.extend(_parse_company(r) for r in raw.get("results", []))

        after = raw.get("paging", {}).get("next", {}).get("after")
        if not after:
            break

    return companies, total


def _parse_company(raw: dict) -> Company:
    props = raw.get("properties", {})
    return Company(
        id=str(raw["id"]),
        name=props.get("name", ""),
        nature=props.get("nature"),
        tier_company=props.get("tier_company"),
        macro_category=props.get("macro_category"),
        beginning_date=_parse_date(props.get("beginning_date")),
        arr_live=float(props.get("arr_live") or 0),
        country=props.get("country"),
    )


# ── Deals ─────────────────────────────────────────────────────────────────────

def fetch_deals_for_company(company_id: str) -> list[Deal]:
    """Most recent active deal (pipeline = ACTIVE_DEAL_PIPELINE) for a company."""
    raw = _get(f"/crm/v3/objects/companies/{company_id}/associations/deals")
    deal_ids = [r["id"] for r in raw.get("results", [])]
    if not deal_ids:
        return []

    batch = _post("/crm/v3/objects/deals/batch/read", {
        "inputs": [{"id": d} for d in deal_ids],
        "properties": ["dealname", "pipeline", "createdate"],
    })
    active = [
        _parse_deal(r)
        for r in batch.get("results", [])
        if r.get("properties", {}).get("pipeline") == ACTIVE_DEAL_PIPELINE
    ]
    active.sort(key=lambda d: d.created_at, reverse=True)
    return active


def _parse_deal(raw: dict) -> Deal:
    props = raw.get("properties", {})
    return Deal(
        id=str(raw["id"]),
        name=props.get("dealname", ""),
        pipeline=props.get("pipeline", ""),
        created_at=_parse_date(props.get("createdate")) or date.today(),
    )


# ── Contacts ──────────────────────────────────────────────────────────────────

def fetch_contacts_for_deal(deal_id: str) -> list[Contact]:
    """Contacts on a deal that have engagement_score_v2 set."""
    raw = _get(f"/crm/v3/objects/deals/{deal_id}/associations/contacts")
    contact_ids = [r["id"] for r in raw.get("results", [])]
    if not contact_ids:
        return []

    batch = _post("/crm/v3/objects/contacts/batch/read", {
        "inputs": [{"id": c} for c in contact_ids],
        "properties": ["firstname", "lastname", "email", "engagement_score_v2"],
    })
    contacts = [_parse_contact(r) for r in batch.get("results", [])]
    return [c for c in contacts if c.engagement_score_v2 is not None]


def _parse_contact(raw: dict) -> Contact:
    props = raw.get("properties", {})
    score = props.get("engagement_score_v2")
    return Contact(
        id=str(raw["id"]),
        first_name=props.get("firstname", ""),
        last_name=props.get("lastname", ""),
        email=props.get("email", ""),
        engagement_score_v2=float(score) if score else None,
    )


# ── Property options (UI dropdowns) ──────────────────────────────────────────

def fetch_property_options(object_type: str, property_name: str) -> list[str]:
    """Enumeration values for a HubSpot property."""
    raw = _get(f"/crm/v3/properties/{object_type}/{property_name}")
    return sorted(o["value"] for o in raw.get("options", []) if o.get("value"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
