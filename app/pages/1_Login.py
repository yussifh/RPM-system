"""
1_Login.py
----------
Placeholder for the authentication page.

Streamlit auto-discovers files in app/pages/ and builds sidebar navigation
from the filename (numeric prefix controls ordering). The real
authentication logic (password verification, session creation) will be
wired up in Phase 4 via app/services/auth_service.py.

For now, this page just confirms the multipage routing works end-to-end.
"""

import streamlit as st

st.set_page_config(page_title="Login", page_icon="🔐")

st.title("🔐 Login")
st.info(
    "Authentication will be implemented in Phase 4. "
    "This page currently exists to verify the project skeleton "
    "and Streamlit multipage navigation are working correctly."
)

with st.form("login_form_placeholder", clear_on_submit=False):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log In")

    if submitted:
        st.warning("Login logic not yet implemented — coming in Phase 4.")
