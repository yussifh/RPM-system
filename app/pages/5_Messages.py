"""
5_Messages.py
--------------
Messaging system for the RPM platform.

- Patients can message their assigned doctor with symptoms, questions,
  or general health updates.
- Doctors can reply to patients and send messages to any of their patients.
- Unread message count shown in the page title.
- Auto-sends a message to the doctor when a patient submits vitals
  with symptoms (triggered from monitoring_service).
"""

import streamlit as st
from datetime import datetime

from app.core.security import SessionManager
from app.database.repositories.message_repository import MessageRepository
from app.database.repositories.patient_repository import PatientRepository
from app.database.repositories.doctor_repository import DoctorRepository
from app.database.repositories.user_repository import UserRepository
from app.utils.custom_css import apply_theme, profile_widget, notification_bell

# ── Session check ────────────────────────────────────────────────
user = SessionManager.get_current_user()
if not user:
    st.set_page_config(page_title="Messages", page_icon="✉️", layout="wide")
    st.warning("Please log in first.")
    st.stop()

role = user["role"]

msg_repo = MessageRepository()
patient_repo = PatientRepository()
doctor_repo = DoctorRepository()
user_repo = UserRepository()

# ── Unread count for badge ───────────────────────────────────────
unread = msg_repo.count_unread(user["id"])
badge = f" ({unread} unread)" if unread > 0 else ""

st.set_page_config(page_title=f"Messages{badge}", page_icon="✉️", layout="wide")
apply_theme()
profile_widget(user)
notification_bell(user)

st.markdown(page_header("✉️", "Messages", f"Your secure inbox with your care team.{badge}"), unsafe_allow_html=True)

if unread > 0:
    st.info(f"📬 You have **{unread} unread message(s)**.")

# ================================================================
# PATIENT VIEW
# ================================================================
if role == "patient":
    compose_tab, inbox_tab, sent_tab = st.tabs(["✍️ Send Message", "📥 Inbox", "📤 Sent"])

    # ── Get assigned doctor ──────────────────────────────────────
    patient = patient_repo.get_by_user_id(user["id"])
    if not patient or not patient.assigned_doctor_id:
        st.warning("You have no assigned doctor yet. Please contact the admin.")
        st.stop()

    doctor_user = user_repo.get_by_id(patient.assigned_doctor_id)

    # ── TAB 1: Compose ───────────────────────────────────────────
    with compose_tab:
        st.subheader(f"Send Message to Dr. {doctor_user.full_name}")
        st.caption("You can share your symptoms, ask questions, or send health updates.")

        # Quick symptom templates
        st.markdown("**Quick Templates:**")
        t1, t2, t3, t4 = st.columns(4)
        template = ""
        if t1.button("🤒 Fever"):
            template = "I have been experiencing fever with temperature above 37.5°C."
        if t2.button("😵 Dizziness"):
            template = "I have been feeling dizzy and lightheaded, especially when standing up."
        if t3.button("💊 Medication"):
            template = "I have a question about my current medication and dosage."
        if t4.button("📊 Check-in"):
            template = "I am doing my regular check-in. My recent readings are attached."

        with st.form("compose_form", clear_on_submit=True):
            subject = st.text_input("Subject",
                                     value="Symptom Report" if template else "",
                                     placeholder="e.g. Symptom Report, Question about medication")
            body = st.text_area("Message", value=template,
                                 placeholder="Describe your symptoms or question here...",
                                 height=180)
            if st.form_submit_button("📤 Send Message", width="stretch"):
                if not subject.strip() or not body.strip():
                    st.error("Please fill in both subject and message.")
                else:
                    msg_repo.send(
                        sender_id=user["id"],
                        receiver_id=patient.assigned_doctor_id,
                        subject=subject.strip(),
                        body=body.strip(),
                    )
                    st.success(f"✅ Message sent to Dr. {doctor_user.full_name}!")
                    st.balloons()

    # ── TAB 2: Inbox ─────────────────────────────────────────────
    with inbox_tab:
        st.subheader("📥 Messages from Your Doctor")
        inbox = msg_repo.get_inbox(user["id"])

        if not inbox:
            st.info("No messages yet. Your doctor's replies will appear here.")
        else:
            for msg in inbox:
                is_unread = not msg.is_read
                with st.container(border=True):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        prefix = "🔵 " if is_unread else ""
                        st.markdown(f"{prefix}**{msg.subject}**")
                        st.caption(f"From: Dr. {msg.sender_name} | {msg.sent_at}")
                        with st.expander("Read message"):
                            st.write(msg.body)
                            if is_unread:
                                if st.button("✅ Mark as read", key=f"read_inbox_{msg.id}"):
                                    msg_repo.mark_as_read(msg.id, user["id"])
                                    st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_inbox_{msg.id}", help="Delete"):
                            msg_repo.delete(msg.id, user["id"])
                            st.rerun()

    # ── TAB 3: Sent ──────────────────────────────────────────────
    with sent_tab:
        st.subheader("📤 Messages You Sent")
        sent = msg_repo.get_sent(user["id"])

        if not sent:
            st.info("No sent messages yet.")
        else:
            for msg in sent:
                with st.container(border=True):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"**{msg.subject}**")
                        st.caption(f"To: Dr. {msg.receiver_name} | {msg.sent_at}")
                        with st.expander("View message"):
                            st.write(msg.body)
                    with col2:
                        if st.button("🗑️", key=f"del_sent_{msg.id}", help="Delete"):
                            msg_repo.delete(msg.id, user["id"])
                            st.rerun()


# ================================================================
# DOCTOR VIEW
# ================================================================
elif role == "doctor":
    inbox_tab, compose_tab, sent_tab = st.tabs(["📥 Inbox", "✍️ Send Message", "📤 Sent"])

    # ── Get assigned patients ────────────────────────────────────
    from app.services.doctor_service import DoctorService
    doctor_service = DoctorService()
    patients = doctor_service.get_assigned_patients(user["id"])
    patient_map = {
        (p.full_name or f"Patient #{p.user_id}"): p.user_id
        for p in patients
    }

    # ── TAB 1: Inbox ─────────────────────────────────────────────
    with inbox_tab:
        st.subheader("📥 Messages from Patients")
        inbox = msg_repo.get_inbox(user["id"])

        if not inbox:
            st.success("✅ Inbox is empty — no patient messages.")
        else:
            # Group by sender
            senders = {}
            for msg in inbox:
                name = msg.sender_name or "Unknown"
                if name not in senders:
                    senders[name] = []
                senders[name].append(msg)

            for sender_name, messages in senders.items():
                unread_count = sum(1 for m in messages if not m.is_read)
                badge_txt = f" 🔵 {unread_count} new" if unread_count else ""
                with st.expander(f"👤 {sender_name}{badge_txt} ({len(messages)} messages)"):
                    for msg in messages:
                        is_unread = not msg.is_read
                        with st.container(border=True):
                            prefix = "🔵 " if is_unread else ""
                            st.markdown(f"{prefix}**{msg.subject}**")
                            st.caption(f"Sent: {msg.sent_at}")
                            st.write(msg.body)

                            if is_unread:
                                if st.button("✅ Mark as read", key=f"read_doc_{msg.id}"):
                                    msg_repo.mark_as_read(msg.id, user["id"])
                                    st.rerun()

                            # Quick reply
                            with st.form(f"reply_{msg.id}"):
                                reply_text = st.text_area("Quick Reply",
                                                           placeholder="Type your reply here...",
                                                           key=f"reply_text_{msg.id}")
                                if st.form_submit_button("📤 Send Reply"):
                                    if reply_text.strip():
                                        msg_repo.send(
                                            sender_id=user["id"],
                                            receiver_id=msg.sender_id,
                                            subject=f"Re: {msg.subject}",
                                            body=reply_text.strip(),
                                        )
                                        st.success(f"✅ Reply sent to {sender_name}!")
                                        st.rerun()

                            col1, col2 = st.columns([1, 5])
                            with col1:
                                if st.button("🗑️ Delete", key=f"del_{msg.id}"):
                                    msg_repo.delete(msg.id, user["id"])
                                    st.rerun()

    # ── TAB 2: Compose ───────────────────────────────────────────
    with compose_tab:
        st.subheader("✍️ Send Message to a Patient")

        if not patients:
            st.info("No patients assigned to you yet.")
        else:
            # Quick message templates for doctors
            st.caption("Quick templates:")
            tc1, tc2, tc3 = st.columns(3)
            template_body = ""
            if tc1.button("📋 Follow-Up"):
                template_body = "This is a follow-up on your recent readings. Please contact me if you have any concerns."
            if tc2.button("💊 Medication Reminder"):
                template_body = "Please remember to take your medications as prescribed and report any side effects."
            if tc3.button("🏥 Appointment"):
                template_body = "Please confirm your upcoming appointment and arrive on time."

            with st.form("doctor_compose_form", clear_on_submit=True):
                selected_patient = st.selectbox("Select Patient", list(patient_map.keys()))
                subject = st.text_input("Subject",
                                         placeholder="e.g. Medication reminder, Appointment, Test results")

                body = st.text_area("Message", value=template_body,
                                     placeholder="Type your message to the patient here...",
                                     height=180)

                # Urgency level
                urgency = st.selectbox("Urgency", ["Normal", "Important", "Urgent"])
                urgency_prefix = {"Normal": "", "Important": "⚠️ IMPORTANT: ", "Urgent": "🚨 URGENT: "}

                if st.form_submit_button("📤 Send Message", width="stretch"):
                    if not subject.strip() or not body.strip():
                        st.error("Please fill in both subject and message.")
                    else:
                        final_body = urgency_prefix[urgency] + body.strip()
                        msg_repo.send(
                            sender_id=user["id"],
                            receiver_id=patient_map[selected_patient],
                            subject=subject.strip(),
                            body=final_body,
                        )
                        st.success(f"✅ Message sent to {selected_patient}!")
                        st.balloons()

    # ── TAB 3: Sent ──────────────────────────────────────────────
    with sent_tab:
        st.subheader("📤 Messages You Sent")
        sent = msg_repo.get_sent(user["id"])

        if not sent:
            st.info("No sent messages yet.")
        else:
            for msg in sent:
                with st.container(border=True):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f"**{msg.subject}**")
                        st.caption(f"To: {msg.receiver_name} | {msg.sent_at}")
                        with st.expander("View message"):
                            st.write(msg.body)
                    with col2:
                        if st.button("🗑️", key=f"del_sent_{msg.id}", help="Delete"):
                            msg_repo.delete(msg.id, user["id"])
                            st.rerun()


# ================================================================
# ADMIN VIEW
# ================================================================
elif role == "admin":
    st.subheader("📊 System Messages Overview")
    st.info("As an admin you can view system stats. Direct messaging is between patients and doctors.")

    all_inbox = msg_repo.get_inbox(user["id"])
    st.metric("Your Inbox", len(all_inbox))


else:
    st.error("Access denied.")

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
