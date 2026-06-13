"""
Generates the weekly digest with Claude and saves it to the local SQLite database.
Previously posted to Notion — replaced with in-app storage.
"""
import anthropic
from config.settings import ANTHROPIC_API_KEY
from src.db import store as db

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM = (
    "You are a product manager assistant. Given a set of customer interview summaries "
    "from the past week, identify the most important recurring themes, patterns, and "
    "signals. Be concise and actionable."
)


def generate_weekly_digest(summaries: list[dict]) -> tuple[str, int]:
    """
    Generates the digest text with Claude, saves it to the DB.
    Returns (digest_text, digest_id).
    """
    if not summaries:
        return "No interviews this week.", 0

    combined = "\n\n---\n\n".join(
        f"**{s['company']} — {s['contact']} ({s['date']})**\n{s['summary']}"
        for s in summaries
    )

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=_SYSTEM,
        messages=[{"role": "user", "content": f"""
Here are the executive summaries from {len(summaries)} customer interviews this week:

{combined}

Write a weekly product digest with:
1. **Top 3 recurring pain points across all interviews**
2. **Top 3 feature requests mentioned most often**
3. **Standout positive signals**
4. **Recommended actions for this week**
5. **One-paragraph executive summary** for leadership
"""}],
    )
    digest_text = response.content[0].text.strip()
    date_range = f"{summaries[0]['date']} to {summaries[-1]['date']}"

    db.init_db()
    digest_id = db.save_digest(content=digest_text, date_range=date_range)
    return digest_text, digest_id
