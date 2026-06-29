"""
EventLedger AI – App Mode
Manages Single User vs Multi User mode.

Single User:
  - No roles, no approvals, no user management
  - One owner account — full access to everything
  - Simple budget → expense → report flow
  - No approval workflow required

Multi User:
  - Full role system (Super Admin, Event Admin, Finance Head, Dept Head)
  - Budget approval workflow
  - User management, audit log, notifications
  - Each person sees only their role's UI
"""

import streamlit as st
from database.schema import get_connection


def get_app_mode() -> str:
    """Return 'single_user' or 'multi_user'. Cached in session."""
    if "app_mode" in st.session_state:
        return st.session_state.app_mode
    try:
        conn = get_connection()
        row  = conn.execute(
            "SELECT value FROM org_settings WHERE key='app_mode'"
        ).fetchone()
        conn.close()
        mode = row[0] if row else "single_user"
    except Exception:
        mode = "single_user"
    st.session_state.app_mode = mode
    return mode


def set_app_mode(mode: str):
    """Persist mode change ('single_user' or 'multi_user')."""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO org_settings (key,value) VALUES ('app_mode',?)",
        (mode,)
    )
    conn.commit()
    conn.close()
    st.session_state.app_mode = mode


def is_single_user() -> bool:
    return get_app_mode() == "single_user"


def is_multi_user() -> bool:
    return get_app_mode() == "multi_user"
