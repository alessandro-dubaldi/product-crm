"""
End-to-end selection pipeline.
Calls the HubSpot traversal, then samples N companies.
"""
from datetime import date

from src.hubspot.filters import qualifying_companies
from src.hubspot.models import SelectedInterview
from src.selection.sampler import sample
from src.hubspot import client as hs


async def run_selection(
    n: int,
    nature: list[str] | None = None,
    tier_company: list[str] | None = None,
    macro_category: list[str] | None = None,
    beginning_date_from: date | None = None,
    beginning_date_to: date | None = None,
    arr_live_min: float | None = None,
    arr_live_max: float | None = None,
) -> tuple[list[SelectedInterview], int]:
    """
    Returns (selected_interviews, total_qualifying_pool_size).
    Each SelectedInterview has one company, one deal, and one contact.
    """
    pool = await qualifying_companies(
        nature=nature,
        tier_company=tier_company,
        macro_category=macro_category,
        beginning_date_from=beginning_date_from,
        beginning_date_to=beginning_date_to,
        arr_live_min=arr_live_min,
        arr_live_max=arr_live_max,
    )

    pool_size = len(pool)
    sampled = sample(pool, min(n, pool_size))

    interviews = []
    for company in sampled:
        deal = company.deals[0]
        contact = sample(deal.contacts, 1)[0]
        interviews.append(SelectedInterview(company=company, deal=deal, contact=contact))

    return interviews, pool_size
