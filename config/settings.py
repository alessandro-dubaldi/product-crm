import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
HUBSPOT_ACCESS_TOKEN = os.environ["HUBSPOT_ACCESS_TOKEN"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DIGEST_PAGE_ID = os.environ["NOTION_DIGEST_PAGE_ID"]
PM_BOOKING_LINK = os.environ["PM_BOOKING_LINK"]
PM_NAME = os.getenv("PM_NAME", "")
PM_EMAIL = os.getenv("PM_EMAIL", "")

# HubSpot internal IDs
ACTIVE_DEAL_PIPELINE = "593165758"
