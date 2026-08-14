"""
1_Login.py — WITH FORGOT PASSWORD LINK
"""
import streamlit as st
from app.services.auth_service import AuthService
from app.database.repositories.doctor_repository import DoctorRepository
from app.core.security import SessionManager
from app.core.exceptions import AuthenticationError, ValidationError, DuplicateRecordError
from app.utils.custom_css import apply_theme

st.set_page_config(page_title="RPM System — Login", page_icon="🩺", layout="centered")
apply_theme()

auth_service = AuthService()
doctor_repo  = DoctorRepository()

current_user = SessionManager.get_current_user()
if current_user is not None:
    st.success(f"You are already logged in as **{current_user['full_name']}** ({current_user['role']}).")
    st.info("Use the sidebar to navigate to your dashboard.")
    if st.button("Log Out"):
        SessionManager.logout()
        st.rerun()
    st.stop()

st.markdown("""
<div style="text-align:center;padding:32px 0 24px;">
    <div style="width:14px;height:14px;border-radius:50%;background:#0E7A5C;margin:0 auto 12px;"></div>
    <h1 style="font-size:26px;font-weight:800;color:#16242B;margin:0;">RPM System</h1>
    <p style="font-size:13px;color:#5F717A;margin:4px 0 0;">AI-Integrated Remote Patient Monitoring</p>
    <p style="font-size:12px;color:#5F717A;margin:2px 0 0;">Chronic Disease Management: Stroke · Diabetes · Hypertension</p>
</div>
""", unsafe_allow_html=True)

login_tab, register_tab = st.tabs(["🔐 Log In", "📋 Patient Registration"])

with login_tab:
    with st.form("login_form"):
        email    = st.text_input("Email address", placeholder="admin@rpm.com")
        password = st.text_input("Password",       type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Sign In →", use_container_width=True)
        if submitted:
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                try:
                    user = auth_service.authenticate(email, password)
                    SessionManager.login(user)
                    st.success(f"Welcome back, {user.full_name}!")
                    st.rerun()
                except AuthenticationError as e:
                    st.error(str(e))

    # Forgot password link
    st.markdown("""
    <div style="text-align:center;margin-top:14px;">
        <a href="/Reset_Password" target="_self"
           style="color:#0E7A5C;font-size:13px;font-weight:500;text-decoration:none;">
            🔑 Forgot your password?
        </a>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔑 Demo accounts"):
        c1, c2, c3 = st.columns(3)
        with c1: st.code("Admin\nadmin@rpm.com\nadmin1234")
        with c2: st.code("Doctor\ndoctor@rpm.com\ndoctor1234")
        with c3: st.code("Patient\npatient@rpm.com\npatient1234")

    st.markdown('<p style="text-align:center;font-size:12px;color:#5F717A;margin-top:16px;">Doctor and admin accounts are provisioned by the system administrator.</p>', unsafe_allow_html=True)

with register_tab:
    st.info("👤 Create your patient account to start monitoring your health remotely.")
    doctors = doctor_repo.list_all()
    doctor_options = {"— Assign later —": None}
    doctor_options.update({f"Dr. {d.specialization or 'General'} (Lic: {d.license_number})": d.user_id for d in doctors})

    with st.form("register_form"):
        c1, c2 = st.columns(2)
        with c1:
            full_name  = st.text_input("Full Name",         placeholder="John Mensah")
            email_r    = st.text_input("Email Address",      placeholder="yourname@rpm.com", key="reg_email")
            password_r = st.text_input("Password",           type="password", key="reg_password",
                                        help="At least 8 characters including a letter and a number")
            confirm_r  = st.text_input("Confirm Password",  type="password")
        with c2:
            dob    = st.date_input("Date of Birth", min_value="1900-01-01")
            gender = st.selectbox("Gender", ["male","female","other"])
            phone  = st.text_input("Phone Number (optional)", placeholder="+233 24 000 0000")
            emergency_contact = st.text_input("Emergency Contact (optional)")
        conditions    = st.multiselect("Chronic Conditions ✱", ["stroke","diabetes","hypertension"])
        chosen_doctor = st.selectbox("Preferred Doctor (optional)", list(doctor_options.keys()))
        st.caption("By registering you confirm this system is used for academic demonstration only.")
        reg_sub = st.form_submit_button("Create My Account ✅", use_container_width=True)
        if reg_sub:
            if password_r != confirm_r:
                st.error("Passwords do not match.")
            elif not conditions:
                st.error("Please select at least one chronic condition.")
            else:
                try:
                    user = auth_service.register_patient(
                        full_name=full_name, email=email_r, password=password_r,
                        date_of_birth=dob, gender=gender, chronic_conditions=conditions,
                        assigned_doctor_id=doctor_options[chosen_doctor],
                        phone_number=phone or None, emergency_contact=emergency_contact or None,
                    )
                    st.success(f"✅ Account created for **{user.full_name}**! Please log in using the Log In tab.")
                    st.balloons()
                except (ValidationError, DuplicateRecordError) as e:
                    st.error(str(e))
