"""
Generates a personalized outreach email for each selected interview using Claude.
"""
import anthropic

from src.hubspot.models import SelectedInterview
from config.settings import ANTHROPIC_API_KEY, PM_CALENDLY_LINK, PM_NAME

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM = (
    "You are a product manager writing a short, warm, and direct email to a customer "
    "inviting them to a 30-minute product interview. The tone should be personal and "
    "human — not corporate or salesy. Never mention NPS scores or internal metrics."
)


def generate_email(interview: SelectedInterview) -> dict[str, str]:
    """
    Returns {"subject": ..., "body": ...} for the given interview contact.
    """
    contact = interview.contact
    company = interview.company

    prompt = f"""
Write a short outreach email inviting {contact.first_name} {contact.last_name}
from {company.name} to a 30-minute product interview.

Context about the customer:
- Company: {company.name}
- Tier: {company.tier_company or "N/A"}
- Category: {company.macro_category or "N/A"}

The email should:
1. Be addressed to {contact.first_name} personally
2. Briefly explain the purpose (understand how they use the product, improve it)
3. Include this scheduling link: {PM_CALENDLY_LINK}
4. Be signed by {PM_NAME or "the Product Team"}
5. Be under 150 words

Return the email in this exact format:
SUBJECT: <subject line>
BODY:
<email body>
"""

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    subject_line, _, body = text.partition("\nBODY:\n")
    subject = subject_line.replace("SUBJECT:", "").strip()
    return {"subject": subject, "body": body.strip()}
