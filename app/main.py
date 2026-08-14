"""
main.py — Landing page for the RPM System ("The Vitals Monitor" theme).
"""
import streamlit as st
from app.utils.custom_css import apply_theme, ecg_svg, theme_tokens

st.set_page_config(
    page_title="AI-Integrated Remote Patient Monitoring System",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()
t = theme_tokens()

# ── Hero ──────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:46px 20px 26px;">
    <div style="display:inline-flex;align-items:center;gap:10px;margin-bottom:18px;">
        <span style="width:10px;height:10px;border-radius:50%;background:{t['pulse']};
              box-shadow:0 0 0 0 {t['pulse']};animation:vpulse 2.4s infinite;"></span>
        <span style="font-size:11px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;
              color:{t['muted']};">Remote Patient Monitoring</span>
    </div>
    <h1 style="font-family:'Space Grotesk',sans-serif;font-size:38px;font-weight:700;
         color:{t['ink']};margin:0;line-height:1.12;letter-spacing:-.02em;">
        AI-Integrated Remote<br>Patient Monitoring System
    </h1>
    <p style="font-size:15px;color:{t['muted']};margin:14px 0 0;font-weight:400;">
        Chronic Disease Management: Stroke · Diabetes · Hypertension
    </p>
    <div style="margin-top:18px;">
        <span style="background:{t['tint_primary']};color:{t['primary']};padding:4px 14px;
              border-radius:20px;font-size:12px;font-weight:600;margin:4px;">Final Year Project — UENR</span>
        <span style="background:{t['tint_primary']};color:{t['primary']};padding:4px 14px;
              border-radius:20px;font-size:12px;font-weight:600;margin:4px;">Computer Science</span>
        <span style="background:{t['tint_primary']};color:{t['primary']};padding:4px 14px;
              border-radius:20px;font-size:12px;font-weight:600;margin:4px;">Academic Demo Only</span>
    </div>
</div>
<div style="max-width:640px;margin:0 auto 8px;">{ecg_svg(t['pulse'], width=84, height=30)}</div>
""", unsafe_allow_html=True)

st.divider()

# ── Feature overview ──────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div style="background:{t['surface']};border:1px solid {t['border']};border-top:3px solid {t['primary']};
         border-radius:12px;padding:20px;text-align:center;height:100%;">
        <div style="font-size:32px;margin-bottom:10px;">👤</div>
        <h3 style="font-family:'Space Grotesk',sans-serif;color:{t['ink']};font-size:16px;margin:0 0 8px;">Patients</h3>
        <p style="color:{t['muted']};font-size:13px;line-height:1.6;">
            Submit vitals remotely, view AI risk assessments,
            download health reports and message your doctor.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:{t['surface']};border:1px solid {t['border']};border-top:3px solid {t['info']};
         border-radius:12px;padding:20px;text-align:center;height:100%;">
        <div style="font-size:32px;margin-bottom:10px;">🩺</div>
        <h3 style="font-family:'Space Grotesk',sans-serif;color:{t['ink']};font-size:16px;margin:0 0 8px;">Doctors</h3>
        <p style="color:{t['muted']};font-size:13px;line-height:1.6;">
            Monitor assigned patients, receive severity alerts,
            book appointments and reply to patient messages.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background:{t['surface']};border:1px solid {t['border']};border-top:3px solid {t['amber']};
         border-radius:12px;padding:20px;text-align:center;height:100%;">
        <div style="font-size:32px;margin-bottom:10px;">🛠️</div>
        <h3 style="font-family:'Space Grotesk',sans-serif;color:{t['ink']};font-size:16px;margin:0 0 8px;">Administrators</h3>
        <p style="color:{t['muted']};font-size:13px;line-height:1.6;">
            Manage users, provision doctor accounts,
            view system analytics and audit logs.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── AI Features ───────────────────────────────────────────────────
st.subheader("AI & Machine Learning Features")
a1, a2, a3, a4 = st.columns(4)
a1.success("**Stroke Risk**\nLogistic Regression model trained on clinical data")
a2.success("**Diabetes Risk**\nPima Indians dataset-inspired prediction model")
a3.success("**Hypertension Risk**\nFramingham Heart Study-inspired model")
a4.success("**Severity Engine**\nReal-time NLP symptom analysis with 25+ rules")

st.divider()
st.caption(
    "⚠️ Final Year Project — University of Energy and Natural Resources (UENR), Sunyani, Ghana. "
    "This is NOT a certified medical device. For academic demonstration purposes only."
)
st.caption("**Please use the sidebar to navigate to the Login page to get started.**")
