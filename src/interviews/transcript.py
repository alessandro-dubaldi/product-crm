"""
Fetches call transcripts from Granola via MCP.
"""
import anthropic
from config.settings import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def fetch_latest_transcript(meeting_title_hint: str = "") -> str | None:
    """
    Fetches the most recent Granola transcript.
    Optionally pass a meeting title hint to narrow down which meeting to fetch.
    Returns the transcript text, or None if not found.
    """
    query = "Fetch the most recent meeting transcript from Granola."
    if meeting_title_hint:
        query += f" The meeting title contains: '{meeting_title_hint}'."
    query += " Return only the transcript text, nothing else."

    response = _client.beta.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        betas=["mcp-client-2025-04-04"],
        mcp_servers=[{
            "type": "url",
            "url": "https://mcp.claude.ai/granola",
            "name": "granola",
        }],
        messages=[{"role": "user", "content": query}],
    )

    text = response.content[0].text.strip()
    return text if text else None
