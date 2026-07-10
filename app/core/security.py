"""
security.py
------------
Two related but distinct responsibilities, kept in one file per the
project's original folder plan ("core/security.py - password hashing,
session mgmt"):

  1. PasswordHasher — framework-agnostic bcrypt wrapper. Used by
     AuthService (Application layer). Has zero Streamlit dependency,
     so it's independently testable and reusable outside a Streamlit
     context.

  2. SessionManager — wraps Streamlit's st.session_state. This IS
     Streamlit-specific by nature (session state is a UI/presentation
     concept), so it deliberately lives at the boundary between the
     Presentation layer and everything else. Pages call
     SessionManager.require_role(...) as a one-line access guard.
"""

import time
from typing import Optional

import bcrypt
import streamlit as st

from app.core.config import Config
from app.database.models import User


# ==================================================================
# 1. Password Hashing
# ==================================================================
class PasswordHasher:
    """
    Wraps bcrypt for password hashing/verification.

    Why bcrypt specifically: it's a deliberately slow, adaptive hash
    function purpose-built for passwords (unlike MD5/SHA256, which are
    fast and therefore poorly suited to resisting brute-force attacks).
    Each hash embeds its own random salt, so identical passwords never
    produce identical hashes.
    """

    @staticmethod
    def hash_password(plain_password: str) -> str:
        salt = bcrypt.gensalt(rounds=Config.SECURITY.bcrypt_rounds)
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Returns False (rather than raising) on malformed hashes, so a
        corrupted/legacy hash in the DB fails a login attempt safely
        instead of crashing the app.
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False


# ==================================================================
# 2. Session Management (Streamlit-specific)
# ==================================================================
_SESSION_USER_KEY = "rpm_current_user"
_SESSION_LOGIN_TIME_KEY = "rpm_login_time"


class SessionManager:
    """
    Manages the logged-in user's identity via st.session_state.

    Design decision: session_state stores only a small dict (id, name,
    email, role) — never the full User object, and never the password
    hash. This is the "current identity" cache; the source of truth
    always remains the database.
    """

    @staticmethod
    def login(user: User) -> None:
        st.session_state[_SESSION_USER_KEY] = {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
        }
        st.session_state[_SESSION_LOGIN_TIME_KEY] = time.time()

    @staticmethod
    def logout() -> None:
        st.session_state.pop(_SESSION_USER_KEY, None)
        st.session_state.pop(_SESSION_LOGIN_TIME_KEY, None)

    @staticmethod
    def get_current_user() -> Optional[dict]:
        """
        Returns the session dict, or None if not logged in or the
        session has expired (auto-clears expired sessions as a
        side effect).
        """
        if _SESSION_USER_KEY not in st.session_state:
            return None
        if SessionManager._is_expired():
            SessionManager.logout()
            return None
        return st.session_state[_SESSION_USER_KEY]

    @staticmethod
    def is_authenticated() -> bool:
        return SessionManager.get_current_user() is not None

    @staticmethod
    def _is_expired() -> bool:
        login_time = st.session_state.get(_SESSION_LOGIN_TIME_KEY)
        if login_time is None:
            return True
        elapsed_minutes = (time.time() - login_time) / 60
        return elapsed_minutes > Config.SECURITY.session_expiry_minutes

    @staticmethod
    def refresh_activity() -> None:
        """Extends the session on each authenticated page load (sliding expiry)."""
        if _SESSION_USER_KEY in st.session_state:
            st.session_state[_SESSION_LOGIN_TIME_KEY] = time.time()

    @staticmethod
    def require_role(*allowed_roles: str) -> dict:
        """
        Page-level access guard. Call this as the FIRST line of every
        protected page:

            user = SessionManager.require_role("doctor")

        Halts page rendering (via st.stop()) with an appropriate
        message if the user isn't logged in or doesn't hold one of the
        allowed roles. Returns the session dict on success so the page
        can use it immediately (e.g., user["id"]).
        """
        user = SessionManager.get_current_user()
        if user is None:
            st.warning("Please log in to access this page.")
            st.stop()
        if user["role"] not in allowed_roles:
            st.error("You do not have permission to access this page.")
            st.stop()
        SessionManager.refresh_activity()
        return user
