"""
Generates the weekly Notion digest by aggregating all interview exec summaries
from the past 7 days and synthesising trends via Claude.
"""
import anthropic
from config.settings import ANTHROPIC_API_KEY, NOTION_TOKEN, NOTION_DIGEST_PAGE_ID

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM = (
    "You are a product manager assistant. Given a set of customer interview summaries "
    "from the past week, identify the most important recurring themes, patterns, and "
    "signals. Be concise and actionable."
)


def generate_weekly_digest(summaries: list[dict]) -> str:
    """
    summaries: list of {"company": str, "contact": str, "date": str, "summary": str}
    Creates a Notion page with the weekly digest and returns its URL.
    """
    if not summaries:
        return "No interviews this week."

    combined = "\n\n---\n\n".join(
        f"**{s['company']} — {s['contact']} ({s['date']})**\n{s['summary']}"
        for s in summaries
    )

    synthesis_prompt = f"""
Here are the executive summaries from {len(summaries)} customer interviews this week:

{combined}

Write a weekly product digest with:
1. **Top 3 recurring pain points across all interviews**
2. **Top 3 feature requests mentioned most often**
3. **Standout positive signals**
4. **Recommended actions for this week**
5. **One-paragraph executive summary** for leadership
"""

    synthesis = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=_SYSTEM,
        messages=[{"role": "user", "content": synthesis_prompt}],
    )
    digest_text = synthesis.content[0].text.strip()

    notion_prompt = f"""
Create a Notion page using the Notion MCP tool.

Parent page ID: {NOTION_DIGEST_PAGE_ID}
Page title: "Weekly Product Interview Digest — {summaries[0]['date']} to {summaries[-1]['date']}"

Page content:
{digest_text}

---
Based on {len(summaries)} interviews with: {", ".join(s['company'] for s in summaries)}

After creating the page, return only the page URL.
"""

    response = _client.beta.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        betas=["mcp-client-2025-04-04"],
        mcp_servers=[{
            "type": "url",
            "url": "https://mcp.claude.ai/notion",
            "name": "notion",
            "authorization_token": NOTION_TOKEN,
        }],
        messages=[{"role": "user", "content": notion_prompt}],
    )

    return response.content[0].text.strip()
