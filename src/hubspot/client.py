"""
HubSpot data access via MCP.

Uses the HubSpot MCP server (@hubspot/mcp-server) through the MCP Python client.
The server must be running and accessible. Credentials are passed via env var
HUBSPOT_ACCESS_TOKEN (set in .env).

All public methods return structured Pydantic models — callers never touch raw
MCP payloads.
"""
import asyncio
import os
from datetime import date
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from src.hubspot.models import Company, Contact, Deal
from config.settings import ACTIVE_DEAL_PIPELINE, HUBSPOT_ACCESS_TOKEN


def _mcp_server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command="npx",
        args=["-y", "@hubspot/mcp-server"],
        env={**os.environ, "HUBSPOT_ACCESS_TOKEN": HUBSPOT_ACCESS_TOKEN},
    )


async def _call(tool: str, args: dict) -> Any:
    async with stdio_client(_mcp_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, args)
            return result.content


# ── Companies ────────────────────────────────────────────────────────────────

async def fetch_active_companies(
    nature: list[str] | None = None,
    tier_company: list[str] | None = None,
    macro_category: list[str] | None = None,
    beginning_date_from: date | None = None,
    beginning_date_to: date | None = None,
    arr_live_min: float | None = None,
    arr_live_max: float | None = None,
) -> list[Company]:
    """
    Returns companies where arr_live != 0, optionally narrowed by the
    PM-supplied filters. Deals and contacts are NOT yet populated here —
    call enrich_company() to traverse the graph.
    """
    filters = [{"propertyName": "arr_live", "operator": "NEQ", "value": "0"}]

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

    raw = await _call("hubspot_search_objects", {
        "objectType": "companies",
        "filterGroups": [{"filters": filters}],
        "properties": ["name", "nature", "tier_company", "macro_category",
                        "beginning_date", "arr_live", "country"],
        "limit": 1000,
    })

    return [_parse_company(r) for r in raw.get("results", [])]


def _parse_company(raw: dict) -> Company:
    props = raw.get("properties", {})
    return Company(
        id=raw["id"],
        name=props.get("name", ""),
        nature=props.get("nature"),
        tier_company=props.get("tier_company"),
        macro_category=props.get("macro_category"),
        beginning_date=_parse_date(props.get("beginning_date")),
        arr_live=float(props.get("arr_live") or 0),
        country=props.get("country"),
    )


# ── Deals ─────────────────────────────────────────────────────────────────────

async def fetch_deals_for_company(company_id: str) -> list[Deal]:
    """Returns active deals (pipeline = ACTIVE_DEAL_PIPELINE) for a company."""
    raw = await _call("hubspot_get_associations", {
        "objectType": "companies",
        "objectId": company_id,
        "toObjectType": "deals",
    })

    deal_ids = [r["id"] for r in raw.get("results", [])]
    if not deal_ids:
        return []

    deals_raw = await _call("hubspot_batch_read_objects", {
        "objectType": "deals",
        "inputs": [{"id": d} for d in deal_ids],
        "properties": ["dealname", "pipeline", "createdate"],
    })

    active = [
        _parse_deal(r)
        for r in deals_raw.get("results", [])
        if r.get("properties", {}).get("pipeline") == ACTIVE_DEAL_PIPELINE
    ]
    active.sort(key=lambda d: d.created_at, reverse=True)
    return active


def _parse_deal(raw: dict) -> Deal:
    props = raw.get("properties", {})
    return Deal(
        id=raw["id"],
        name=props.get("dealname", ""),
        pipeline=props.get("pipeline", ""),
        created_at=_parse_date(props.get("createdate")) or date.today(),
    )


# ── Contacts ──────────────────────────────────────────────────────────────────

async def fetch_contacts_for_deal(deal_id: str) -> list[Contact]:
    """Returns contacts on a deal that have a non-empty engagement_score_v2."""
    raw = await _call("hubspot_get_associations", {
        "objectType": "deals",
        "objectId": deal_id,
        "toObjectType": "contacts",
    })

    contact_ids = [r["id"] for r in raw.get("results", [])]
    if not contact_ids:
        return []

    contacts_raw = await _call("hubspot_batch_read_objects", {
        "objectType": "contacts",
        "inputs": [{"id": c} for c in contact_ids],
        "properties": ["firstname", "lastname", "email", "engagement_score_v2", "nps"],
    })

    contacts = [_parse_contact(r) for r in contacts_raw.get("results", [])]
    return [c for c in contacts if c.engagement_score_v2 is not None]


def _parse_contact(raw: dict) -> Contact:
    props = raw.get("properties", {})
    score = props.get("engagement_score_v2")
    nps = props.get("nps")
    return Contact(
        id=raw["id"],
        first_name=props.get("firstname", ""),
        last_name=props.get("lastname", ""),
        email=props.get("email", ""),
        engagement_score_v2=float(score) if score else None,
        nps=float(nps) if nps else None,
    )


# ── Discrete property values (for UI dropdowns) ───────────────────────────────

async def fetch_property_options(object_type: str, property_name: str) -> list[str]:
    """Returns the enumeration options for a discrete HubSpot property."""
    raw = await _call("hubspot_get_property", {
        "objectType": object_type,
        "propertyName": property_name,
    })
    options = raw.get("options", [])
    return sorted([o["value"] for o in options if o.get("value")])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def run(coro):
    """Convenience wrapper so sync Streamlit code can call async functions."""
    return asyncio.run(coro)
