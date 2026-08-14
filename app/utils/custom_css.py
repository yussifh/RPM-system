"""
custom_css.py — "The Vitals Monitor" design system.

A centralized visual identity for the RPM System. Every page calls
apply_theme(), so the whole app follows one token set. The signature
element is the vitals monitor: monospace numerals, uppercase unit
labels, a live pulse dot and a small ECG trace on each readout card.
"""

import streamlit as st

# ── Design tokens ──────────────────────────────────────────────────
TOKENS = {
    "light": {
        "canvas":        "#F1F5F3",
        "surface":       "#FFFFFF",
        "ink":           "#16242B",
        "muted":         "#5F717A",
        "border":        "#DCE5E1",
        "primary":       "#0E7A5C",
        "primary_hover": "#0A5E46",
        "primary_ink":   "#FFFFFF",
        "pulse":         "#12A085",
        "info":          "#2A6A9B",
        "alert":         "#C73E3A",
        "amber":         "#B8761D",
        "sidebar":       "#12312E",
        "sidebar_2":     "#173B37",
        "tint_primary":  "#E7F4EF",
        "tint_info":     "#E7F0F7",
        "tint_amber":    "#FBF3E4",
        "tint_alert":    "#FBE9E7",
    },
    "dark": {
        "canvas":        "#0B1214",
        "surface":       "#131D20",
        "ink":           "#E6EDEA",
        "muted":         "#8BA0A6",
        "border":        "#24363A",
        "primary":       "#2FC495",
        "primary_hover": "#46D6A8",
        "primary_ink":   "#06231B",
        "pulse":         "#35D3B4",
        "info":          "#6DB1E2",
        "alert":         "#F2655B",
        "amber":         "#ECAF55",
        "sidebar":       "#0E171A",
        "sidebar_2":     "#142023",
        "tint_primary":  "#0E241D",
        "tint_info":     "#0E1E2C",
        "tint_amber":    "#2B2210",
        "tint_alert":    "#2B1416",
    },
}


def theme_tokens() -> dict:
    """Return the token set for the active mode."""
    return TOKENS["dark" if st.session_state.get("dark_mode", False) else "light"]


def is_dark() -> bool:
    return st.session_state.get("dark_mode", False)


# ── Signature: ECG trace + pulse dot ───────────────────────────────
def ecg_svg(color: str, width: int = 84, height: int = 26, stroke: float = 1.6) -> str:
    """A tiny ECG-style trace used inside vitals readout cards."""
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 84 26" '
        f'fill="none" xmlns="http://www.w3.org/2000/svg" '
        f'style="display:block;width:100%;height:{height}px;opacity:.9;">'
        f'<path d="M0 15 H12 L16 9 L20 20 L24 15 H36 L41 3 L46 22 L51 15 H72 L76 10 L80 19 L84 15" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )


def page_header(icon: str, title: str, subtitle: str = None) -> str:
    """Signature page header: icon, Space Grotesk title, subtitle, ECG rule."""
    t = theme_tokens()
    sub = f'<div style="font-size:13px;color:{t["muted"]};margin-top:6px;">{subtitle}</div>' if subtitle else ""
    return f"""
    <div style="margin:0 0 6px;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:44px;height:44px;border-radius:12px;background:{t['tint_primary']};
                 border:1px solid {t['border']};display:flex;align-items:center;justify-content:center;
                 font-size:22px;flex-shrink:0;">{icon}</div>
            <div>
                <h1 style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:700;
                     color:{t['ink']};margin:0;line-height:1.15;">{title}</h1>
                {sub}
            </div>
        </div>
        <div style="margin-top:14px;border-bottom:1px solid {t['border']};position:relative;height:10px;">
            <svg width="100%" height="10" viewBox="0 0 600 10" preserveAspectRatio="none" fill="none">
                <path d="M0 5 H140 L146 1 L152 8 L158 5 H290 L296 3 L302 7 L308 5 H440 L446 2 L452 8 L458 5 H600"
                      stroke="{t['pulse']}" stroke-width="1.5" stroke-linejoin="round" opacity="0.55"/>
            </svg>
        </div>
    </div>
    """


def severity_tone(level: str) -> str:
    """Map a severity/risk level to a palette tone name."""
    level = (level or "").lower()
    if level in ("critical", "severe", "high", "danger"):
        return "alert"
    if level in ("moderate", "medium", "warning"):
        return "amber"
    if level in ("mild", "elevated", "low"):
        return "info"
    return "normal"


def vital_card(label: str, value: str, unit: str = "", tone: str = "normal",
               delta: str = None) -> str:
    """Signature vitals monitor readout card.

    tone: normal | info | amber | alert  (maps to a palette color)
    """
    t = theme_tokens()
    color = {
        "normal": t["primary"],
        "info":   t["info"],
        "amber":  t["amber"],
        "alert":  t["alert"],
    }.get(tone, t["primary"])
    dot = (
        f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
        f'background:{t["pulse"]};box-shadow:0 0 0 0 {t["pulse"]};animation:vpulse 2.4s infinite;"></span>'
    )
    delta_html = (
        f'<span style="font-size:11px;font-weight:600;color:{color};'
        f'font-family:\'JetBrains Mono\',monospace;">{delta}</span>' if delta else ""
    )
    return f"""
    <div style="background:{t['surface']};border:1px solid {t['border']};border-left:3px solid {color};
         border-radius:12px;padding:12px 14px 8px;height:100%;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <span style="font-size:10px;font-weight:600;text-transform:uppercase;
                 letter-spacing:.06em;color:{t['muted']};">{label}</span>
            {dot}
        </div>
        <div style="display:flex;align-items:baseline;gap:6px;margin-top:6px;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:600;
                 color:{t['ink']};line-height:1;">{value}</span>
            <span style="font-size:11px;font-weight:500;color:{t['muted']};">{unit}</span>
            <span style="margin-left:auto;">{delta_html}</span>
        </div>
        <div style="margin-top:6px;">{ecg_svg(color)}</div>
    </div>
    """


# ── Theme CSS ──────────────────────────────────────────────────────
def _shared_css() -> str:
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    html, body, [class*="css"], .stMarkdown, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    h1, h2, h3, h4, h5 { font-family: 'Space Grotesk', sans-serif !important; }
    [data-testid="stMetric"] * { font-family: 'JetBrains Mono', monospace; }
    @keyframes vpulse {
        0%   { box-shadow: 0 0 0 0 var(--vp, #12A085); }
        70%  { box-shadow: 0 0 0 6px rgba(0,0,0,0); }
        100% { box-shadow: 0 0 0 0 rgba(0,0,0,0); }
    }
    @media (prefers-reduced-motion: reduce) {
        [style*="animation:vpulse"] { animation: none !important; }
    }
    </style>
    """


def _light_css(t: dict) -> str:
    return f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {t['sidebar']} !important; }}
    [data-testid="stSidebar"] * {{ color: rgba(255,255,255,0.88) !important; }}
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] p {{ color: rgba(255,255,255,0.72) !important; font-size: 13px !important; }}
    [data-testid="stSidebarNav"] a {{ color: rgba(255,255,255,0.66) !important; font-size: 13px !important;
        font-weight: 500 !important; border-left: 2px solid transparent !important; padding-left: 10px !important;
        border-radius: 0 !important; letter-spacing:.01em; }}
    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] a[aria-current="page"] {{ color: #ffffff !important;
        background: rgba(18,161,133,0.18) !important; border-left: 2px solid {t['pulse']} !important; }}
    [data-testid="stHeader"] {{ background: linear-gradient(90deg, {t['primary']} 0%, {t['sidebar']} 100%) !important;
        height: 52px !important; border-bottom: 1px solid {t['border']}; }}
    [data-testid="stHeader"] * {{ color: white !important; }}
    .main .block-container {{ background-color: {t['canvas']} !important; padding-top: 1.5rem !important; }}
    [data-testid="stMetric"] {{ background: {t['surface']} !important; border: 1px solid {t['border']} !important;
        border-radius: 12px !important; padding: 14px 16px !important; box-shadow: 0 1px 2px rgba(22,36,43,0.05); }}
    [data-testid="stMetricLabel"] {{ font-size: 10px !important; font-weight: 600 !important;
        text-transform: uppercase !important; letter-spacing: .05em !important; color: {t['muted']} !important; }}
    [data-testid="stMetricValue"] {{ font-size: 24px !important; font-weight: 600 !important;
        color: {t['primary']} !important; font-family: 'JetBrains Mono', monospace !important; }}
    .stButton > button, .stDownloadButton > button {{ background-color: {t['primary']} !important;
        color: {t['primary_ink']} !important; border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; font-size: 13px !important; padding: 8px 18px !important;
        box-shadow: 0 1px 2px rgba(22,36,43,0.12); }}
    .stButton > button:hover, .stDownloadButton > button:hover {{ background-color: {t['primary_hover']} !important; }}
    .stButton > button[kind="secondary"] {{ background-color: {t['surface']} !important;
        color: {t['alert']} !important; border: 1px solid {t['alert']} !important; }}
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput input, .stDateInput input, .stTimeInput input {{ border: 1px solid {t['border']} !important;
        border-radius: 8px !important; font-size: 13px !important; background: {t['surface']} !important; }}
    .stTextInput input:focus, .stTextArea textarea:focus {{ border-color: {t['primary']} !important;
        box-shadow: 0 0 0 2px rgba(14,122,92,0.15) !important; }}
    .stSelectbox div[data-baseweb="select"] > div:focus {{ border-color: {t['primary']} !important; }}
    h1 {{ font-family: 'Space Grotesk', sans-serif !important; font-size: 22px !important;
        font-weight: 700 !important; color: {t['ink']} !important; letter-spacing: -.01em; }}
    h2 {{ font-family: 'Space Grotesk', sans-serif !important; font-size: 17px !important;
        font-weight: 700 !important; color: {t['ink']} !important; }}
    h3 {{ font-family: 'Space Grotesk', sans-serif !important; font-size: 14px !important;
        font-weight: 700 !important; color: {t['ink']} !important; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 13px !important; font-weight: 600 !important;
        color: {t['muted']} !important; }}
    .stTabs [aria-selected="true"] {{ color: {t['primary']} !important; border-bottom-color: {t['primary']} !important; }}
    .stAlert {{ border-radius: 8px !important; font-size: 13px !important; }}
    .stSuccess {{ background: {t['tint_primary']} !important; border-left: 4px solid {t['primary']} !important;
        border-radius: 8px !important; color: {t['primary']} !important; }}
    .stInfo {{ background: {t['tint_info']} !important; border-left: 4px solid {t['info']} !important;
        border-radius: 8px !important; color: {t['info']} !important; }}
    .stWarning {{ background: {t['tint_amber']} !important; border-left: 4px solid {t['amber']} !important;
        border-radius: 8px !important; color: {t['amber']} !important; }}
    .stError {{ background: {t['tint_alert']} !important; border-left: 4px solid {t['alert']} !important;
        border-radius: 8px !important; color: {t['alert']} !important; }}
    .stDataFrame, [data-testid="stDataFrame"] {{ border-radius: 10px !important;
        border: 1px solid {t['border']} !important; overflow: hidden !important; }}
    .streamlit-expanderHeader {{ background: {t['surface']} !important; border-radius: 8px !important;
        font-size: 13px !important; font-weight: 600 !important; color: {t['ink']} !important;
        border: 1px solid {t['border']} !important; }}
    .stContainer, div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"],
    .stForm {{ border-color: {t['border']} !important; border-radius: 12px !important; }}
    hr {{ border-color: {t['border']} !important; }}
    code, pre, [data-testid="stCode"] {{ font-family: 'JetBrains Mono', monospace !important; }}
    #MainMenu {{ visibility: hidden; }} footer {{ visibility: hidden; }}
    [data-testid="stToolbar"] {{ visibility: hidden; }} [data-testid="stDecoration"] {{ display: none; }}
    </style>
    """


def _dark_css(t: dict) -> str:
    return f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: {t['sidebar']} !important; }}
    [data-testid="stSidebar"] * {{ color: rgba(255,255,255,0.88) !important; }}
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] p {{ color: rgba(255,255,255,0.72) !important; font-size: 13px !important; }}
    [data-testid="stSidebarNav"] a {{ color: rgba(255,255,255,0.66) !important; font-size: 13px !important;
        font-weight: 500 !important; border-left: 2px solid transparent !important; padding-left: 10px !important;
        border-radius: 0 !important; }}
    [data-testid="stSidebarNav"] a:hover,
    [data-testid="stSidebarNav"] a[aria-current="page"] {{ color: #ffffff !important;
        background: rgba(53,211,180,0.14) !important; border-left: 2px solid {t['pulse']} !important; }}
    [data-testid="stHeader"] {{ background: linear-gradient(90deg, #0F1E1C 0%, {t['canvas']} 100%) !important;
        height: 52px !important; border-bottom: 1px solid {t['border']}; }}
    [data-testid="stHeader"] * {{ color: white !important; }}
    .main .block-container {{ background-color: {t['canvas']} !important; padding-top: 1.5rem !important; }}
    [data-testid="stMetric"] {{ background: {t['surface']} !important; border: 1px solid {t['border']} !important;
        border-radius: 12px !important; padding: 14px 16px !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 10px !important; font-weight: 600 !important;
        text-transform: uppercase !important; letter-spacing: .05em !important; color: {t['muted']} !important; }}
    [data-testid="stMetricValue"] {{ font-size: 24px !important; font-weight: 600 !important;
        color: {t['primary']} !important; font-family: 'JetBrains Mono', monospace !important; }}
    .stButton > button, .stDownloadButton > button {{ background-color: {t['primary']} !important;
        color: {t['primary_ink']} !important; border: none !important; border-radius: 8px !important;
        font-weight: 600 !important; font-size: 13px !important; padding: 8px 18px !important; }}
    .stButton > button:hover, .stDownloadButton > button:hover {{ background-color: {t['primary_hover']} !important; }}
    .stButton > button[kind="secondary"] {{ background-color: {t['surface']} !important;
        color: {t['alert']} !important; border: 1px solid {t['alert']} !important; }}
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput input, .stDateInput input, .stTimeInput input {{ border: 1px solid {t['border']} !important;
        border-radius: 8px !important; font-size: 13px !important; background: {t['surface']} !important;
        color: {t['ink']} !important; }}
    .stTextInput input:focus, .stTextArea textarea:focus {{ border-color: {t['primary']} !important;
        box-shadow: 0 0 0 2px rgba(47,196,149,0.15) !important; }}
    .stSelectbox div[data-baseweb="select"] > div:focus {{ border-color: {t['primary']} !important; }}
    h1 {{ font-family: 'Space Grotesk', sans-serif !important; font-size: 22px !important;
        font-weight: 700 !important; color: {t['ink']} !important; letter-spacing: -.01em; }}
    h2 {{ font-family: 'Space Grotesk', sans-serif !important; font-size: 17px !important;
        font-weight: 700 !important; color: {t['ink']} !important; }}
    h3 {{ font-family: 'Space Grotesk', sans-serif !important; font-size: 14px !important;
        font-weight: 700 !important; color: {t['ink']} !important; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 13px !important; font-weight: 600 !important;
        color: {t['muted']} !important; }}
    .stTabs [aria-selected="true"] {{ color: {t['primary']} !important; border-bottom-color: {t['primary']} !important; }}
    .stAlert {{ border-radius: 8px !important; font-size: 13px !important; }}
    .stSuccess {{ background: {t['tint_primary']} !important; border-left: 4px solid {t['primary']} !important;
        border-radius: 8px !important; color: {t['primary']} !important; }}
    .stInfo {{ background: {t['tint_info']} !important; border-left: 4px solid {t['info']} !important;
        border-radius: 8px !important; color: {t['info']} !important; }}
    .stWarning {{ background: {t['tint_amber']} !important; border-left: 4px solid {t['amber']} !important;
        border-radius: 8px !important; color: {t['amber']} !important; }}
    .stError {{ background: {t['tint_alert']} !important; border-left: 4px solid {t['alert']} !important;
        border-radius: 8px !important; color: {t['alert']} !important; }}
    .stDataFrame, [data-testid="stDataFrame"] {{ border-radius: 10px !important;
        border: 1px solid {t['border']} !important; overflow: hidden !important; }}
    .streamlit-expanderHeader {{ background: {t['surface']} !important; border-radius: 8px !important;
        font-size: 13px !important; font-weight: 600 !important; color: {t['ink']} !important;
        border: 1px solid {t['border']} !important; }}
    .stContainer, div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"],
    .stForm {{ border-color: {t['border']} !important; border-radius: 12px !important; }}
    hr {{ border-color: {t['border']} !important; }}
    code, pre, [data-testid="stCode"] {{ font-family: 'JetBrains Mono', monospace !important; }}
    #MainMenu {{ visibility: hidden; }} footer {{ visibility: hidden; }}
    [data-testid="stToolbar"] {{ visibility: hidden; }} [data-testid="stDecoration"] {{ display: none; }}
    </style>
    """


def apply_theme():
    st.markdown(_shared_css(), unsafe_allow_html=True)
    if is_dark():
        st.markdown(_dark_css(TOKENS["dark"]), unsafe_allow_html=True)
    else:
        st.markdown(_light_css(TOKENS["light"]), unsafe_allow_html=True)


# ── Sidebar widgets ────────────────────────────────────────────────
def notification_bell(user: dict):
    """
    Renders a notification bell in the sidebar with unread counts.
    Role-based: patients see messages, doctors see messages + alerts,
    admins see messages + alerts + emergency notifications.
    """
    from app.database.repositories.message_repository import MessageRepository
    from app.database.repositories.alert_repository import AlertRepository
    from app.database.repositories.emergency_contact_repository import EmergencyContactRepository

    msg_repo = MessageRepository()
    alert_repo = AlertRepository()
    emerg_repo = EmergencyContactRepository()

    unread_msgs = msg_repo.count_unread(user["id"])
    open_alerts = 0
    emerg_count = 0

    if user["role"] == "doctor":
        open_alerts = len(alert_repo.list_open_for_doctor(user["id"]))
    elif user["role"] == "admin":
        severity_counts = alert_repo.count_open_by_severity_all()
        open_alerts = sum(severity_counts.values())
        emerg_count = len(emerg_repo.list_pending())

    total = unread_msgs + open_alerts + emerg_count
    alert_color = TOKENS["dark"]["alert"]

    badge_html = ""
    if total > 0:
        badge_html = f"""
        <span style="position:absolute;top:-4px;right:-4px;background:{alert_color};
             color:white;font-size:9px;font-weight:700;min-width:16px;height:16px;
             border-radius:8px;display:flex;align-items:center;justify-content:center;
             padding:0 4px;font-family:'JetBrains Mono',monospace;">{total}</span>
        """

    bell_html = f"""
    <div style="padding:6px 16px 10px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:4px;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="position:relative;display:inline-flex;">
                    <span style="font-size:16px;">🔔</span>
                    {badge_html}
                </div>
                <span style="font-size:11px;font-weight:600;color:rgba(255,255,255,0.7);
                     text-transform:uppercase;letter-spacing:.04em;">Notifications</span>
            </div>
            <span style="font-size:13px;font-weight:700;color:white;font-family:'JetBrains Mono',monospace;">
                {total}
            </span>
        </div>
    </div>
    """
    st.sidebar.markdown(bell_html, unsafe_allow_html=True)

    if total > 0:
        details = []
        if unread_msgs > 0:
            details.append(f"✉️ {unread_msgs} unread message{'s' if unread_msgs != 1 else ''}")
        if open_alerts > 0:
            details.append(f"🚨 {open_alerts} open alert{'s' if open_alerts != 1 else ''}")
        if emerg_count > 0:
            details.append(f"🆘 {emerg_count} pending emergency notification{'s' if emerg_count != 1 else ''}")

        with st.sidebar.expander("View notifications", expanded=False):
            for d in details:
                st.markdown(f'<p style="color:rgba(255,255,255,0.85);font-size:12px;margin:4px 0;">{d}</p>',
                            unsafe_allow_html=True)
            st.markdown('<hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:6px 0;">',
                        unsafe_allow_html=True)

            if unread_msgs > 0:
                if st.button("✉️ Go to Messages", key="notif_msgs"):
                    st.switch_page("pages/5_Messages.py")
            if open_alerts > 0 and user["role"] == "doctor":
                if st.button("🩻 Go to Dashboard", key="notif_dash"):
                    st.switch_page("pages/3_Doctor_Dashboard.py")
            if emerg_count > 0 and user["role"] == "admin":
                if st.button("📈 Go to Reports", key="notif_rpt"):
                    st.switch_page("pages/10_Admin_Reports.py")
    else:
        with st.sidebar.expander("View notifications", expanded=False):
            st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:12px;">No new notifications</p>',
                        unsafe_allow_html=True)


def profile_widget(user: dict):
    """Renders a profile card at the top of the sidebar."""
    initials = "".join([n[0].upper() for n in user["full_name"].split()[:2]])
    role_colors = {
        "admin":   "#ECAF55",
        "doctor":  "#6DB1E2",
        "patient": "#2FC495",
    }
    role_color = role_colors.get(user.get("role", "patient"), "#2FC495")

    st.sidebar.markdown(f"""
    <div style="text-align:center; padding:18px 16px 14px;
         border-bottom:1px solid rgba(255,255,255,0.1); margin-bottom:8px;">
        <div style="
            width:54px; height:54px; border-radius:50%;
            background:{role_color}; color:white;
            display:flex; align-items:center; justify-content:center;
            font-weight:800; font-size:18px; margin:0 auto;
            font-family:'JetBrains Mono', monospace;
        ">{initials}</div>
        <div style="font-size:10px; color:rgba(255,255,255,0.4); margin-top:10px; text-transform:uppercase; letter-spacing:.05em;">
            Welcome
        </div>
        <div style="font-size:14px; font-weight:700; color:white; margin-top:3px; font-family:'Space Grotesk',sans-serif;">
            {user["full_name"]}
        </div>
        <div style="font-size:11px; color:rgba(255,255,255,0.45); margin-top:2px;">
            {user.get("role","").title()}
        </div>
    </div>
    """, unsafe_allow_html=True)


def stat_tiles(stats: list):
    """
    Renders mini stat tiles in the sidebar.
    stats = [{"label": "Patients", "value": 24}, ...]
    Max 3 items.
    """
    tiles_html = "".join([
        f"""<div style="background:rgba(255,255,255,0.07);border-radius:7px;
            padding:8px 4px;text-align:center;">
            <div style="font-size:16px;font-weight:700;color:white;font-family:'JetBrains Mono',monospace;">{s["value"]}</div>
            <div style="font-size:9px;color:rgba(255,255,255,0.45);margin-top:2px;">{s["label"]}</div>
        </div>"""
        for s in stats[:3]
    ])
    st.sidebar.markdown(f"""
    <div style="padding:0 12px 12px;">
        <div style="font-size:9px;font-weight:700;text-transform:uppercase;
             letter-spacing:.05em;color:rgba(255,255,255,0.4);padding:10px 4px 8px;">
            Today
        </div>
        <div style="display:grid;grid-template-columns:repeat({len(stats[:3])},1fr);gap:6px;">
            {tiles_html}
        </div>
    </div>
    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:0 0 8px;">
    """, unsafe_allow_html=True)
