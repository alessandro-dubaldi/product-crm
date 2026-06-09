"""
Orchestrates the full HubSpot traversal:
  Company (filtered) → most recent active Deal → engaged Contacts
Returns only companies that have at least one qualifying contact.
"""
import asyncio
from datetime import date

from src.hubspot import client as hs
from src.hubspot.models import Company


async def qualifying_companies(
    nature: list[str] | None = None,
    tier_company: list[str] | None = None,
    macro_category: list[str] | None = None,
    beginning_date_from: date | None = None,
    beginning_date_to: date | None = None,
    arr_live_min: float | None = None,
    arr_live_max: float | None = None,
) -> list[Company]:
    """
    Returns companies (with deals and contacts populated) that pass all
    filters and have at least one engaged contact on an active deal.
    """
    companies = await hs.fetch_active_companies(
        nature=nature,
        tier_company=tier_company,
        macro_category=macro_category,
        beginning_date_from=beginning_date_from,
        beginning_date_to=beginning_date_to,
        arr_live_min=arr_live_min,
        arr_live_max=arr_live_max,
    )

    enriched = await asyncio.gather(*[_enrich(c) for c in companies])
    return [c for c in enriched if c is not None]


async def _enrich(company: Company) -> Company | None:
    """
    Adds deals (most recent active only) and contacts to the company.
    Returns None if no qualifying contact exists.
    """
    deals = await hs.fetch_deals_for_company(company.id)
    if not deals:
        return None

    most_recent = deals[0]
    contacts = await hs.fetch_contacts_for_deal(most_recent.id)
    if not contacts:
        return None

    most_recent.contacts = contacts
    company.deals = [most_recent]
    return company
