"""
HubSpot data access via the claude.ai MCP integration.
Uses the Anthropic API MCP client beta — no HubSpot Private App token required.
"""
import json
from datetime import date
from typing import Any

import anthropic

from src.hubspot.models import Company, Contact, Deal
from config.settings import ANTHROPIC_API_KEY, ACTIVE_DEAL_PIPELINE

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=300.0)

_HS_MCP = [{"type": "url", "url": "https://mcp.claude.ai/hubspot", "name": "hubspot"}]


def _call(prompt: str, max_tokens: int = 16000) -> Any:
    response = _client.beta.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        betas=["mcp-client-2025-04-04"],
        mcp_servers=_HS_MCP,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[-1].text.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        inner = parts[1]
        if inner.startswith("json"):
            inner = inner[4:].lstrip("\n")
        text = inner
    return json.loads(text.strip())


def fetch_property_options(object_type: str, property_name: str) -> list[str]:
    """Enumeration values for a HubSpot property — used to populate UI dropdowns."""
    raw = _call(
        f"Use HubSpot to fetch all valid enumeration options for the '{property_name}' "
        f"property on '{object_type}'. Return ONLY a JSON array of string values, "
        'e.g. ["val1", "val2"]. No explanation, no markdown.',
        max_tokens=2048,
    )
    return sorted(raw) if isinstance(raw, list) else []


def fetch_qualifying_pool(
    nature: list[str] | None = None,
    tier_company: list[str] | None = None,
    macro_category: list[str] | None = None,
    beginning_date_from: date | None = None,
    beginning_date_to: date | None = None,
    arr_live_min: float | None = None,
    arr_live_max: float | None = None,
) -> tuple[list[Company], int]:
    """
    Traverses Company → active Deal → engaged Contact in one Claude/MCP call.
    Returns (qualifying_companies_with_deals_and_contacts, total_raw_company_count).
    Capped at the first 100 qualifying companies — apply filters to stay within this.
    """
    company_filter_parts = ["arr_live greater than 0"]
    if nature:
        company_filter_parts.append(f"nature IN [{', '.join(nature)}]")
    if tier_company:
        company_filter_parts.append(f"tier_company IN [{', '.join(tier_company)}]")
    if macro_category:
        company_filter_parts.append(f"macro_category IN [{', '.join(macro_category)}]")
    if beginning_date_from:
        company_filter_parts.append(f"beginning_date >= {beginning_date_from.isoformat()}")
    if beginning_date_to:
        company_filter_parts.append(f"beginning_date <= {beginning_date_to.isoformat()}")
    if arr_live_min is not None:
        company_filter_parts.append(f"arr_live >= {arr_live_min}")
    if arr_live_max is not None:
        company_filter_parts.append(f"arr_live <= {arr_live_max}")

    company_filter_desc = " AND ".join(company_filter_parts)

    prompt = f"""Execute this HubSpot pipeline using search_crm_objects. Return ONLY valid JSON at the end.

STEP 1 — Search companies where: {company_filter_desc}
Properties: id, name, nature, tier_company, macro_category, beginning_date, arr_live, country
Take the first 100 results. Record the total count from the response.

STEP 2 — For each company from Step 1:
Search deals where pipeline = "{ACTIVE_DEAL_PIPELINE}" AND associated with this company.
Sort by createdate DESCENDING. Take only the most recent deal.
Skip companies with no deal in that pipeline.

STEP 3 — For each deal from Step 2:
Search contacts associated with this deal where engagement_score_v2 HAS_PROPERTY.
Properties: id, firstname, lastname, email, engagement_score_v2
Take the first contact. Skip deals with no such contact.

STEP 4 — Return ONLY this JSON object (no markdown, no explanation):
{{
  "total_companies": <integer total from Step 1>,
  "entries": [
    {{
      "company": {{"id": "123", "name": "Acme", "nature": "Legal", "tier_company": "Lawyer", "macro_category": "Mass Market", "beginning_date": "2024-01-01", "arr_live": 1200.0, "country": "IT"}},
      "deal": {{"id": "456", "name": "Acme Deal", "created_at": "2024-01-01"}},
      "contact": {{"id": "789", "first_name": "Mario", "last_name": "Rossi", "email": "mario@acme.it", "engagement_score_v2": 5.0}}
    }}
  ]
}}"""

    raw = _call(prompt, max_tokens=16000)
    entries = raw.get("entries", [])
    total = int(raw.get("total_companies", 0))
    companies = [_parse_entry(e) for e in entries if _entry_valid(e)]
    return companies, total


# ── Parsers ───────────────────────────────────────────────────────────────────

def _entry_valid(entry: dict) -> bool:
    return all(k in entry for k in ("company", "deal", "contact"))


def _parse_entry(entry: dict) -> Company:
    c = entry["company"]
    d = entry["deal"]
    ct = entry["contact"]

    contact = Contact(
        id=str(ct.get("id", "")),
        first_name=ct.get("first_name") or ct.get("firstname", ""),
        last_name=ct.get("last_name") or ct.get("lastname", ""),
        email=ct.get("email", ""),
        engagement_score_v2=_to_float(ct.get("engagement_score_v2")),
    )
    deal = Deal(
        id=str(d.get("id", "")),
        name=d.get("name") or d.get("dealname", ""),
        pipeline=ACTIVE_DEAL_PIPELINE,
        created_at=_parse_date(d.get("created_at") or d.get("createdate")) or date.today(),
        contacts=[contact],
    )
    return Company(
        id=str(c.get("id", "")),
        name=c.get("name", ""),
        nature=c.get("nature"),
        tier_company=c.get("tier_company"),
        macro_category=c.get("macro_category"),
        beginning_date=_parse_date(c.get("beginning_date")),
        arr_live=_to_float(c.get("arr_live")) or 0.0,
        country=c.get("country"),
        deals=[deal],
    )


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None
