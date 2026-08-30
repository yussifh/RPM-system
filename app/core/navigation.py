"""
navigation.py — Role-aware sidebar navigation.

Builds the st.navigation() page list for the current signed-in role so each
user only sees the pages they are actually allowed to access (instead of the
Streamlit default of listing every file under app/pages).

Run this router from the app entrypoint (app/main.py) as the very first
Streamlit command:

    from app.core.navigation import build_navigation
    build_navigation().run()
"""

import streamlit as st

from app.core.security import SessionManager

# key -> (relative page path from the entrypoint dir, sidebar title, sidebar icon)
_PAGE_REGISTRY = {
    "home":                ("pages/0_Home.py",                "Home",               ":material/monitor_heart:"),
    "login":               ("pages/1_Login.py",               "Login",              ":material/login:"),
    "admin_dashboard":     ("pages/2_Admin_Dashboard.py",     "Admin Dashboard",    ":material/admin_panel_settings:"),
    "doctor_dashboard":    ("pages/3_Doctor_Dashboard.py",    "Doctor Dashboard",   ":material/stethoscope:"),
    "patient_dashboard":   ("pages/4_Patient_Dashboard.py",   "Patient Dashboard",  ":material/person:"),
    "messages":            ("pages/5_Messages.py",            "Messages",           ":material/mail:"),
    "appointments":        ("pages/6_Appointments.py",        "Appointments",       ":material/calendar_month:"),
    "reset":               ("pages/7_Reset_Password.py",      "Reset Password",     ":material/key:"),
    "medications":         ("pages/8_Medications.py",         "Medications",        ":material/medication:"),
    "patient_profile":     ("pages/9_Patient_Profile.py",     "Patient Profile",    ":material/person:"),
    "admin_reports":       ("pages/10_Admin_Reports.py",      "Admin Reports",      ":material/analytics:"),
    "profile_completion":  ("pages/11_Profile_Completion.py", "Profile Completion", ":material/task:"),
    "symptom_checker":     ("pages/12_AI_Symptom_Checker.py", "AI Symptom Checker", ":material/psychology:"),
    "doctor_schedule":     ("pages/13_Doctor_Schedule.py",    "Doctor Schedule",    ":material/calendar_month:"),
    "progress_report":     ("pages/14_Patient_Progress_Report.py", "Patient Progress Report", ":material/assessment:"),
    "reminders":           ("pages/15_Medication_Reminders.py", "Medication Reminders", ":material/alarm:"),
    "vitals":              ("pages/16_Vitals_Charts.py",      "Vitals Charts",      ":material/show_chart:"),
    "chat":                ("pages/17_Chat_History.py",       "Chat History",       ":material/chat:"),
    "notifications":       ("pages/18_Notifications.py",      "Notifications",      ":material/notifications:"),
    "rating":              ("pages/19_Doctor_Rating.py",      "Doctor Rating",      ":material/star:"),
    "teleconsultation":    ("pages/20_Teleconsultation.py",   "Teleconsultation",   ":material/videocam:"),
    "settings":            ("pages/21_System_Settings.py",    "System Settings",    ":material/settings:"),
    "preferences":         ("pages/22_Preferences.py",        "Preferences",        ":material/palette:"),
}

# role -> list of page keys shown in the sidebar. None = visitor (not signed in).
_ALLOWED_PAGES = {
    None: ["home", "login", "reset"],
    "patient": [
        "home", "patient_dashboard", "messages", "appointments", "medications",
        "patient_profile", "profile_completion", "symptom_checker", "progress_report",
        "reminders", "vitals", "chat", "reset", "notifications", "rating",
        "teleconsultation", "preferences",
    ],
    "doctor": [
        "home", "doctor_dashboard", "messages", "appointments", "medications",
        "symptom_checker", "doctor_schedule", "progress_report", "vitals", "chat",
        "reset", "notifications", "rating", "teleconsultation", "preferences",
    ],
    "admin": [
        "home", "admin_dashboard", "messages", "admin_reports", "progress_report",
        "vitals", "reset", "notifications", "rating", "teleconsultation", "settings",
        "preferences",
    ],
}


def build_navigation():
    """Return an st.navigation object limited to the current role's pages."""
    user = SessionManager.get_current_user()
    role = user["role"] if user else None

    keys = _ALLOWED_PAGES.get(role, _ALLOWED_PAGES[None])

    # Default landing page: role dashboard once signed in, otherwise Home.
    default_key = "home" if role is None else {
        "patient": "patient_dashboard",
        "doctor": "doctor_dashboard",
        "admin": "admin_dashboard",
    }.get(role, "home")

    pages = [
        st.Page(path, title=title, icon=icon, default=(key == default_key))
        for key in keys
        for path, title, icon in [_PAGE_REGISTRY[key]]
    ]

    return st.navigation(pages, position="sidebar", expanded=True)