"""
ProductCRM — PM-facing Streamlit UI.
Run with: streamlit run app.py
"""
from datetime import date

import pandas as pd
import streamlit as st

from src.auth.manager import login_gate
from src.profile import store as profile_store
from src.templates import store as tpl_store
from src.hubspot import client as hs
from src.selection.pipeline import run_selection
from src.outreach.sender import apply_template_to_interviews
from src.db import store as db
from config.settings import HS_TOKEN

st.set_page_config(page_title="ProductCRM", layout="wide")

# ── Auth ───────────────────────────────────────────────────────────────────────

username, display_name, authenticator = login_gate()
db.init_db()

st.title("ProductCRM")
st.caption("Product interview orchestration — from HubSpot to insights.")

with st.sidebar:
    st.write(f"Logged in as **{display_name}**")
    authenticator.logout("Log out", "sidebar")

# ── Shared session state ───────────────────────────────────────────────────────

if "interviews" not in st.session_state:
    st.session_state.interviews = []
if "pool_size" not in st.session_state:
    st.session_state.pool_size = 0

# ── Tabs ───────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab_tpl, tab_profile = st.tabs([
    "1 · Filter & Sample",
    "2 · Outreach",
    "3 · Capture Insights",
    "4 · Weekly Digest",
    "Templates",
    "Profile",
])


# ── Tab 1: Filter & Sample ─────────────────────────────────────────────────────

with tab1:
    st.subheader("Filter companies")

    if not HS_TOKEN:
        st.info("Running with mock HubSpot data. Set `HS_TOKEN` in `.env` to connect to your real CRM.")

    @st.cache_data(ttl=3600)
    def load_filter_options():
        return (
            hs.fetch_property_options("companies", "nature"),
            hs.fetch_property_options("companies", "tier_company"),
            hs.fetch_property_options("companies", "macro_category"),
        )

    with st.spinner("Loading filter options..."):
        try:
            nature_options, tier_options, category_options = load_filter_options()
        except Exception as e:
            st.error(f"Could not load filter options: {e}")
            nature_options, tier_options, category_options = [], [], []

    col1, col2, col3 = st.columns(3)
    with col1:
        nature = st.multiselect("Nature", options=nature_options, default=[])
    with col2:
        tier = st.multiselect("Tier", options=tier_options, default=[])
    with col3:
        category = st.multiselect("Macro category", options=category_options, default=[])

    col4, col5 = st.columns(2)
    with col4:
        date_from = st.date_input("Onboarding date — from", value=None)
        arr_min = st.number_input("ARR min (€)", min_value=0, value=0, step=1000)
    with col5:
        date_to = st.date_input("Onboarding date — to", value=None)
        arr_max = st.number_input("ARR max (€)", min_value=0, value=0, step=1000,
                                  help="Set to 0 to apply no upper limit")

    n = st.number_input("Number of interviews to sample (N)", min_value=1, max_value=200, value=25)

    if st.button("Find qualifying companies & sample", type="primary"):
        with st.spinner("Querying companies..."):
            try:
                interviews, pool_size = run_selection(
                    n=int(n),
                    nature=nature or None,
                    tier_company=tier or None,
                    macro_category=category or None,
                    beginning_date_from=date_from if date_from else None,
                    beginning_date_to=date_to if date_to else None,
                    arr_live_min=arr_min if arr_min > 0 else None,
                    arr_live_max=arr_max if arr_max > 0 else None,
                )
                st.session_state.interviews = interviews
                st.session_state.pool_size = pool_size
            except Exception as e:
                st.error(f"Selection failed: {e}")

    if st.session_state.interviews:
        st.success(
            f"Qualifying pool: **{st.session_state.pool_size}** companies · "
            f"Sampled: **{len(st.session_state.interviews)}**"
        )
        rows = [
            {
                "Company": i.company.name,
                "Country": i.company.country or "—",
                "Tier": i.company.tier_company or "—",
                "ARR (€)": f"{i.company.arr_live:,.0f}",
                "Contact": f"{i.contact.first_name} {i.contact.last_name}",
                "Email": i.contact.email,
                "Engagement score": i.contact.engagement_score_v2,
            }
            for i in st.session_state.interviews
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ── Tab 2: Outreach ────────────────────────────────────────────────────────────

with tab2:
    st.subheader("Send outreach emails")

    if not st.session_state.interviews:
        st.info("Run the filter & sample step first.")
    else:
        profile = profile_store.load(username)
        booking_links = profile.get("booking_links", [])
        pm_name = profile.get("name") or display_name
        templates = tpl_store.list_templates(username)

        # ── Booking link selector ──
        if not booking_links:
            st.warning("No booking links saved. Add one in the **Profile** tab first.")
            st.stop()

        link_labels = [lnk["label"] for lnk in booking_links]
        selected_label = st.selectbox("Booking link", options=link_labels)
        selected_url = next(lnk["url"] for lnk in booking_links if lnk["label"] == selected_label)
        st.caption(selected_url)

        st.divider()

        # ── Template selector ──
        if not templates:
            st.warning("No email templates yet. Create one in the **Templates** tab first.")
            st.stop()

        tpl_names = [t["name"] for t in templates]
        selected_tpl_name = st.selectbox("Email template", options=tpl_names)
        selected_tpl = next(t for t in templates if t["name"] == selected_tpl_name)

        st.divider()

        # ── Editable template ──
        st.subheader("Edit template")
        st.caption(
            "Variables — replaced automatically per contact: "
            + "  ".join(f"`{v}`" for v, _ in tpl_store.VARIABLES)
        )

        edited_subject = st.text_input("Subject", value=selected_tpl["subject"])
        edited_body = st.text_area("Body", value=selected_tpl["body"], height=220)

        edited_tpl = {"subject": edited_subject, "body": edited_body}

        st.divider()

        # ── Preview for first contact ──
        first = st.session_state.interviews[0]
        preview = tpl_store.apply(
            edited_tpl,
            first_name=first.contact.first_name,
            last_name=first.contact.last_name,
            company=first.company.name,
            booking_link=selected_url,
            pm_name=pm_name,
        )
        with st.expander(f"Preview — {first.contact.first_name} {first.contact.last_name} ({first.company.name})", expanded=True):
            st.markdown(f"**Subject:** {preview['subject']}")
            st.text(preview["body"])

        st.divider()

        # ── Contacts table with per-row Gmail links ──
        st.subheader(f"Send to {len(st.session_state.interviews)} contacts")
        filled = apply_template_to_interviews(
            st.session_state.interviews,
            template=edited_tpl,
            booking_link=selected_url,
            pm_name=pm_name,
        )
        for row in filled:
            col_a, col_b, col_c = st.columns([3, 4, 2])
            with col_a:
                st.write(f"**{row['first_name']} {row['last_name']}**")
                st.caption(row["company"])
            with col_b:
                st.caption(row["contact_email"])
            with col_c:
                st.link_button("Open in Gmail ↗", url=row["gmail_url"])


# ── Tab 3: Capture Insights — Coming soon ─────────────────────────────────────

with tab3:
    st.subheader("Capture interview insights")
    st.info("Coming soon — this feature requires an Anthropic API key.")


# ── Tab 4: Weekly Digest — Coming soon ────────────────────────────────────────

with tab4:
    st.subheader("Weekly digest")
    st.info("Coming soon — this feature requires an Anthropic API key.")


# ── Templates tab ──────────────────────────────────────────────────────────────

with tab_tpl:
    st.subheader("Email templates")
    st.caption(
        "Available variables: "
        + ", ".join(f"`{v}` ({desc})" for v, desc in tpl_store.VARIABLES)
    )

    user_templates = tpl_store.list_templates(username)

    # ── Existing templates ──
    for tpl in user_templates:
        with st.expander(tpl["name"]):
            with st.form(f"edit_tpl_{tpl['id']}"):
                new_name = st.text_input("Name", value=tpl["name"])
                new_subj = st.text_input("Subject", value=tpl["subject"])
                new_body = st.text_area("Body", value=tpl["body"], height=200)
                col_save, col_del = st.columns([1, 1])
                with col_save:
                    if st.form_submit_button("Save changes"):
                        tpl_store.save_template(username, {
                            "id": tpl["id"], "name": new_name,
                            "subject": new_subj, "body": new_body,
                        })
                        st.success("Saved.")
                        st.rerun()
                with col_del:
                    if st.form_submit_button("Delete", type="secondary"):
                        tpl_store.delete_template(username, tpl["id"])
                        st.rerun()

    st.divider()

    # ── New template ──
    st.subheader("New template")
    with st.form("new_tpl_form"):
        new_name = st.text_input("Name")
        new_subj = st.text_input("Subject")
        new_body = st.text_area("Body", height=200)
        if st.form_submit_button("Create template", type="primary"):
            if new_name.strip() and new_subj.strip() and new_body.strip():
                tpl_store.save_template(username, {
                    "name": new_name.strip(),
                    "subject": new_subj.strip(),
                    "body": new_body.strip(),
                })
                st.success(f'Template "{new_name}" created.')
                st.rerun()
            else:
                st.warning("All fields are required.")


# ── Profile tab ────────────────────────────────────────────────────────────────

with tab_profile:
    st.subheader("Your profile")
    profile = profile_store.load(username)

    with st.form("profile_form"):
        name_val = st.text_input("Display name", value=profile.get("name", ""))
        email_val = st.text_input("Email", value=profile.get("email", ""))
        st.caption("Used as the sender signature in outreach emails (`{{pm_name}}`).")
        if st.form_submit_button("Save profile"):
            profile["name"] = name_val.strip()
            profile["email"] = email_val.strip()
            profile_store.save(username, profile)
            st.success("Profile saved.")

    st.divider()
    st.subheader("Booking links")
    st.caption("Add one or more Google Calendar appointment links. You'll pick which one to use in the Outreach tab.")

    links = profile.get("booking_links", [])
    to_delete = None

    for idx, lnk in enumerate(links):
        col_l, col_u, col_del = st.columns([2, 4, 1])
        with col_l:
            new_label = st.text_input("Label", value=lnk["label"], key=f"lbl_{idx}")
        with col_u:
            new_url = st.text_input("URL", value=lnk["url"], key=f"url_{idx}")
        with col_del:
            st.write("")
            if st.button("Remove", key=f"del_{idx}"):
                to_delete = idx
        links[idx] = {"label": new_label, "url": new_url}

    if to_delete is not None:
        links.pop(to_delete)
        profile["booking_links"] = links
        profile_store.save(username, profile)
        st.rerun()

    st.divider()
    with st.form("add_link_form"):
        st.write("Add a new booking link")
        new_label = st.text_input("Label (e.g. '30-min product interview')")
        new_url = st.text_input("Google Calendar URL")
        if st.form_submit_button("Add"):
            if new_label.strip() and new_url.strip():
                links.append({"label": new_label.strip(), "url": new_url.strip()})
                profile["booking_links"] = links
                profile_store.save(username, profile)
                st.success("Booking link added.")
                st.rerun()
            else:
                st.warning("Both label and URL are required.")

    if links != profile.get("booking_links"):
        profile["booking_links"] = links
        profile_store.save(username, profile)
