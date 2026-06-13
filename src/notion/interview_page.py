"""
Saves interview data to the local SQLite database.
Previously posted to Notion — replaced with in-app storage.
"""
from src.db import store as db


def create_interview_page(
    company_name: str,
    contact_name: str,
    interview_date: str,
    transcript: str,
    exec_summary: str,
) -> int:
    """Saves the interview and returns its database ID."""
    db.init_db()
    return db.save_interview(
        company=company_name,
        contact=contact_name,
        date=interview_date,
        transcript=transcript,
        exec_summary=exec_summary,
    )
