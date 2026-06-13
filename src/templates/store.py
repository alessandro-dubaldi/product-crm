"""
Per-user email template storage — persisted as JSON in data/templates/{username}.json.

Template schema:
  {"id": int, "name": str, "subject": str, "body": str}

Supported variables (replaced at send time):
  {{first_name}}, {{last_name}}, {{company}}, {{booking_link}}, {{pm_name}}
"""
import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "templates")

VARIABLES = [
    ("{{first_name}}", "Contact's first name"),
    ("{{last_name}}", "Contact's last name"),
    ("{{company}}", "Company name"),
    ("{{booking_link}}", "Selected booking link URL"),
    ("{{pm_name}}", "Your display name from Profile"),
]

_DEFAULT_TEMPLATES = [
    {
        "id": 1,
        "name": "30-min product interview invite",
        "subject": "Quick chat about your experience, {{first_name}}?",
        "body": (
            "Hi {{first_name}},\n\n"
            "I'm reaching out because we'd love to learn more about how {{company}} uses our product — "
            "your feedback directly shapes what we build next.\n\n"
            "Would you be open to a quick 30-minute call? You can grab a slot that works for you here:\n"
            "{{booking_link}}\n\n"
            "Thanks so much,\n{{pm_name}}"
        ),
    },
]


def _path(username: str) -> str:
    os.makedirs(_DATA_DIR, exist_ok=True)
    return os.path.join(_DATA_DIR, f"{username}.json")


def list_templates(username: str) -> list[dict]:
    p = _path(username)
    if not os.path.exists(p):
        return list(_DEFAULT_TEMPLATES)
    with open(p) as f:
        return json.load(f)


def save_template(username: str, template: dict) -> dict:
    """Insert or update a template. Assigns an ID if new."""
    templates = list_templates(username)
    if template.get("id"):
        templates = [t if t["id"] != template["id"] else template for t in templates]
    else:
        next_id = max((t["id"] for t in templates), default=0) + 1
        template = {**template, "id": next_id}
        templates.append(template)
    _write(username, templates)
    return template


def delete_template(username: str, template_id: int) -> None:
    templates = [t for t in list_templates(username) if t["id"] != template_id]
    _write(username, templates)


def apply(template: dict, *, first_name: str, last_name: str, company: str,
          booking_link: str, pm_name: str) -> dict:
    """Returns {subject, body} with all variables replaced."""
    replacements = {
        "{{first_name}}": first_name,
        "{{last_name}}": last_name,
        "{{company}}": company,
        "{{booking_link}}": booking_link,
        "{{pm_name}}": pm_name,
    }
    def fill(text: str) -> str:
        for var, val in replacements.items():
            text = text.replace(var, val)
        return text
    return {"subject": fill(template["subject"]), "body": fill(template["body"])}


def _write(username: str, templates: list[dict]) -> None:
    with open(_path(username), "w") as f:
        json.dump(templates, f, indent=2)
