import requests
import anthropic
from config.settings import ANTHROPIC_API_KEY, NOTION_TOKEN, NOTION_DIGEST_PAGE_ID
from src.notion.interview_page import _heading, _paragraphs

_BASE = "https://api.notion.com/v1"
_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM = (
    "You are a product manager assistant. Given a set of customer interview summaries "
    "from the past week, identify the most important recurring themes, patterns, and "
    "signals. Be concise and actionable."
)


def generate_weekly_digest(summaries: list[dict]) -> str:
    if not summaries:
        return "No interviews this week."

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

    title = f"Weekly Product Interview Digest — {summaries[0]['date']} to {summaries[-1]['date']}"
    blocks = [
        _heading(title, 1),
        *_paragraphs(digest_text),
        {"object": "block", "type": "divider", "divider": {}},
        _heading("Interviews included", 2),
        *[{"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": f"{s['company']} — {s['contact']} ({s['date']})"}}]
        }} for s in summaries],
    ]

    body = {
        "parent": {"page_id": NOTION_DIGEST_PAGE_ID},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        },
        "children": blocks[:100],
    }
    r = requests.post(f"{_BASE}/pages", headers=_HEADERS, json=body, timeout=30)
    r.raise_for_status()
    page_id = r.json()["id"]

    for i in range(100, len(blocks), 100):
        requests.patch(
            f"{_BASE}/blocks/{page_id}/children",
            headers=_HEADERS,
            json={"children": blocks[i:i + 100]},
            timeout=30,
        ).raise_for_status()

    return f"https://notion.so/{page_id.replace('-', '')}"
