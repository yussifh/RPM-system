"""
0_Home.py — Landing page for the RPM System ("The Vitals Monitor" theme).
"""
import streamlit as st
from app.utils.custom_css import (
    apply_theme,
    landing_hero,
    feature_card,
    stat_card,
    section_heading,
    theme_tokens,
)

st.set_page_config(
    page_title="AI-Integrated Remote Patient Monitoring System",
    page_icon=":material/monitor_heart:",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()
t = theme_tokens()

# ── Hero ──────────────────────────────────────────────────────────
st.markdown(
    landing_hero(
        eyebrow="Remote Patient Monitoring",
        title="AI-Integrated Remote<br>Patient Monitoring System",
        subtitle=(
            "Continuous vitals monitoring, real-time AI risk assessment and secure "
            "doctor–patient communication for chronic disease management."
        ),
        tags=["Final Year Project — UENR", "Computer Science", "Academic Demo Only"],
    ),
    unsafe_allow_html=True,
)

# ── Stats strip ───────────────────────────────────────────────────
s1, s2, s3, s4 = st.columns(4)
s1.markdown(stat_card("Chronic diseases", "3", "stroke · diabetes · hypertension"), unsafe_allow_html=True)
s2.markdown(stat_card("ML models", "3", "trained on real clinical datasets"), unsafe_allow_html=True)
s3.markdown(stat_card("Severity rules", "25+", "real-time symptom analysis"), unsafe_allow_html=True)
s4.markdown(stat_card("Roles", "3", "patient · doctor · admin"), unsafe_allow_html=True)

# ── Role overview ─────────────────────────────────────────────────
st.markdown(
    section_heading(":material/group:", "Built for every role",
                    "A complete workflow connecting patients, doctors and administrators."),
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        feature_card(
            "person",
            "Patients",
            "Submit vitals remotely, view AI risk assessments, download health reports "
            "and message your doctor.",
            accent=t["primary"],
        ),
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        feature_card(
            "stethoscope",
            "Doctors",
            "Monitor assigned patients, receive severity alerts, book appointments "
            "and reply to patient messages.",
            accent=t["info"],
        ),
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        feature_card(
            "admin_panel_settings",
            "Administrators",
            "Manage users, provision doctor accounts, view system analytics "
            "and audit logs.",
            accent=t["amber"],
        ),
        unsafe_allow_html=True,
    )

# ── How it works ──────────────────────────────────────────────────
st.markdown(
    section_heading(":material/timeline:", "How it works",
                    "From vitals entry to clinical insight in three steps."),
    unsafe_allow_html=True,
)

w1, w2, w3, w4 = st.columns(4)
steps = [
    ("monitor_heart", "1 · Record", "Patients enter their vitals (BP, heart rate, glucose, SpO2) at home."),
    ("psychology", "2 · Assess", "ML models and the severity engine score stroke, diabetes and hypertension risk."),
    ("notifications", "3 · Alert", "Abnormal readings generate severity-based alerts to the assigned doctor."),
    ("medical_information", "4 · Act", "Doctors acknowledge, schedule follow-ups and document clinical notes."),
]
for col, (icon, title, desc) in zip((w1, w2, w3, w4), steps):
    col.markdown(
        f"""
        <div style="background:{t['surface']};border:1px solid {t['border']};border-radius:14px;
             padding:18px 16px;height:100%;">
            <span class="material-symbols-outlined" style="font-size:26px;color:{t['primary']};">{icon}</span>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:14px;
                 color:{t['ink']};margin:8px 0 6px;">{title}</div>
            <p style="font-size:12px;color:{t['muted']};line-height:1.6;margin:0;">{desc}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── AI features ───────────────────────────────────────────────────
st.markdown(
    section_heading(":material/psychology:", "AI & machine learning features"),
    unsafe_allow_html=True,
)

a1, a2, a3, a4 = st.columns(4)
a1.success("**Stroke risk**\nLogistic Regression model trained on clinical data", icon=":material/emergency:")
a2.success("**Diabetes risk**\nPima Indians dataset-inspired prediction model", icon=":material/bloodtype:")
a3.success("**Hypertension risk**\nFramingham Heart Study-inspired model", icon=":material/favorite:")
a4.success("**Severity engine**\nReal-time NLP symptom analysis with 25+ rules", icon=":material/flag:")

# ── Get started ───────────────────────────────────────────────────
st.markdown(
    section_heading(":material/login:", "Get started",
                    "Use the sidebar to open the login page and sign in with your account."),
    unsafe_allow_html=True,
)

st.caption(
    "⚠️ Final Year Project — University of Energy and Natural Resources (UENR), Sunyani, Ghana. "
    "This is NOT a certified medical device. For academic demonstration purposes only."
)

if st.button("Log In / Register", icon=":material/login:", type="primary"):
    st.switch_page("pages/1_Login.py")