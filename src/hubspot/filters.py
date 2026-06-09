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
    return hs.fetch_qualifying_pool(
        nature=nature,
        tier_company=tier_company,
        macro_category=macro_category,
        beginning_date_from=beginning_date_from,
        beginning_date_to=beginning_date_to,
        arr_live_min=arr_live_min,
        arr_live_max=arr_live_max,
    )
