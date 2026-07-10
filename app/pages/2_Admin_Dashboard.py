"""
2_Admin_Dashboard.py
----------------------
Admin-only page. Full admin functionality (user management, system-wide
analytics, audit log viewer) is built in Phase 8 — this placeholder
exists now to prove the role-based access guard works end-to-end.
"""

import streamlit as st

from app.core.security import SessionManager

st.set_page_config(page_title="Admin Dashboard", page_icon="🛠️", layout="wide")

# Access guard: MUST be the first substantive line. Halts execution
# for anyone not logged in as 'admin'.
user = SessionManager.require_role("admin")

st.title("🛠️ Administrator Dashboard")
st.write(f"Welcome, **{user['full_name']}**.")
st.info(
    "Full admin functionality — user management, doctor/patient "
    "assignment, system-wide analytics, and audit log viewer — "
    "will be built in Phase 8."
)

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
