"""
Per-user profile storage — persisted as JSON in data/profiles/{username}.json.
Profile schema:
  {
    "name": str,
    "email": str,
    "booking_links": [{"label": str, "url": str}, ...]
  }
"""
import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "profiles")


def _path(username: str) -> str:
    os.makedirs(_DATA_DIR, exist_ok=True)
    return os.path.join(_DATA_DIR, f"{username}.json")


def load(username: str) -> dict:
    p = _path(username)
    if not os.path.exists(p):
        return {"name": "", "email": "", "booking_links": []}
    with open(p) as f:
        return json.load(f)


def save(username: str, profile: dict) -> None:
    with open(_path(username), "w") as f:
        json.dump(profile, f, indent=2)
