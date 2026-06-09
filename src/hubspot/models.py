from pydantic import BaseModel
from typing import Optional
from datetime import date


class Contact(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    engagement_score_v2: Optional[float] = None
    nps: Optional[float] = None


class Deal(BaseModel):
    id: str
    name: str
    pipeline: str
    created_at: date
    contacts: list[Contact] = []


class Company(BaseModel):
    id: str
    name: str
    nature: Optional[str] = None
    tier_company: Optional[str] = None
    macro_category: Optional[str] = None
    beginning_date: Optional[date] = None
    arr_live: float = 0.0
    country: Optional[str] = None
    deals: list[Deal] = []


class SelectedInterview(BaseModel):
    """One row in the final sample: company + deal + contact."""
    company: Company
    deal: Deal
    contact: Contact
