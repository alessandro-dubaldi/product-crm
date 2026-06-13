"""
Applies an email template to a list of contacts.
Returns one filled-in email dict per contact.
"""
from urllib.parse import quote
from src.hubspot.models import SelectedInterview
from src.templates import store as templates


def build_gmail_url(to: str, subject: str, body: str) -> str:
    return (
        "https://mail.google.com/mail/?view=cm"
        f"&to={quote(to)}"
        f"&su={quote(subject)}"
        f"&body={quote(body)}"
    )


def apply_template_to_interviews(
    interviews: list[SelectedInterview],
    template: dict,
    booking_link: str,
    pm_name: str,
) -> list[dict]:
    """
    Returns one dict per interview:
      {contact_email, first_name, last_name, company, subject, body, gmail_url}
    """
    results = []
    for i in interviews:
        filled = templates.apply(
            template,
            first_name=i.contact.first_name,
            last_name=i.contact.last_name,
            company=i.company.name,
            booking_link=booking_link,
            pm_name=pm_name,
        )
        results.append({
            "contact_email": i.contact.email,
            "first_name": i.contact.first_name,
            "last_name": i.contact.last_name,
            "company": i.company.name,
            "subject": filled["subject"],
            "body": filled["body"],
            "gmail_url": build_gmail_url(i.contact.email, filled["subject"], filled["body"]),
        })
    return results
