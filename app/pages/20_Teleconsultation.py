"""
20_Teleconsultation.py — Video call room management for doctor-patient sessions.
Real meetings run on Jitsi Meet (meet.jit.si) embedded in the page. Both
participants join the same room; they must be on the same network as the app.
"""
import json
import streamlit as st
from app.utils.custom_css import apply_theme, profile_widget, notification_bell, page_header, theme_tokens, material_icon
from app.core.security import SessionManager
from app.database.repositories.teleconsultation_repository import TeleconsultationRepository
from app.database.repositories.patient_repository import PatientRepository

st.set_page_config(page_title="RPM — Teleconsultation", page_icon=":material/videocam:", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.switch_page("pages/1_Login.py")
    st.stop()

profile_widget(user)
notification_bell(user)

t = theme_tokens()
tele_repo = TeleconsultationRepository()
patient_repo = PatientRepository()

st.markdown(page_header(":material/videocam:", "Teleconsultation", "Secure video sessions with your care team."), unsafe_allow_html=True)


# ── Small helpers ───────────────────────────────────────────────────
def _initials(name: str) -> str:
    parts = [p for p in str(name or "").split() if p]
    return "".join(p[0].upper() for p in parts[:2]) or "?"


def _fmt_dt(value) -> str:
    if value is None:
        return ""
    try:
        return value.strftime("%d %b %Y, %H:%M")
    except Exception:
        return str(value)


def _status_badge(status: str) -> str:
    styles = {
        "scheduled":   (t["amber"], t["tint_amber"], "schedule"),
        "in_progress": (t["pulse"], t["tint_primary"], "pulse_dot"),
        "completed":   (t["info"],  t["tint_info"], "check_circle"),
        "cancelled":   (t["alert"], t["tint_alert"], "cancel"),
    }
    color, bg, icon = styles.get(status, (t["muted"], t["surface"], "circle"))
    icon_html = (
        f'<span class="material-symbols-outlined" style="font-size:13px;vertical-align:-2px;">{icon}</span>'
        if icon != "pulse_dot"
        else f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:{color};'
             f'box-shadow:0 0 0 0 {color};animation:vpulse 2.4s infinite;"></span>'
    )
    return (f'<span style="background:{bg};color:{color};padding:4px 12px;border-radius:20px;'
            f'font-size:11px;font-weight:700;display:inline-flex;align-items:center;gap:6px;">'
            f'{icon_html}{status.replace("_", " ").upper()}</span>')


def _room_chip(room_id: str) -> str:
    return (f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:{t["muted"]};'
            f'background:{t["tint_info"]};padding:2px 10px;border-radius:8px;">'
            f'<span class="material-symbols-outlined" style="font-size:12px;vertical-align:-2px;">vpn_key</span> '
            f'{room_id}</span>')


def _how_it_works():
    steps = [
        ("video_call", "1 · Invite", "A doctor creates the session or your doctor invites you to join."),
        ("vpn_key", "2 · Secure room", "Both of you enter the same private Jitsi room (meet.jit.si)."),
        ("forum", "3 · Talk live", "Video call, chat and clinical notes — all in one place."),
    ]
    cols = st.columns(3)
    for col, (icon, title, desc) in zip(cols, steps):
        col.markdown(f"""
        <div style="background:{t['surface']};border:1px solid {t['border']};border-radius:14px;
             padding:16px;height:100%;">
            <span class="material-symbols-outlined" style="font-size:24px;color:{t['primary']};">{icon}</span>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:13px;
                 color:{t['ink']};margin:8px 0 6px;">{title}</div>
            <p style="font-size:12px;color:{t['muted']};line-height:1.6;margin:0;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)


def _session_card(name: str, subtitle_html: str, status: str, created: str = "") -> str:
    return f"""
    <div style="background:{t['surface']};border:1px solid {t['border']};border-radius:14px;
         padding:18px 20px;margin-bottom:12px;">
        <div style="display:flex;align-items:center;gap:14px;">
            <div style="width:46px;height:46px;border-radius:50%;background:{t['tint_primary']};
                 color:{t['primary']};display:flex;align-items:center;justify-content:center;
                 font-weight:800;font-family:'JetBrains Mono',monospace;flex-shrink:0;">{_initials(name)}</div>
            <div style="flex:1;min-width:0;">
                <div style="font-size:15px;font-weight:700;color:{t['ink']};">{name}</div>
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:5px;">
                    {subtitle_html}
                    {f'<span style="font-size:11px;color:{t["muted"]};">· {created}</span>' if created else ''}
                </div>
            </div>
            <div style="flex-shrink:0;">{_status_badge(status)}</div>
        </div>
    </div>
    """


def _call_panel(s: dict, display_name: str, peer: str):
    """Live call: header strip + embedded Jitsi room + notes/end controls."""
    live_label = "LIVE" if s["status"] == "in_progress" else "READY"
    st.markdown(f"""
    <div style="background:{t['surface']};border:1px solid {t['border']};border-radius:14px;
         overflow:hidden;margin-top:4px;">
        <div style="background:linear-gradient(90deg,{t['primary']} 0%,{t['sidebar']} 100%);
             padding:12px 18px;display:flex;align-items:center;gap:12px;">
            <div style="width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,0.18);
                 color:white;display:flex;align-items:center;justify-content:center;
                 font-weight:800;font-family:'JetBrains Mono',monospace;font-size:13px;">{_initials(peer)}</div>
            <div style="flex:1;min-width:0;color:white;">
                <div style="font-size:14px;font-weight:700;">Live session with {peer}</div>
                <div style="font-size:11px;opacity:.75;">Room <span style="font-family:'JetBrains Mono',monospace;">{s['room_id']}</span>
                     · camera starts off</div>
            </div>
            <span style="background:rgba(255,255,255,0.16);color:white;padding:4px 12px;border-radius:20px;
                 font-size:11px;font-weight:700;">{live_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.iframe(jitsi_meeting_html(s["room_id"], display_name, height=520))


def jitsi_meeting_html(room_id: str, display_name: str, height: int = 520) -> str:
    """HTML that embeds a live Jitsi Meet room for this teleconsultation."""
    return f"""
    <div id="meet" style="width:100%;"></div>
    <script src="https://meet.jit.si/external_api.js"></script>
    <script>
      (function () {{
        var domain = "meet.jit.si";
        var options = {{
          roomName: {json.dumps(room_id)},
          width: "100%",
          height: {height},
          parentNode: document.querySelector("#meet"),
          userInfo: {{ displayName: {json.dumps(display_name)} }},
          configOverwrite: {{
            prejoinPageEnabled: false,
            startWithAudioMuted: false,
            startWithVideoMuted: true,
            disableDeepLinking: true,
            enableClosePage: false
          }},
          interfaceConfigOverwrite: {{
            SHOW_JITSI_WATERMARK: false,
            SHOW_WATERMARK_FOR_GUESTS: false,
            TOOLBAR_BUTTONS: ["microphone","camera","desktop","fullscreen","hangup","chat","raisehand","tileview"]
          }}
        }};
        new JitsiMeetExternalAPI(domain, options);
      }})();
    </script>
    """


_how_it_works()

role = user["role"]

# ================================================================
# DOCTOR VIEW
# ================================================================
if role == "doctor":
    active = tele_repo.list_active_for_doctor(user["id"])
    history = tele_repo.list_for_doctor(user["id"])

    tab1, tab2, tab3 = st.tabs([":material/videocam: Active Sessions", ":material/edit_calendar: Start New", ":material/history: History"])

    with tab1:
        if not active:
            st.info("No active teleconsultation sessions. Start one from the **Start New** tab.", icon=":material/videocam:")
        else:
            for s in active:
                st.markdown(_session_card(
                    s["patient_name"],
                    _room_chip(s["room_id"]),
                    s["status"],
                    _fmt_dt(s.get("created_at")),
                ), unsafe_allow_html=True)

                if s["status"] == "scheduled":
                    if st.button(f":material/play_arrow: Start Call",
                                 key=f"start_{s['id']}", width="stretch"):
                        tele_repo.update_status(s["id"], "in_progress")
                        st.rerun()
                elif s["status"] == "in_progress":
                    _call_panel(s, user["full_name"], s["patient_name"])
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown("**Session notes**")
                        notes = st.text_area("Add clinical notes",
                                             key=f"notes_{s['id']}",
                                             value=s.get("notes") or "",
                                             height=130,
                                             placeholder="e.g. Blood pressure stable, follow-up in 2 weeks…")
                        if st.button(":material/save: Save Notes", key=f"save_{s['id']}", type="primary"):
                            tele_repo.update_notes(s["id"], notes)
                            st.success("Notes saved.")
                    with col2:
                        st.markdown("**End the call**")
                        if st.button(":material/stop: End Call", key=f"end_{s['id']}",
                                     use_container_width=True):
                            tele_repo.update_status(s["id"], "completed")
                            st.success("Call ended and recorded.")
                            st.rerun()

    with tab2:
        st.markdown(f"""
        <div style="background:{t['surface']};border:1px solid {t['border']};border-radius:14px;
             padding:20px;margin-bottom:8px;">
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:16px;color:{t['ink']};">
                Start a new teleconsultation</div>
            <p style="font-size:12px;color:{t['muted']};margin:4px 0 0;">Pick a patient — a secure video room is
                created instantly and the patient gets an active session to join.</p>
        </div>
        """, unsafe_allow_html=True)

        try:
            patients = patient_repo.list_by_doctor(user["id"])
        except Exception:
            patients = []

        if not patients:
            st.info("No patients assigned. Assign patients from the patient dashboard first.", icon=":material/groups:")
        else:
            patient_names = {f"{p.full_name} ({p.email})": p.user_id for p in patients}
            chosen = st.selectbox("Select Patient", list(patient_names.keys()))
            if st.button(":material/video_call: Create & Start Session", width="stretch", type="primary"):
                pid = patient_names[chosen]
                tele_id = tele_repo.create(patient_user_id=pid, doctor_user_id=user["id"])
                tele_repo.update_status(tele_id, "in_progress")
                st.success("Teleconsultation session started — the patient can now join the room.")
                st.balloons()
                st.rerun()

    with tab3:
        if not history:
            st.info("No teleconsultation history yet.")
        else:
            st.caption(f"{len(history)} past session(s)")
            for s in history:
                st.markdown(_session_card(
                    s["patient_name"],
                    _room_chip(s["room_id"]),
                    s["status"],
                    _fmt_dt(s.get("created_at")),
                ), unsafe_allow_html=True)

# ================================================================
# PATIENT VIEW
# ================================================================
elif role == "patient":
    active = tele_repo.list_active_for_patient(user["id"])
    history = tele_repo.list_for_patient(user["id"])

    tab1, tab2 = st.tabs([":material/videocam: Active Sessions", ":material/history: History"])

    with tab1:
        if not active:
            st.info("No active teleconsultation sessions. Your doctor will create one when needed.", icon=":material/videocam:")
        else:
            for s in active:
                st.markdown(_session_card(
                    f"Dr. {s['doctor_name']}",
                    _room_chip(s["room_id"]),
                    s["status"],
                    _fmt_dt(s.get("created_at")),
                ), unsafe_allow_html=True)

                if s["status"] == "scheduled":
                    if st.button(f":material/check_circle: Join Call",
                                 key=f"join_{s['id']}", width="stretch", type="primary"):
                        tele_repo.update_status(s["id"], "in_progress")
                        st.rerun()

                if s["status"] == "in_progress":
                    _call_panel(s, user["full_name"], f"Dr. {s['doctor_name']}")
                    st.caption("You can turn your camera on when you're ready. Your doctor can also get your vitals "
                               "while you talk — stay on the same Wi-Fi network as your doctor for the best connection.")

    with tab2:
        if not history:
            st.info("No teleconsultation history yet.")
        else:
            st.caption(f"{len(history)} past session(s)")
            for s in history:
                st.markdown(_session_card(
                    f"Dr. {s['doctor_name']}",
                    _room_chip(s["room_id"]),
                    s["status"],
                    _fmt_dt(s.get("created_at")),
                ), unsafe_allow_html=True)

# ================================================================
# ADMIN VIEW
# ================================================================
elif role == "admin":
    history = tele_repo.list_all()
    total = tele_repo.count_all()
    active_count = sum(1 for s in history if s["status"] in ("scheduled", "in_progress"))
    completed = sum(1 for s in history if s["status"] == "completed")

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Sessions", total)
    m2.metric("Active / Scheduled", active_count)
    m3.metric("Completed", completed)

    st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader(":material/clipboard: All Teleconsultation Sessions")
        if not history:
            st.info("No teleconsultation sessions yet.")
        else:
            st.dataframe([{
                "Patient": s.get("patient_name"),
                "Doctor": s.get("doctor_name"),
                "Room": s["room_id"],
                "Status": s["status"].title(),
                "Started": s.get("started_at"),
                "Ended": s.get("ended_at"),
                "Created": s.get("created_at"),
            } for s in history], width="stretch")