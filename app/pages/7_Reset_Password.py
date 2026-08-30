"""
7_Reset_Password.py — OTP VERSION
Password reset using a 6-digit One Time PIN.
"""

import streamlit as st
import time
from app.services.otp_service import OTPService
from app.core.exceptions import ValidationError
from app.utils.custom_css import apply_theme

st.set_page_config(page_title="Reset Password", page_icon=":material/key:", layout="centered")
apply_theme()

otp_service = OTPService()

# ── Session state ─────────────────────────────────────────────────
for key, default in [("otp_email_sent", False), ("otp_email", ""),
                      ("otp_done", False), ("otp_generated_at", None),
                      ("otp_attempts", 0)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Page header ───────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:28px 0 20px;">
    <div style="width:14px;height:14px;border-radius:50%;
         background:#0E7A5C;margin:0 auto 12px;"></div>
    <h1 style="font-size:24px;font-weight:800;color:#16242B;margin:0;">
        Reset Your Password
    </h1>
    <p style="font-size:13px;color:#5F717A;margin:6px 0 0;">
        We will generate a 6-digit One Time PIN (OTP) for you.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Step indicator ────────────────────────────────────────────────
step = 3 if st.session_state["otp_done"] else (2 if st.session_state["otp_email_sent"] else 1)

cols = st.columns(3)
step_styles = {
    "active":   "background:#0E7A5C;color:white;text-align:center;border-radius:8px;padding:8px;font-size:12px;font-weight:700;",
    "inactive": "background:#DCE5E1;color:#5F717A;text-align:center;border-radius:8px;padding:8px;font-size:12px;",
}
steps = [
    (1, "1 · Enter Email"),
    (2, "2 · Enter OTP"),
    (3, "3 · Done ✓"),
]
for col, (s, label) in zip(cols, steps):
    style = step_styles["active"] if step >= s else step_styles["inactive"]
    col.markdown(f'<div style="{style}">{label}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ================================================================
# STEP 1 — Enter Email
# ================================================================
if step == 1:
    st.subheader("Step 1 — Enter your registered email")

    with st.form("email_form"):
        email = st.text_input(
            "Email Address",
            placeholder="admin@rpm.com",
        )
        submitted = st.form_submit_button(
            "Generate OTP →", width="stretch"
        )

        if submitted:
            if not email.strip():
                st.error("Please enter your email address.")
            else:
                sent = otp_service.email_otp(email.strip())

                # Always show the same message for security
                if sent:
                    st.session_state["otp_email"]        = email.strip()
                    st.session_state["otp_email_sent"]   = True
                    st.session_state["otp_generated_at"] = time.time()
                    st.session_state["otp_attempts"]     = 0

                    st.success("If this email is registered, a One Time PIN has been sent.")
                    st.info(f"Check your inbox at **{email.strip()}** — the OTP expires in 10 minutes.")
                else:
                    # Email not found or SMTP not configured — same generic message
                    st.info("If your email is registered, check your inbox. Otherwise contact admin.")

# ================================================================
# STEP 2 — Enter OTP + New Password
# ================================================================
elif step == 2:
    st.subheader("Step 2 — Enter OTP and set new password")

    # OTP countdown timer
    if st.session_state["otp_generated_at"]:
        elapsed  = time.time() - st.session_state["otp_generated_at"]
        remaining = max(0, 600 - elapsed)  # 10 minutes = 600 seconds
        mins = int(remaining // 60)
        secs = int(remaining % 60)

        if remaining > 0:
            color = "#0E7A5C" if remaining > 120 else "#B8761D" if remaining > 30 else "#C73E3A"
            st.markdown(f"""
            <div style="background:white;border:1px solid #DCE5E1;border-radius:8px;
                 padding:10px 16px;display:flex;align-items:center;
                 justify-content:space-between;margin-bottom:16px;">
                <span style="font-size:13px;color:#5F717A;">OTP expires in:</span>
                <span style="font-size:18px;font-weight:700;color:{color};
                      font-family:monospace;">{mins:02d}:{secs:02d}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Your OTP has expired. Please request a new one.")
            if st.button("← Request New OTP"):
                st.session_state["otp_email_sent"]   = False
                st.session_state["otp_email"]        = ""
                st.session_state["otp_generated_at"] = None
                st.rerun()
            st.stop()

    # Show OTP reminder
    st.info(f"Resetting password for: **{st.session_state['otp_email']}**")

    # Attempt counter warning
    attempts = st.session_state["otp_attempts"]
    if attempts > 0:
        remaining_attempts = OTPService.MAX_ATTEMPTS - attempts
        if remaining_attempts <= 0:
            st.error("Too many failed attempts. Please request a new OTP.")
            if st.button("← Request New OTP"):
                st.session_state["otp_email_sent"]   = False
                st.session_state["otp_email"]        = ""
                st.session_state["otp_generated_at"] = None
                st.session_state["otp_attempts"]     = 0
                st.rerun()
            st.stop()
        else:
            st.warning(f"{attempts} failed attempt(s). {remaining_attempts} remaining.")

    with st.form("reset_form"):
        otp_input = st.text_input(
            "Enter OTP",
            placeholder="6-digit PIN",
            max_chars=6,
            help="Check your email for the 6-digit PIN"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="At least 8 characters, include a letter and a number"
        )
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        # Password strength indicator
        if new_password:
            has_letter  = any(c.isalpha() for c in new_password)
            has_digit   = any(c.isdigit() for c in new_password)
            long_enough = len(new_password) >= 8
            strength = sum([has_letter, has_digit, long_enough])
            colors = ["#C73E3A", "#B8761D", "#0E7A5C"]
            labels = ["Weak", "Fair", "Strong"]
            if strength > 0:
                st.markdown(
                    f'<div style="background:{colors[strength-1]};color:white;'
                    f'border-radius:4px;padding:4px 12px;font-size:12px;'
                    f'font-weight:600;display:inline-block;margin:4px 0;">'
                    f'Password strength: {labels[strength-1]}</div>',
                    unsafe_allow_html=True
                )

        submitted = st.form_submit_button(
            "Reset password", width="stretch"
        )

        if submitted:
            if len(otp_input.strip()) != 6 or not otp_input.strip().isdigit():
                st.error("Please enter a valid 6-digit OTP.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    success = otp_service.verify_and_reset(
                        email=st.session_state["otp_email"],
                        otp=otp_input.strip(),
                        new_password=new_password,
                    )
                    if success:
                        st.session_state["otp_done"] = True
                        st.rerun()
                except ValidationError as e:
                    st.session_state["otp_attempts"] += 1
                    st.error(str(e))

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Use a different email"):
        st.session_state["otp_email_sent"]   = False
        st.session_state["otp_email"]        = ""
        st.session_state["otp_generated_at"] = None
        st.session_state["otp_attempts"]     = 0
        st.rerun()

# ================================================================
# STEP 3 — Success
# ================================================================
elif step == 3:
    st.markdown("""
    <div style="text-align:center;padding:40px 20px;">
        <div class="material-symbols-outlined" style="font-size:72px;margin-bottom:16px;">check_circle</div>
        <h2 style="color:#0A5E46;font-size:26px;font-weight:800;margin:0 0 10px;">
            Password Reset Successfully!
        </h2>
        <p style="color:#5F717A;font-size:14px;margin:0 0 8px;">
            Your password has been updated.
        </p>
        <p style="color:#5F717A;font-size:13px;">
            You can now log in with your new password.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button(":material/lock: Go to login page →", width="stretch"):
        st.session_state["otp_email_sent"]   = False
        st.session_state["otp_email"]        = ""
        st.session_state["otp_done"]         = False
        st.session_state["otp_generated_at"] = None
        st.session_state["otp_attempts"]     = 0
        st.switch_page("pages/1_Login.py")

st.caption("Academic demonstration only — not a certified medical system.")
