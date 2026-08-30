"""
22_Preferences.py — Dark mode toggle + language selector
"""
import streamlit as st
from app.utils.custom_css import apply_theme, profile_widget, page_header
from app.utils.translations import t, language_selector, LANGUAGES
from app.core.security import SessionManager

st.set_page_config(page_title="RPM — Preferences", page_icon=":material/palette:", layout="wide")
apply_theme()

user = SessionManager.get_current_user()
if not user:
    st.switch_page("pages/1_Login.py")
    st.stop()

profile_widget(user)

st.markdown(page_header(":material/palette:", "Preferences", "Dark mode and language settings for your experience."), unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### :material/dark_mode: Dark Mode")
    current_dark = st.session_state.get("dark_mode", False)
    dark_mode = st.toggle("Enable Dark Mode", value=current_dark,
                           help="Switch between light and dark themes")
    if dark_mode != current_dark:
        st.session_state.dark_mode = dark_mode
        st.rerun()

    if dark_mode:
        st.markdown("""
        <div style="background:#131D20;border:1px solid #24363A;border-radius:10px;padding:16px;margin-top:10px;">
            <div style="color:#E6EDEA;font-weight:600;"><span class="material-symbols-outlined" style="font-size:16px;vertical-align:-3px;">dark_mode</span> Dark Mode Active</div>
            <div style="color:#8BA0A6;font-size:12px;margin-top:4px;">Easy on the eyes for nighttime monitoring.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#F1F5F3;border:1px solid #DCE5E1;border-radius:10px;padding:16px;margin-top:10px;">
            <div style="color:#16242B;font-weight:600;"><span class="material-symbols-outlined" style="font-size:16px;vertical-align:-3px;">light_mode</span> Light Mode Active</div>
            <div style="color:#5F717A;font-size:12px;margin-top:4px;">Clean and bright for daytime use.</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("### :material/language: Language")
    current_lang = st.session_state.get("language", "en")

    lang_descriptions = {
        "en": "English — Default language",
        "es": "Español — Spanish translation",
        "fr": "Français — French translation",
        "de": "Deutsch — German translation",
    }

    selected_lang = st.selectbox(
        "Select Language",
        list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(current_lang),
        format_func=lambda x: LANGUAGES[x],
    )

    if selected_lang != current_lang:
        st.session_state.language = selected_lang
        st.rerun()

    st.markdown(f"**Current:** {LANGUAGES.get(selected_lang, 'English')}")
    st.caption(lang_descriptions.get(selected_lang, ""))

st.markdown("### :material/info: Preview")
st.info(f"Currently viewing the system in **{LANGUAGES.get(selected_lang, 'English')}** "
        f"with **{'dark' if st.session_state.get('dark_mode', False) else 'light'}** mode.")

if st.button(":material/restart_alt: Reset to Defaults"):
    st.session_state.dark_mode = False
    st.session_state.language = "en"
    st.rerun()
