"""
ProductCRM — PM-facing Streamlit UI.
Run with: streamlit run app.py
"""
import asyncio
from datetime import date, datetime

import pandas as pd
import streamlit as st

from src.hubspot import client as hs
from src.selection.pipeline import run_selection
from src.outreach.sender import send_drafts
from src.interviews.transcript import fetch_latest_transcript
from src.interviews.insights import generate_exec_summary
from src.notion.interview_page import create_interview_page
from src.notion.digest import generate_weekly_digest

st.set_page_config(page_title="ProductCRM", layout="wide")
st.title("ProductCRM")
st.caption("Product interview orchestration — from HubSpot to insights.")

tab1, tab2, tab3, tab4 = st.tabs([
    "1 · Filter & Sample",
    "2 · Outreach",
    "3 · Capture Insights",
    "4 · Weekly Digest",
])


# ── Shared session state ───────────────────────────────────────────────────────

if "interviews" not in st.session_state:
    st.session_state.interviews = []
if "pool_size" not in st.session_state:
    st.session_state.pool_size = 0
if "completed_interviews" not in st.session_state:
    st.session_state.completed_interviews = []  # list of {company, contact, date, summary}


# ── Tab 1: Filter & Sample ─────────────────────────────────────────────────────

with tab1:
    st.subheader("Filter companies")

    with st.spinner("Loading HubSpot filter options..."):
        try:
            nature_options = hs.run(hs.fetch_property_options("companies", "nature"))
            tier_options = hs.run(hs.fetch_property_options("companies", "tier_company"))
            category_options = hs.run(hs.fetch_property_options("companies", "macro_category"))
        except Exception as e:
            st.error(f"Could not load HubSpot options: {e}")
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
        with st.spinner("Querying HubSpot..."):
            try:
                interviews, pool_size = asyncio.run(run_selection(
                    n=int(n),
                    nature=nature or None,
                    tier_company=tier or None,
                    macro_category=category or None,
                    beginning_date_from=date_from if date_from else None,
                    beginning_date_to=date_to if date_to else None,
                    arr_live_min=arr_min if arr_min > 0 else None,
                    arr_live_max=arr_max if arr_max > 0 else None,
                ))
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
        st.write(
            f"Ready to create Gmail drafts for **{len(st.session_state.interviews)}** contacts. "
            "Drafts will appear in your Gmail — review before sending."
        )
        if st.button("Generate & create Gmail drafts", type="primary"):
            with st.spinner("Generating emails and creating drafts..."):
                try:
                    drafts = send_drafts(st.session_state.interviews)
                    st.success(f"Created {len(drafts)} Gmail drafts.")
                    for d in drafts:
                        with st.expander(f"{d['contact_email']} — {d['subject']}"):
                            st.text(d["body"])
                except Exception as e:
                    st.error(f"Failed to create drafts: {e}")


# ── Tab 3: Capture Insights ────────────────────────────────────────────────────

with tab3:
    st.subheader("Capture interview insights")
    st.write("After a call, fetch the Granola transcript and generate an exec summary.")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        company_name = st.text_input("Company name")
    with col_b:
        contact_name = st.text_input("Contact name")
    with col_c:
        interview_date = st.date_input("Interview date", value=date.today())

    meeting_hint = st.text_input("Meeting title hint (optional — helps Granola find the right call)")

    if st.button("Fetch transcript & generate summary", type="primary"):
        if not company_name or not contact_name:
            st.warning("Please fill in company and contact name.")
        else:
            with st.spinner("Fetching transcript from Granola..."):
                transcript = fetch_latest_transcript(meeting_hint or company_name)

            if not transcript:
                st.error("No transcript found. Make sure the call was recorded in Granola.")
            else:
                with st.spinner("Generating exec summary..."):
                    summary = generate_exec_summary(transcript, company_name, contact_name)

                st.subheader("Exec Summary")
                st.markdown(summary)

                with st.expander("Full transcript"):
                    st.text(transcript)

                if st.button("Save to Notion"):
                    with st.spinner("Creating Notion page..."):
                        url = create_interview_page(
                            company_name=company_name,
                            contact_name=contact_name,
                            interview_date=interview_date.isoformat(),
                            transcript=transcript,
                            exec_summary=summary,
                        )
                        st.success(f"Notion page created: {url}")
                        st.session_state.completed_interviews.append({
                            "company": company_name,
                            "contact": contact_name,
                            "date": interview_date.isoformat(),
                            "summary": summary,
                        })


# ── Tab 4: Weekly Digest ───────────────────────────────────────────────────────

with tab4:
    st.subheader("Weekly digest")

    if not st.session_state.completed_interviews:
        st.info("No completed interviews yet this session. Capture insights in Tab 3 first.")
    else:
        st.write(
            f"{len(st.session_state.completed_interviews)} interviews captured this session. "
            "Click below to synthesise and post the weekly digest to Notion."
        )
        for i in st.session_state.completed_interviews:
            st.markdown(f"- **{i['company']}** — {i['contact']} ({i['date']})")

        if st.button("Generate & post weekly digest to Notion", type="primary"):
            with st.spinner("Synthesising insights and posting to Notion..."):
                try:
                    url = generate_weekly_digest(st.session_state.completed_interviews)
                    st.success(f"Weekly digest posted: {url}")
                except Exception as e:
                    st.error(f"Failed to generate digest: {e}")
