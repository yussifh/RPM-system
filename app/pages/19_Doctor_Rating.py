"""
19_Doctor_Rating.py — Patients rate doctors; doctors see feedback
"""
import streamlit as st
from app.utils.custom_css import apply_theme, profile_widget, notification_bell
from app.core.security import SessionManager
from app.database.repositories.rating_repository import RatingRepository
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.doctor_repository import DoctorRepository

st.set_page_config(page_title="RPM — Doctor Rating", page_icon="⭐", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.switch_page("pages/1_Login.py")
    st.stop()

profile_widget(user)
notification_bell(user)

rating_repo = RatingRepository()
patient_repo = PatientRepository()
doctor_repo = DoctorRepository()

st.markdown("## ⭐ Doctor Ratings")

role = user["role"]

if role == "patient":
    try:
        patient = patient_repo.get_by_user_id(user["id"])
        doctor_user_id = patient.assigned_doctor_id
    except Exception:
        doctor_user_id = None

    if not doctor_user_id:
        st.info("No doctor assigned yet.")
        st.stop()

    try:
        doctor = doctor_repo.get_by_user_id(doctor_user_id)
    except Exception:
        st.info("Doctor profile not found.")
        st.stop()

    avg = rating_repo.get_average_rating(doctor_user_id)
    total = rating_repo.get_total_count(doctor_user_id)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Average Rating", f"{avg}/5" if avg else "No ratings")
        st.metric("Total Reviews", total)
        existing = rating_repo.list_for_doctor(doctor_user_id)
        my_rating = [r for r in existing if r["patient_user_id"] == user["id"]]
        if my_rating:
            st.success(f"You already rated this doctor: {'⭐' * my_rating[0]['rating']}")

    with c2:
        st.markdown(f"### Rate Dr. {doctor.specialization or 'General'}")
        if not my_rating:
            with st.form("rate_form"):
                stars = st.slider("Your Rating", 1, 5, 3, help="1=Poor, 5=Excellent")
                comment = st.text_area("Your Feedback (optional)", placeholder="How was your experience?")
                if st.form_submit_button("Submit Rating", use_container_width=True):
                    if stars < 1 or stars > 5:
                        st.error("Rating must be between 1 and 5.")
                    else:
                        rating_repo.create(
                            patient_user_id=user["id"],
                            doctor_user_id=doctor_user_id,
                            rating=stars,
                            comment=comment or None,
                        )
                        st.success("Thank you for your feedback!")
                        st.rerun()
        else:
            st.info("You have already rated this doctor.")

    if existing:
        st.markdown("---")
        st.markdown("### All Ratings for This Doctor")
        for r in existing[:10]:
            with st.container():
                st.markdown(f"""
                <div style="background:white;border:1px solid #DCE5E1;border-radius:10px;padding:14px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:600;color:#16242B;">{r['patient_name']}</span>
                        <span style="color:#B8761D;font-size:14px;">{'⭐' * r['rating']}</span>
                    </div>
                    <div style="font-size:11px;color:#5F717A;margin-top:2px;">{r['created_at'].strftime('%Y-%m-%d %H:%M') if r['created_at'] else ''}</div>
                    {'<p style="margin-top:6px;font-size:13px;color:#333;">' + r['comment'] + '</p>' if r.get('comment') else ''}
                </div>
                """, unsafe_allow_html=True)

elif role == "doctor":
    ratings = rating_repo.list_for_doctor(user["id"])
    avg = rating_repo.get_average_rating(user["id"])
    total = rating_repo.get_total_count(user["id"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Average Rating", f"{avg}/5" if avg else "No ratings")
    c2.metric("Total Reviews", total)
    if total > 0:
        c3.metric("5-Star Reviews",
                   sum(1 for r in ratings if r["rating"] == 5))

    st.markdown("---")
    if not ratings:
        st.info("No ratings received yet.")
    else:
        for r in ratings:
            with st.container():
                st.markdown(f"""
                <div style="background:white;border:1px solid #DCE5E1;border-radius:10px;padding:14px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:600;color:#16242B;">{r['patient_name']}</span>
                        <span style="color:#B8761D;font-size:14px;">{'⭐' * r['rating']}</span>
                    </div>
                    <div style="font-size:11px;color:#5F717A;margin-top:2px;">{r['created_at'].strftime('%Y-%m-%d %H:%M') if r['created_at'] else ''}</div>
                    {'<p style="margin-top:6px;font-size:13px;color:#333;">' + r['comment'] + '</p>' if r.get('comment') else ''}
                </div>
                """, unsafe_allow_html=True)

elif role == "admin":
    ratings = rating_repo.list_all()
    avg_all = sum(r["rating"] for r in ratings) / len(ratings) if ratings else 0

    c1, c2 = st.columns(2)
    c1.metric("Total Ratings", len(ratings))
    c2.metric("System Average", f"{avg_all:.1f}/5" if ratings else "N/A")

    st.markdown("---")
    if not ratings:
        st.info("No ratings in the system.")
    else:
        import pandas as pd
        df = pd.DataFrame(ratings)
        st.dataframe(df[["patient_name", "doctor_name", "rating", "comment", "created_at"]],
                      use_container_width=True, hide_index=True)
