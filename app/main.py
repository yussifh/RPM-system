"""
main.py
-------
Entry point for the Streamlit application.

Design decision: This file stays intentionally thin. Its only job is:
  1. Configure the page (title, icon, layout).
  2. Show a landing/welcome screen with basic project info.
  3. Direct the user to the Login page.

All real logic lives in app/pages/*, app/services/*, etc. Keeping main.py
minimal avoids the common anti-pattern of dumping all UI logic into one
giant script.

Run with:
    streamlit run app/main.py
"""

import streamlit as st

st.set_page_config(
    page_title="AI-Integrated Remote Patient Monitoring System",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_landing_page() -> None:
    """Renders the public-facing welcome/landing screen."""
    st.title("🩺 AI-Integrated Remote Patient Monitoring System")
    st.subheader("Chronic Disease Management: Stroke · Diabetes · Hypertension")

    st.markdown(
        """
        Welcome. This platform enables patients with chronic conditions to
        submit health readings remotely, while doctors and administrators
        monitor patient status in real time using AI-driven risk assessment.

        **Please use the sidebar to navigate to the Login page.**
        """
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Patients**\n\nSubmit vitals, view your health trends and AI feedback.")
    with col2:
        st.info("**Doctors**\n\nMonitor assigned patients, review alerts, add clinical notes.")
    with col3:
        st.info("**Administrators**\n\nManage users, oversee system-wide analytics.")

    st.caption("Final Year Project — for academic demonstration purposes only. "
               "Not a certified medical device.")


if __name__ == "__main__":
    render_landing_page()
