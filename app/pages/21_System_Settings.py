"""
21_System_Settings.py — Admin-configurable system settings
"""
import streamlit as st
from app.utils.custom_css import apply_theme, profile_widget, notification_bell
from app.core.security import SessionManager
from app.database.repositories.settings_repository import SettingsRepository

st.set_page_config(page_title="RPM — System Settings", page_icon="⚙️", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.switch_page("pages/1_Login.py")
    st.stop()

if user["role"] != "admin":
    st.error("⛔ Access denied. Admin only.")
    st.stop()

profile_widget(user)
notification_bell(user)

settings_repo = SettingsRepository()
settings_repo.seed_defaults()

st.markdown("## ⚙️ System Settings")

tab1, tab2, tab3, tab4 = st.tabs(["🏥 Clinic Info", "📊 Vitals Thresholds", "📧 Notifications", "🔐 Security"])

with tab1:
    st.markdown("### Clinic Information")
    with st.form("clinic_form"):
        c1, c2 = st.columns(2)
        with c1:
            clinic_name = st.text_input("Clinic Name", value=settings_repo.get("clinic_name") or "")
            clinic_email = st.text_input("Clinic Email", value=settings_repo.get("clinic_email") or "")
        with c2:
            clinic_phone = st.text_input("Clinic Phone", value=settings_repo.get("clinic_phone") or "")
            st.empty()

        if st.form_submit_button("💾 Save Clinic Info", use_container_width=True):
            settings_repo.set("clinic_name", clinic_name, user["id"])
            settings_repo.set("clinic_email", clinic_email, user["id"])
            settings_repo.set("clinic_phone", clinic_phone, user["id"])
            st.success("Clinic information updated!")
            st.rerun()

with tab2:
    st.markdown("### Vitals Alert Thresholds")
    st.caption("Alerts trigger when patient readings exceed these values.")

    with st.form("thresholds_form"):
        c1, c2 = st.columns(2)
        with c1:
            bp_systolic = st.number_input("Systolic BP High (mmHg)",
                                           value=int(settings_repo.get("vitals_threshold_bp_systolic_high") or 140))
            bp_diastolic = st.number_input("Diastolic BP High (mmHg)",
                                            value=int(settings_repo.get("vitals_threshold_bp_diastolic_high") or 90))
            hr_high = st.number_input("Heart Rate High (bpm)",
                                       value=int(settings_repo.get("vitals_threshold_hr_high") or 100))
            hr_low = st.number_input("Heart Rate Low (bpm)",
                                      value=int(settings_repo.get("vitals_threshold_hr_low") or 50))
        with c2:
            glucose_high = st.number_input("Glucose High (mg/dL)",
                                            value=int(settings_repo.get("vitals_threshold_glucose_high") or 200))
            glucose_low = st.number_input("Glucose Low (mg/dL)",
                                           value=int(settings_repo.get("vitals_threshold_glucose_low") or 54))
            spo2_low = st.number_input("SpO2 Low (%)",
                                        value=int(settings_repo.get("vitals_threshold_spo2_low") or 90))
            st.empty()

        if st.form_submit_button("💾 Save Thresholds", use_container_width=True):
            settings_repo.set("vitals_threshold_bp_systolic_high", str(bp_systolic), user["id"])
            settings_repo.set("vitals_threshold_bp_diastolic_high", str(bp_diastolic), user["id"])
            settings_repo.set("vitals_threshold_hr_high", str(hr_high), user["id"])
            settings_repo.set("vitals_threshold_hr_low", str(hr_low), user["id"])
            settings_repo.set("vitals_threshold_glucose_high", str(glucose_high), user["id"])
            settings_repo.set("vitals_threshold_glucose_low", str(glucose_low), user["id"])
            settings_repo.set("vitals_threshold_spo2_low", str(spo2_low), user["id"])
            st.success("Vitals thresholds updated!")
            st.rerun()

with tab3:
    st.markdown("### Notification Settings")

    with st.form("notify_form"):
        c1, c2 = st.columns(2)
        with c1:
            smtp_host = st.text_input("SMTP Host", value=settings_repo.get("smtp_host") or "")
            smtp_port = st.text_input("SMTP Port", value=settings_repo.get("smtp_port") or "587")
            smtp_user = st.text_input("SMTP Username", value=settings_repo.get("smtp_user") or "")
            smtp_pass = st.text_input("SMTP Password", value=settings_repo.get("smtp_password") or "",
                                       type="password")
        with c2:
            enable_email = st.toggle("Enable Email Alerts",
                                      value=(settings_repo.get("enable_email_alerts") == "true"))
            enable_sms = st.toggle("Enable SMS Alerts",
                                    value=(settings_repo.get("enable_sms_alerts") == "true"))
            st.empty()
            st.empty()

        if st.form_submit_button("💾 Save Notification Settings", use_container_width=True):
            settings_repo.set("smtp_host", smtp_host, user["id"])
            settings_repo.set("smtp_port", smtp_port, user["id"])
            settings_repo.set("smtp_user", smtp_user, user["id"])
            settings_repo.set("smtp_password", smtp_pass, user["id"])
            settings_repo.set("enable_email_alerts", "true" if enable_email else "false", user["id"])
            settings_repo.set("enable_sms_alerts", "true" if enable_sms else "false", user["id"])
            st.success("Notification settings updated!")
            st.rerun()

with tab4:
    st.markdown("### Security Settings")

    with st.form("security_form"):
        session_timeout = st.number_input(
            "Session Timeout (minutes)",
            min_value=5, max_value=480,
            value=int(settings_repo.get("session_timeout_min") or 60),
        )

        if st.form_submit_button("💾 Save Security Settings", use_container_width=True):
            settings_repo.set("session_timeout_min", str(session_timeout), user["id"])
            st.success("Security settings updated!")
            st.rerun()

st.markdown("---")
st.markdown("### All Settings")
with st.expander("View raw settings table"):
    all_settings = settings_repo.list_all()
    for s in all_settings:
        st.text(f"{s['setting_key']}: {s['setting_value']}")
