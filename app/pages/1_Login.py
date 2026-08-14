"""
1_Login.py — WITH FORGOT PASSWORD LINK
"""
import streamlit as st
from app.services.auth_service import AuthService
from app.database.repositories.doctor_repository import DoctorRepository
from app.core.security import SessionManager
from app.core.exceptions import AuthenticationError, ValidationError, DuplicateRecordError
from app.utils.custom_css import apply_theme, theme_tokens

st.set_page_config(page_title="RPM System — Login", page_icon=":material/monitor_heart:", layout="centered")
apply_theme()
t = theme_tokens()

auth_service = AuthService()
doctor_repo  = DoctorRepository()

current_user = SessionManager.get_current_user()
if current_user is not None:
    st.success(
        f"You are already logged in as **{current_user['full_name']}** ({current_user['role']}).",
        icon=":material/check_circle:",
    )
    st.info("Use the sidebar to navigate to your dashboard.", icon=":material/info:")
    if st.button("Log out", icon=":material/logout:"):
        SessionManager.logout()
        st.rerun()
    st.stop()

st.markdown(f"""
<div style="text-align:center;padding:32px 0 24px;">
    <div style="width:52px;height:52px;border-radius:14px;background:{t['tint_primary']};
         border:1px solid {t['border']};display:flex;align-items:center;justify-content:center;
         margin:0 auto 14px;">
        <span class="material-symbols-outlined" style="font-size:28px;color:{t['primary']};">monitor_heart</span>
    </div>
    <h1 style="font-size:26px;font-weight:800;color:{t['ink']};margin:0;">RPM System</h1>
    <p style="font-size:13px;color:{t['muted']};margin:4px 0 0;">AI-Integrated Remote Patient Monitoring</p>
    <p style="font-size:12px;color:{t['muted']};margin:2px 0 0;">Chronic Disease Management: Stroke · Diabetes · Hypertension</p>
</div>
""", unsafe_allow_html=True)

login_tab, register_tab = st.tabs([":material/lock_open: Log in", ":material/person_add: Patient registration"])

with login_tab:
    with st.form("login_form"):
        email    = st.text_input("Email address", placeholder="admin@rpm.com")
        password = st.text_input("Password",       type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign in", width="stretch", icon=":material/login:")
        if submitted:
            if not email or not password:
                st.warning("Please enter both email and password.", icon=":material/warning:")
            else:
                try:
                    user = auth_service.authenticate(email, password)
                    SessionManager.login(user)
                    st.success(f"Welcome back, {user.full_name}!", icon=":material/check_circle:")
                    st.rerun()
                except AuthenticationError as e:
                    st.error(str(e), icon=":material/error:")

    # Forgot password link
    st.markdown(f"""
    <div style="text-align:center;margin-top:14px;">
        <a href="/Reset_Password" target="_self"
           style="color:{t['primary']};font-size:13px;font-weight:500;text-decoration:none;">
            Forgot your password?
        </a>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(":material/key: Demo accounts", icon=":material/key:"):
        c1, c2, c3 = st.columns(3)
        with c1: st.code("Admin\nadmin@rpm.com\nadmin1234")
        with c2: st.code("Doctor\ndoctor@rpm.com\ndoctor1234")
        with c3: st.code("Patient\npatient@rpm.com\npatient1234")

    st.markdown(f'<p style="text-align:center;font-size:12px;color:{t["muted"]};margin-top:16px;">'
                'Doctor and admin accounts are provisioned by the system administrator.</p>',
                unsafe_allow_html=True)

with register_tab:
    st.info(":material/person: Create your patient account to start monitoring your health remotely.",
            icon=":material/person:")
    doctors = doctor_repo.list_all()
    doctor_options = {"— Assign later —": None}
    doctor_options.update({f"Dr. {d.specialization or 'General'} (Lic: {d.license_number})": d.user_id for d in doctors})

    with st.form("register_form"):
        c1, c2 = st.columns(2)
        with c1:
            full_name  = st.text_input("Full name",         placeholder="John Mensah")
            email_r    = st.text_input("Email address",      placeholder="yourname@rpm.com", key="reg_email")
            password_r = st.text_input("Password",           type="password", key="reg_password",
                                        help="At least 8 characters including a letter and a number")
            confirm_r  = st.text_input("Confirm password",  type="password")
        with c2:
            dob    = st.date_input("Date of birth", min_value="1900-01-01")
            gender = st.selectbox("Gender", ["male", "female", "other"])
            phone  = st.text_input("Phone number (optional)", placeholder="+233 24 000 0000")
            emergency_contact = st.text_input("Emergency contact (optional)")
        conditions    = st.multiselect("Chronic conditions ✱", ["stroke", "diabetes", "hypertension"])
        chosen_doctor = st.selectbox("Preferred doctor (optional)", list(doctor_options.keys()))
        st.caption("By registering you confirm this system is used for academic demonstration only.")
        reg_sub = st.form_submit_button("Create my account", width="stretch", icon=":material/person_add:")
        if reg_sub:
            if password_r != confirm_r:
                st.error("Passwords do not match.", icon=":material/error:")
            elif not conditions:
                st.error("Please select at least one chronic condition.", icon=":material/error:")
            else:
                try:
                    user = auth_service.register_patient(
                        full_name=full_name, email=email_r, password=password_r,
                        date_of_birth=dob, gender=gender, chronic_conditions=conditions,
                        assigned_doctor_id=doctor_options[chosen_doctor],
                        phone_number=phone or None, emergency_contact=emergency_contact or None,
                    )
                    st.success(
                        f"Account created for **{user.full_name}**! Please log in using the Log in tab.",
                        icon=":material/check_circle:",
                    )
                    st.balloons()
                except (ValidationError, DuplicateRecordError) as e:
                    st.error(str(e), icon=":material/error:")
