"""
18_Notifications.py
-------------------
System notifications center showing all alerts, appointments,
messages, and emergency notifications in one place.
"""

import streamlit as st
from datetime import datetime

from app.core.security import SessionManager
from app.database.repositories.alert_repository import AlertRepository
from app.database.repositories.message_repository import MessageRepository
from app.database.repositories.appointment_repository import AppointmentRepository
from app.utils.custom_css import apply_theme, profile_widget, notification_bell

st.set_page_config(page_title="Notifications", page_icon="🔔", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.warning("Please log in first.")
    st.stop()

profile_widget(user)
notification_bell(user)

st.title("🔔 Notifications")
st.caption("All your alerts, messages, and updates in one place.")

alert_repo = AlertRepository()
msg_repo = MessageRepository()
appt_repo = AppointmentRepository()

role = user["role"]
user_id = user["id"]

# ── Collect all notifications ────────────────────────────────────
notifications = []

# Unread messages
if role == "doctor":
    inbox = msg_repo.get_inbox(user_id)
    unread = [m for m in inbox if not m.is_read]
    for m in unread:
        notifications.append({
            "type": "message",
            "icon": "💬",
            "title": f"New message from {m.sender_name or 'Unknown'}",
            "detail": m.subject or "No subject",
            "time": m.sent_at,
            "color": "#2A6A9B",
            "priority": 1,
        })

elif role == "patient":
    inbox = msg_repo.get_inbox(user_id)
    unread = [m for m in inbox if not m.is_read]
    for m in unread:
        notifications.append({
            "type": "message",
            "icon": "💬",
            "title": f"New message from {m.sender_name or 'Doctor'}",
            "detail": m.subject or "No subject",
            "time": m.sent_at,
            "color": "#2A6A9B",
            "priority": 1,
        })

# Open alerts (doctor only)
if role == "doctor":
    open_alerts = alert_repo.list_open_for_doctor(user_id)
    for a in open_alerts:
        sev_icon = {"critical": "🚨", "high": "⚠️", "medium": "📋", "low": "✅"}.get(a["severity"], "📋")
        notifications.append({
            "type": "alert",
            "icon": sev_icon,
            "title": f"{a['severity'].upper()} Alert — {a.get('patient_name', 'Patient')}",
            "detail": a["message"][:100] if a["message"] else "No details",
            "time": a["created_at"],
            "color": "#C73E3A" if a["severity"] in ("critical", "high") else "#B8761D",
            "priority": 0 if a["severity"] == "critical" else 1,
        })

# Upcoming appointments
if role == "doctor":
    upcoming = appt_repo.get_for_doctor(user_id, upcoming_only=True)
elif role == "patient":
    upcoming = appt_repo.get_for_patient(user_id, upcoming_only=True)
else:
    upcoming = []

for a in upcoming:
    notifications.append({
        "type": "appointment",
        "icon": "📅",
        "title": f"Upcoming appointment on {a.appointment_date}",
        "detail": f"With {'Dr. ' + a.doctor_name if role == 'patient' else a.patient_name} at {a.location}",
        "time": datetime.combine(a.appointment_date, a.appointment_time) if a.appointment_date and a.appointment_time else None,
        "color": "#0E7A5C",
        "priority": 2,
    })

# Sort by priority then time
notifications.sort(key=lambda n: (n["priority"], n["time"] or datetime.min), reverse=True)

# ── Display ──────────────────────────────────────────────────────
if not notifications:
    st.success("✅ You're all caught up! No new notifications.")
else:
    st.markdown(f"**{len(notifications)} notification(s)**")
    st.markdown("---")

    for n in notifications:
        with st.container(border=True):
            col1, col2 = st.columns([1, 6])
            with col1:
                st.markdown(f"<div style='font-size:32px;text-align:center;'>{n['icon']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{n['title']}**")
                st.caption(n["detail"])
                if n["time"]:
                    st.caption(f"📅 {n['time'].strftime('%d %b %Y, %I:%M %p') if isinstance(n['time'], datetime) else n['time']}")

            # Mark as read button for messages
            if n["type"] == "message" and role in ("doctor", "patient"):
                if st.button("Mark as Read", key=f"read_{n['time']}"):
                    st.rerun()

    # Mark all as read
    if role in ("doctor", "patient"):
        st.markdown("---")
        if st.button("✅ Mark All Messages as Read", use_container_width=True):
            for m in unread:
                msg_repo.mark_as_read(m.id, user["id"])
            st.success("All messages marked as read.")
            st.rerun()

if st.button("Log Out"):
    SessionManager.logout()
    st.rerun()
