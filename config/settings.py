import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # optional — required only for AI features
HS_TOKEN = os.getenv("HS_TOKEN", "")   # optional — app uses mock data when empty
INVITE_CODE = os.environ["INVITE_CODE"]

# HubSpot internal IDs
ACTIVE_DEAL_PIPELINE = "593165758"
