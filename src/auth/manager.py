"""
Auth helpers — login gate + self-registration with domain restriction and invite code.
Credentials are stored in users.yaml (gitignored).
"""
import os
import secrets

import bcrypt
import streamlit as st
import streamlit_authenticator as stauth
import yaml

from config.settings import INVITE_CODE

_YAML_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "users.yaml")
_ALLOWED_DOMAIN = "lexroom.ai"


# ── YAML helpers ───────────────────────────────────────────────────────────────

def _load_config() -> dict:
    if not os.path.exists(_YAML_PATH):
        return {
            "credentials": {"usernames": {}},
            "cookie": {
                "name": "productcrm_auth",
                "key": secrets.token_hex(32),
                "expiry_days": 30,
            },
        }
    with open(_YAML_PATH) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)


def _save_config(config: dict) -> None:
    with open(_YAML_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


# ── Registration ───────────────────────────────────────────────────────────────

def _register_form() -> None:
    st.subheader("Create your account")
    with st.form("register_form"):
        username = st.text_input("Username").strip().lower()
        name = st.text_input("Display name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        password2 = st.text_input("Confirm password", type="password")
        invite_code = st.text_input("Invite code", type="password")
        submitted = st.form_submit_button("Sign up", type="primary")

    if not submitted:
        return

    # Validation
    if not all([username, name, email, password, invite_code]):
        st.error("All fields are required.")
        return
    if not email.lower().endswith(f"@{_ALLOWED_DOMAIN}"):
        st.error(f"Only @{_ALLOWED_DOMAIN} email addresses are allowed.")
        return
    if invite_code != INVITE_CODE:
        st.error("Invalid invite code.")
        return
    if password != password2:
        st.error("Passwords do not match.")
        return
    if len(password) < 8:
        st.error("Password must be at least 8 characters.")
        return

    config = _load_config()
    if username in config["credentials"]["usernames"]:
        st.error("Username already taken.")
        return

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    config["credentials"]["usernames"][username] = {
        "email": email.strip(),
        "name": name.strip(),
        "password": hashed,
    }
    _save_config(config)
    st.success("Account created! Switch to the **Log in** tab to sign in.")


# ── Public API ─────────────────────────────────────────────────────────────────

def login_gate():
    """
    Renders login / register tabs and halts execution if not authenticated.
    Returns (username, display_name, authenticator) for the logged-in user.
    """
    config = _load_config()
    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    if not st.session_state.get("authentication_status"):
        tab_login, tab_register = st.tabs(["Log in", "Sign up"])

        with tab_login:
            authenticator.login()
            if st.session_state.get("authentication_status") is False:
                st.error("Incorrect username or password.")

        with tab_register:
            _register_form()

        st.stop()

    return st.session_state["username"], st.session_state["name"], authenticator
