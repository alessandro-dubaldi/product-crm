"""
Sends outreach emails via Gmail MCP.
Each email is sent as a draft first; the PM can review and confirm before sending.
"""
import anthropic

from src.hubspot.models import SelectedInterview
from src.outreach.email_gen import generate_email
from config.settings import ANTHROPIC_API_KEY, PM_EMAIL, PM_NAME

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def create_draft(interview: SelectedInterview) -> dict:
    """
    Generates the email and creates a Gmail draft via MCP.
    Returns the draft details including Gmail draft ID.
    """
    email = generate_email(interview)
    contact = interview.contact

    response = _client.beta.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        betas=["mcp-client-2025-04-04"],
        mcp_servers=[{
            "type": "url",
            "url": "https://mcp.claude.ai/gmail",
            "name": "gmail",
        }],
        messages=[{
            "role": "user",
            "content": (
                f"Create a Gmail draft with the following details:\n"
                f"To: {contact.email}\n"
                f"Subject: {email['subject']}\n"
                f"Body:\n{email['body']}\n\n"
                f"Return only the draft ID."
            ),
        }],
    )

    return {
        "contact_email": contact.email,
        "subject": email["subject"],
        "body": email["body"],
        "draft_response": response.content[0].text,
    }


def send_drafts(interviews: list[SelectedInterview]) -> list[dict]:
    """Creates Gmail drafts for all interviews. Returns draft details."""
    return [create_draft(i) for i in interviews]
