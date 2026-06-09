import requests
from config.settings import NOTION_TOKEN, NOTION_DIGEST_PAGE_ID

_BASE = "https://api.notion.com/v1"
_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def create_interview_page(
    company_name: str,
    contact_name: str,
    interview_date: str,
    transcript: str,
    exec_summary: str,
) -> str:
    blocks = [
        _heading(f"Interview with {contact_name} · {company_name} · {interview_date}", 1),
        _heading("Executive Summary", 2),
        *_paragraphs(exec_summary),
        {"object": "block", "type": "divider", "divider": {}},
        _heading("Full Transcript", 2),
        *_paragraphs(transcript),
    ]

    body = {
        "parent": {"page_id": NOTION_DIGEST_PAGE_ID},
        "properties": {
            "title": {"title": [{"type": "text", "text": {
                "content": f"Interview — {company_name} ({interview_date})"
            }}]}
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


def _heading(text: str, level: int) -> dict:
    key = f"heading_{level}"
    return {"object": "block", "type": key, key: {
        "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
    }}


def _paragraphs(text: str) -> list[dict]:
    return [
        {"object": "block", "type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": chunk}}]
        }}
        for chunk in [text[i:i + 2000] for i in range(0, max(len(text), 1), 2000)]
    ]
