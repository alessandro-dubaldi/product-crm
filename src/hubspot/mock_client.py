"""
Mock HubSpot client — returns realistic fake data when HS_TOKEN is not set.
Swap out by setting HS_TOKEN in .env.
"""
from datetime import date
from src.hubspot.models import Company, Contact, Deal

_COMPANIES = [
    Company(id="1", name="Acme Corp", nature="B2B", tier_company="Tier 1", macro_category="SaaS", beginning_date=date(2022, 3, 1), arr_live=120000, country="Italy"),
    Company(id="2", name="Bright Solutions", nature="B2B", tier_company="Tier 2", macro_category="FinTech", beginning_date=date(2023, 1, 15), arr_live=48000, country="France"),
    Company(id="3", name="CloudNine", nature="B2B", tier_company="Tier 1", macro_category="SaaS", beginning_date=date(2021, 9, 10), arr_live=240000, country="Germany"),
    Company(id="4", name="DeltaWave", nature="B2C", tier_company="Tier 3", macro_category="E-commerce", beginning_date=date(2023, 6, 1), arr_live=18000, country="Spain"),
    Company(id="5", name="EchoBase", nature="B2B", tier_company="Tier 2", macro_category="LegalTech", beginning_date=date(2022, 11, 20), arr_live=72000, country="Italy"),
    Company(id="6", name="FrontierAI", nature="B2B", tier_company="Tier 1", macro_category="SaaS", beginning_date=date(2020, 5, 5), arr_live=390000, country="UK"),
    Company(id="7", name="GreenPath", nature="B2C", tier_company="Tier 3", macro_category="ClimateTech", beginning_date=date(2023, 2, 28), arr_live=9600, country="Netherlands"),
    Company(id="8", name="HorizonPay", nature="B2B", tier_company="Tier 2", macro_category="FinTech", beginning_date=date(2022, 7, 14), arr_live=55000, country="France"),
    Company(id="9", name="Innova Labs", nature="B2B", tier_company="Tier 1", macro_category="HealthTech", beginning_date=date(2021, 4, 1), arr_live=180000, country="Italy"),
    Company(id="10", name="JetStream", nature="B2B", tier_company="Tier 2", macro_category="LogisticsTech", beginning_date=date(2022, 12, 1), arr_live=66000, country="Germany"),
]

_CONTACTS = {
    "1": Contact(id="101", first_name="Giulia", last_name="Rossi", email="giulia.rossi@acme.com", engagement_score_v2=87.0),
    "2": Contact(id="102", first_name="Pierre", last_name="Dubois", email="pierre.dubois@brightsolutions.fr", engagement_score_v2=62.0),
    "3": Contact(id="103", first_name="Hans", last_name="Müller", email="hans.mueller@cloudnine.de", engagement_score_v2=91.0),
    "4": Contact(id="104", first_name="María", last_name="García", email="maria.garcia@deltawave.es", engagement_score_v2=45.0),
    "5": Contact(id="105", first_name="Luca", last_name="Ferrari", email="luca.ferrari@echobase.it", engagement_score_v2=78.0),
    "6": Contact(id="106", first_name="James", last_name="Smith", email="james.smith@frontierai.co.uk", engagement_score_v2=95.0),
    "7": Contact(id="107", first_name="Emma", last_name="de Vries", email="emma.devries@greenpath.nl", engagement_score_v2=53.0),
    "8": Contact(id="108", first_name="Sophie", last_name="Martin", email="sophie.martin@horizonpay.fr", engagement_score_v2=70.0),
    "9": Contact(id="109", first_name="Marco", last_name="Bianchi", email="marco.bianchi@innovalabs.it", engagement_score_v2=83.0),
    "10": Contact(id="110", first_name="Klaus", last_name="Weber", email="klaus.weber@jetstream.de", engagement_score_v2=67.0),
}

_DEALS = {
    cid: Deal(id=f"2{cid}", name=f"Deal — {_COMPANIES[int(cid)-1].name}", pipeline="593165758", created_at=date(2023, 1, 1))
    for cid in _CONTACTS
}


def fetch_active_companies(**kwargs) -> tuple[list[Company], int]:
    return _COMPANIES, len(_COMPANIES)


def fetch_deals_for_company(company_id: str) -> list[Deal]:
    return [_DEALS[company_id]] if company_id in _DEALS else []


def fetch_contacts_for_deal(deal_id: str) -> list[Contact]:
    cid = deal_id[1:]  # strip leading "2"
    return [_CONTACTS[cid]] if cid in _CONTACTS else []


def fetch_property_options(object_type: str, property_name: str) -> list[str]:
    options = {
        "nature": ["B2B", "B2C"],
        "tier_company": ["Tier 1", "Tier 2", "Tier 3"],
        "macro_category": ["SaaS", "FinTech", "LegalTech", "HealthTech", "E-commerce", "LogisticsTech", "ClimateTech"],
    }
    return options.get(property_name, [])
