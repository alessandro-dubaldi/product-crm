"""
Creates a Notion page per interview containing the transcript and exec summary.
"""
import anthropic
from config.settings import ANTHROPIC_API_KEY, NOTION_TOKEN, NOTION_DIGEST_PAGE_ID

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def create_interview_page(
    company_name: str,
    contact_name: str,
    interview_date: str,
    transcript: str,
    exec_summary: str,
) -> str:
    """
    Creates a Notion page under NOTION_DIGEST_PAGE_ID.
    Returns the URL of the created page.
    """
    prompt = f"""
Create a Notion page with the following content. Use the Notion MCP tool.

Parent page ID: {NOTION_DIGEST_PAGE_ID}
Page title: "Interview — {company_name} ({interview_date})"

Page content (in order):
1. A header: "Interview with {contact_name} · {company_name} · {interview_date}"
2. A section titled "Executive Summary" with this content:
{exec_summary}

3. A divider

4. A section titled "Full Transcript" with this content:
{transcript}

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
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
