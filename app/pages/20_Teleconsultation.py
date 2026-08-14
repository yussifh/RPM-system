"""
20_Teleconsultation.py — Video call room management for doctor-patient sessions.
Real meetings run on Jitsi Meet (meet.jit.si) embedded in the page. Both
participants join the same room; they must be on the same network as the app.
"""
import json
import streamlit as st
from app.utils.custom_css import apply_theme, profile_widget, notification_bell
from app.core.security import SessionManager
from app.database.repositories.teleconsultation_repository import TeleconsultationRepository
from app.database.repositories.patient_repository import PatientRepository

st.set_page_config(page_title="RPM — Teleconsultation", page_icon="📹", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.switch_page("pages/1_Login.py")
    st.stop()

profile_widget(user)
notification_bell(user)

tele_repo = TeleconsultationRepository()
patient_repo = PatientRepository()

st.markdown("## 📹 Teleconsultation")


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
            startWithVideoMuted: false,
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


def embed_call(s: dict, display_name: str):
    st.markdown("#### 🔴 Live call")
    st.caption(f"Room **{s['room_id']}** — allow camera/microphone when the browser asks. "
               "The other participant must open the same session on another device (same Wi-Fi).")
    st.components.v1.html(jitsi_meeting_html(s["room_id"], display_name), height=520, scrolling=False)


role = user["role"]

if role == "doctor":
    active = tele_repo.list_active_for_doctor(user["id"])
    history = tele_repo.list_for_doctor(user["id"])

    tab1, tab2, tab3 = st.tabs(["📹 Active Sessions", "📋 Start New", "📜 History"])

    with tab1:
        if not active:
            st.info("No active teleconsultation sessions.")
        else:
            for s in active:
                status_color = "#0E7A5C" if s["status"] == "in_progress" else "#B8761D"
                st.markdown(f"""
                <div style="background:white;border:1px solid #DCE5E1;border-radius:10px;padding:16px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-weight:700;color:#16242B;font-size:14px;">{s['patient_name']}</div>
                            <div style="font-size:11px;color:#5F717A;">Room: {s['room_id']}</div>
                        </div>
                        <span style="background:{status_color};color:white;padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;">{s['status'].upper()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if s["status"] == "scheduled":
                    if st.button(f"▶️ Start Call", key=f"start_{s['id']}"):
                        tele_repo.update_status(s["id"], "in_progress")
                        st.rerun()
                elif s["status"] == "in_progress":
                    embed_call(s, f"Dr. {user['full_name']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Session Notes**")
                        notes = st.text_area("Add clinical notes", key=f"notes_{s['id']}",
                                             value=s.get("notes") or "", height=150)
                        if st.button("💾 Save Notes", key=f"save_{s['id']}"):
                            tele_repo.update_notes(s["id"], notes)
                            st.success("Notes saved.")
                    with col2:
                        if st.button("⏹️ End Call", key=f"end_{s['id']}"):
                            tele_repo.update_status(s["id"], "completed")
                            st.success("Call ended.")
                            st.rerun()

    with tab2:
        st.markdown("### Start New Teleconsultation")
        try:
            patients = patient_repo.list_by_doctor(user["id"])
        except Exception:
            patients = []

        if not patients:
            st.info("No patients assigned.")
        else:
            patient_names = {f"{p.full_name} ({p.email})": p.user_id for p in patients}
            chosen = st.selectbox("Select Patient", list(patient_names.keys()))
            if st.button("📹 Create & Start Session", use_container_width=True):
                pid = patient_names[chosen]
                tele_id = tele_repo.create(patient_user_id=pid, doctor_user_id=user["id"])
                tele_repo.update_status(tele_id, "in_progress")
                st.success("Teleconsultation session started!")
                st.rerun()

    with tab3:
        if not history:
            st.info("No teleconsultation history.")
        else:
            for s in history:
                status_color = {"completed": "#0E7A5C", "cancelled": "#C73E3A",
                                "in_progress": "#2A6A9B", "scheduled": "#B8761D"
                               }.get(s["status"], "#5F717A")
                st.markdown(f"""
                <div style="background:white;border:1px solid #DCE5E1;border-radius:10px;padding:12px;margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-weight:600;color:#16242B;">{s['patient_name']}</span>
                            <span style="font-size:11px;color:#5F717A;margin-left:8px;">{s['room_id']}</span>
                        </div>
                        <span style="background:{status_color};color:white;padding:3px 10px;border-radius:10px;font-size:11px;">{s['status'].upper()}</span>
                    </div>
                    <div style="font-size:11px;color:#5F717A;margin-top:4px;">{s['created_at'].strftime('%Y-%m-%d %H:%M') if s['created_at'] else ''}</div>
                </div>
                """, unsafe_allow_html=True)

elif role == "patient":
    active = tele_repo.list_active_for_patient(user["id"])
    history = tele_repo.list_for_patient(user["id"])

    tab1, tab2 = st.tabs(["📹 Active Sessions", "📜 History"])

    with tab1:
        if not active:
            st.info("No active teleconsultation sessions.")
        else:
            for s in active:
                st.markdown(f"""
                <div style="background:white;border:1px solid #DCE5E1;border-radius:10px;padding:16px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-weight:700;color:#16242B;font-size:14px;">Dr. {s['doctor_name']}</div>
                            <div style="font-size:11px;color:#5F717A;">Room: {s['room_id']}</div>
                        </div>
                        <span style="background:#0E7A5C;color:white;padding:4px 12px;border-radius:12px;font-size:11px;font-weight:600;">{s['status'].upper()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if s["status"] == "scheduled":
                    if st.button("✅ Join Call", key=f"join_{s['id']}"):
                        tele_repo.update_status(s["id"], "in_progress")
                        st.rerun()

                if s["status"] == "in_progress":
                    embed_call(s, user["full_name"])

    with tab2:
        if not history:
            st.info("No teleconsultation history.")
        else:
            for s in history:
                status_color = {"completed": "#0E7A5C", "cancelled": "#C73E3A",
                                "in_progress": "#2A6A9B", "scheduled": "#B8761D"
                               }.get(s["status"], "#5F717A")
                st.markdown(f"""
                <div style="background:white;border:1px solid #DCE5E1;border-radius:10px;padding:12px;margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-weight:600;color:#16242B;">Dr. {s['doctor_name']}</span>
                            <span style="font-size:11px;color:#5F717A;margin-left:8px;">{s['room_id']}</span>
                        </div>
                        <span style="background:{status_color};color:white;padding:3px 10px;border-radius:10px;font-size:11px;">{s['status'].upper()}</span>
                    </div>
                    <div style="font-size:11px;color:#5F717A;margin-top:4px;">{s['created_at'].strftime('%Y-%m-%d %H:%M') if s['created_at'] else ''}</div>
                </div>
                """, unsafe_allow_html=True)

elif role == "admin":
    history = tele_repo.list_for_doctor(None)
    st.metric("Total Sessions", tele_repo.count_all())
    st.markdown("---")
    st.info("Admin view: Use the sidebar to navigate to specific doctor dashboards for session details.")
