from datetime import date

from src.hubspot.filters import qualifying_companies
from src.hubspot.models import SelectedInterview
from src.selection.sampler import sample


def run_selection(
    n: int,
    nature: list[str] | None = None,
    tier_company: list[str] | None = None,
    macro_category: list[str] | None = None,
    beginning_date_from: date | None = None,
    beginning_date_to: date | None = None,
    arr_live_min: float | None = None,
    arr_live_max: float | None = None,
) -> tuple[list[SelectedInterview], int]:
    pool, pool_size = qualifying_companies(
        nature=nature,
        tier_company=tier_company,
        macro_category=macro_category,
        beginning_date_from=beginning_date_from,
        beginning_date_to=beginning_date_to,
        arr_live_min=arr_live_min,
        arr_live_max=arr_live_max,
    )
    sampled = sample(pool, min(n, len(pool)))
    interviews = [
        SelectedInterview(company=c, deal=c.deals[0], contact=c.deals[0].contacts[0])
        for c in sampled
    ]
    return interviews, pool_size
