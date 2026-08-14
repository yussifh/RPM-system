"""
17_Chat_History.py
------------------
Full chat history view between doctors and patients.
Shows complete conversation thread with timestamps.
"""

import streamlit as st
from datetime import datetime

from app.core.security import SessionManager
from app.database.repositories.message_repository import MessageRepository
from app.database.repositories.user_repository import UserRepository
from app.utils.custom_css import apply_theme, profile_widget, notification_bell

st.set_page_config(page_title="Chat History", page_icon="💬", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.warning("Please log in first.")
    st.stop()

profile_widget(user)
notification_bell(user)

st.title("💬 Chat History")
st.caption("View your full conversation thread.")

msg_repo = MessageRepository()
user_repo = UserRepository()

# ── Doctor View ──────────────────────────────────────────────────
if user["role"] == "doctor":
    from app.services.doctor_service import DoctorService
    patients = DoctorService().get_assigned_patients(user["id"])
    patient_map = {p.full_name: p.user_id for p in patients}

    if not patients:
        st.info("No patients assigned to you yet.")
    else:
        selected = st.selectbox("Select Patient to View Chat", list(patient_map.keys()))
        other_id = patient_map[selected]
        other_name = selected

        conversation = msg_repo.get_conversation(user["id"], other_id)

        if not conversation:
            st.info(f"No messages with {other_name} yet.")
        else:
            st.markdown(f"#### Conversation with {other_name} ({len(conversation)} messages)")
            st.markdown("---")

            for msg in conversation:
                is_sent = msg.sender_id == user["id"]
                sender_name = "You" if is_sent else other_name
                bg = "#E7F4EF" if is_sent else "#EFF3F1"
                align = "right" if is_sent else "left"
                border = "#0E7A5C" if is_sent else "#DCE5E1"

                read_status = "👁️ Read" if msg.is_read else "📩 Delivered"

                st.markdown(f"""
                <div style="background:{bg};border:1px solid {border};border-radius:10px;
                     padding:12px 16px;margin:8px 0;max-width:80%;float:{align};">
                    <div style="font-weight:600;font-size:13px;color:#333;">{sender_name}</div>
                    <div style="font-size:12px;color:#888;margin-bottom:6px;">
                        {msg.sent_at.strftime('%d %b %Y, %I:%M %p') if msg.sent_at else ''} • {read_status}
                    </div>
                    <div style="font-weight:600;color:#0E7A5C;margin-bottom:4px;">{msg.subject or ''}</div>
                    <div style="font-size:13px;color:#333;white-space:pre-wrap;">{msg.body or ''}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='clear:both;'></div>", unsafe_allow_html=True)

# ── Patient View ─────────────────────────────────────────────────
elif user["role"] == "patient":
    from app.database.repositories.patient_repository import PatientRepository
    patient_repo = PatientRepository()
    patient = patient_repo.get_by_user_id(user["id"])

    if not patient or not patient.assigned_doctor_id:
        st.info("You don't have an assigned doctor yet.")
    else:
        doctor = user_repo.get_by_id(patient.assigned_doctor_id)
        other_name = f"Dr. {doctor.full_name}" if doctor else "Your Doctor"
        other_id = patient.assigned_doctor_id

        conversation = msg_repo.get_conversation(user["id"], other_id)

        if not conversation:
            st.info(f"No messages with {other_name} yet.")
        else:
            st.markdown(f"#### Conversation with {other_name} ({len(conversation)} messages)")
            st.markdown("---")

            for msg in conversation:
                is_sent = msg.sender_id == user["id"]
                sender_name = "You" if is_sent else other_name
                bg = "#E7F4EF" if is_sent else "#EFF3F1"
                align = "right" if is_sent else "left"
                border = "#0E7A5C" if is_sent else "#DCE5E1"

                st.markdown(f"""
                <div style="background:{bg};border:1px solid {border};border-radius:10px;
                     padding:12px 16px;margin:8px 0;max-width:80%;float:{align};">
                    <div style="font-weight:600;font-size:13px;color:#333;">{sender_name}</div>
                    <div style="font-size:12px;color:#888;margin-bottom:6px;">
                        {msg.sent_at.strftime('%d %b %Y, %I:%M %p') if msg.sent_at else ''}
                    </div>
                    <div style="font-weight:600;color:#0E7A5C;margin-bottom:4px;">{msg.subject or ''}</div>
                    <div style="font-size:13px;color:#333;white-space:pre-wrap;">{msg.body or ''}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='clear:both;'></div>", unsafe_allow_html=True)

else:
    st.error("Access denied.")

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
