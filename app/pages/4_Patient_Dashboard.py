"""
4_Patient_Dashboard.py
-------------------------
Patient-only page. Full functionality (vitals submission, personal
trend charts, AI feedback) is built in Phase 5 — this placeholder
proves the role guard works end-to-end.
"""

import streamlit as st

from app.core.security import SessionManager

st.set_page_config(page_title="Patient Dashboard", page_icon="🧑‍⚕️", layout="wide")

user = SessionManager.require_role("patient")

st.title("🧑‍⚕️ Patient Dashboard")
st.write(f"Welcome, **{user['full_name']}**.")
st.info(
    "Full patient functionality — vitals submission, personal trend "
    "charts, and AI-driven feedback — will be built in Phase 5."
)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
