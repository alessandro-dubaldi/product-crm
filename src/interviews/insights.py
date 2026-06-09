"""
Generates an executive summary from a call transcript using Claude.
"""
import anthropic
from config.settings import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM = (
    "You are a product manager assistant. Given a customer interview transcript, "
    "extract a concise executive summary. Be factual and specific — no fluff."
)


def generate_exec_summary(transcript: str, company_name: str, contact_name: str) -> str:
    """Returns a structured exec summary from the interview transcript."""
    prompt = f"""
Interview with {contact_name} from {company_name}.

Transcript:
{transcript}

Write an executive summary with these sections:
1. **Key pain points** (bullet list, max 5)
2. **Feature requests / wishes** (bullet list, max 5)
3. **Positive feedback** (bullet list, max 3)
4. **Action items for product team** (bullet list, max 3)
5. **One-sentence overall impression**
"""

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
