"""
Generates outreach emails for each selected interview.
Emails are returned for PM review — Gmail draft creation requires Gmail MCP auth (v2).
"""
from src.hubspot.models import SelectedInterview
from src.outreach.email_gen import generate_email


def send_drafts(interviews: list[SelectedInterview]) -> list[dict]:
    """Generates emails for all interviews. Returns list of {contact_email, subject, body}."""
    return [
        {
            "contact_email": i.contact.email,
            "subject": email["subject"],
            "body": email["body"],
        }
        for i in interviews
        for email in [generate_email(i)]
    ]
