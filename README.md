# ProductCRM

> Systematic, data-driven product interview orchestration — from HubSpot to structured insights.

## Problem

Product teams lack a reliable, repeatable way to run customer interviews. Contact selection is ad-hoc, outreach is manual, and unstructured notes make interview data noisy and unusable.

## Solution

ProductCRM automates the full interview pipeline: filter real customers from HubSpot, randomly sample a cohort, generate personalized outreach emails, schedule calls, capture transcripts, and synthesize insights into a weekly Notion digest.

## Pipeline

```
HubSpot (MCP)
  └─ Filter companies: arr_live ≠ 0, nature, tier_company, macro_category,
                       beginning_date range, arr_live range
       └─ Traverse deals: pipeline = 593165758 (most recent per company)
            └─ Traverse contacts: engagement_score_v2 non-empty
                 └─ Qualify company if ≥ 1 contact passes

Random sample N companies from qualifying pool
  └─ Per company → most recent active deal → random engaged contact

Generate personalized email per contact (Claude)
  └─ Send via Gmail MCP (includes PM's Calendly link)

Customer books via Calendly → syncs to PM's Google Calendar

Call happens → Granola records transcript
  └─ Claude generates exec summary
       └─ Notion page created per interview

Weekly: Claude aggregates all interviews → trends + key insights
  └─ Notion weekly digest page
```

## HubSpot Data Model

```
Company  (arr_live ≠ 0 = active client)
  └── Deal(s)  [filter: pipeline = 593165758]
        └── Contact(s)  [filter: engagement_score_v2 non-empty]
```

Contacts are not directly linked to companies — traversal is always **Company → Deal → Contact**.

## Filters

| Object | Property | Type | Notes |
|---|---|---|---|
| Company | `nature` | discrete | |
| Company | `tier_company` | discrete | |
| Company | `macro_category` | discrete | |
| Company | `beginning_date` | date range | |
| Company | `arr_live` | numeric range | also used as activity gate (≠ 0) |
| Deal | `pipeline` | fixed | = `593165758` (active deals only) |
| Contact | `engagement_score_v2` | gate | non-empty required for selection |

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/alessandro-dubaldi/product-crm.git
cd product-crm
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in all values in .env
```

### 3. Run the app

```bash
streamlit run app.py
```

The PM opens `http://localhost:8501` in their browser — no code needed to operate.

## Environment Variables

See `.env.example` for the full list. Required:

- `ANTHROPIC_API_KEY` — Claude API key
- `HUBSPOT_ACCESS_TOKEN` — HubSpot private app token
- `NOTION_TOKEN` — Notion integration token
- `NOTION_DIGEST_PAGE_ID` — Parent Notion page for weekly digests
- `PM_CALENDLY_LINK` — PM's Calendly scheduling link

## Team

Built at hackathon by Alessandro Dubaldi and colleagues.

## Roadmap

See [ROADMAP.md](ROADMAP.md).
