from datetime import date

from src.hubspot import client as hs
from src.hubspot.models import Company


def qualifying_companies(
    nature: list[str] | None = None,
    tier_company: list[str] | None = None,
    macro_category: list[str] | None = None,
    beginning_date_from: date | None = None,
    beginning_date_to: date | None = None,
    arr_live_min: float | None = None,
    arr_live_max: float | None = None,
) -> tuple[list[Company], int]:
    companies, total = hs.fetch_active_companies(
        nature=nature,
        tier_company=tier_company,
        macro_category=macro_category,
        beginning_date_from=beginning_date_from,
        beginning_date_to=beginning_date_to,
        arr_live_min=arr_live_min,
        arr_live_max=arr_live_max,
    )
    return [c for c in (_enrich(c) for c in companies) if c is not None], total


def _enrich(company: Company) -> Company | None:
    deals = hs.fetch_deals_for_company(company.id)
    if not deals:
        return None
    most_recent = deals[0]
    contacts = hs.fetch_contacts_for_deal(most_recent.id)
    if not contacts:
        return None
    most_recent.contacts = contacts
    company.deals = [most_recent]
    return company
