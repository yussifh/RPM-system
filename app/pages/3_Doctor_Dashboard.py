"""
3_Doctor_Dashboard.py
------------------------
Doctor-only page. Full functionality (assigned patient list, AI risk
alerts, clinical notes) is built in Phase 7 — this placeholder proves
the role guard works end-to-end.
"""

import streamlit as st

from app.core.security import SessionManager

st.set_page_config(page_title="Doctor Dashboard", page_icon="🩻", layout="wide")

user = SessionManager.require_role("doctor")

st.title("🩻 Doctor Dashboard")
st.write(f"Welcome, **Dr. {user['full_name']}**.")
st.info(
    "Full doctor functionality — assigned patients, AI risk alerts, "
    "vitals review, and clinical notes — will be built in Phase 7."
)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
