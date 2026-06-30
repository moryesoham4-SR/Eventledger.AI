"""EventLedger AI – UI Components (mode-aware sidebar)"""

import streamlit as st
from utils.app_mode import is_single_user
from utils.roles import (
    get_primary_role, unread_count,
    ROLE_ICONS, ROLE_COLORS, ROLES
)


def render_sidebar(user):
    if is_single_user():
        _sidebar_single(user)
    else:
        _sidebar_multi(user)


def _sidebar_single(user):
    """Simple sidebar for single-user mode — full access, no role restrictions."""
    with st.sidebar:
        st.markdown("## 📊 EventLedger AI")
        st.caption(f"👤 {user['name']}")
        st.caption("🟢 **Single User Mode**")
        st.divider()

        nav = [
            ("dashboard",   "🏠", "Dashboard"),
            ("events",      "📅", "Events"),
            ("finance",     "💰", "Finance"),
            ("sponsors",    "🤝", "Sponsors"),
            ("vendors",     "🚚", "Vendors"),
            ("analytics",   "📈", "Analytics"),
            ("ai_insights", "🤖", "AI Insights"),
            ("reports",     "📄", "Reports"),
            ("archive",     "📦", "Archive"),
            ("settings",    "⚙️", "Settings"),
        ]
        for page, icon, label in nav:
            if st.button(f"{icon}  {label}", key=f"nav_{page}",
                         use_container_width=True):
                st.session_state.page = page
                st.session_state.active_event = None
                st.rerun()

        st.divider()
        if st.button("🚪  Sign Out", key="logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


@st.fragment(run_every=8)
def _live_notification_badge(uid):
    """
    Polls every 8 seconds for new unread notifications.
    Only this small fragment re-runs (not the whole page/app),
    so it feels like a live WhatsApp/Instagram-style badge
    without disrupting whatever the user is doing.
    """
    notifs = unread_count(uid)

    prev_key = f"_prev_notif_count_{uid}"
    prev = st.session_state.get(prev_key, notifs)

    if notifs > prev:
        # New notification(s) arrived since last poll
        new_count = notifs - prev
        st.toast(f"🔔 You have {new_count} new notification{'s' if new_count>1 else ''}!", icon="🔔")

    st.session_state[prev_key] = notifs

    if notifs > 0:
        st.warning(f"🔔 {notifs} unread notification{'s' if notifs>1 else ''}")
    else:
        st.caption("🔕 No new notifications")


def _sidebar_multi(user):
    """Full role-based sidebar for multi-user mode."""
    uid    = user["id"]
    role   = get_primary_role(uid)
    icon   = ROLE_ICONS.get(role, "👤")

    with st.sidebar:
        st.markdown("## 📊 EventLedger AI")
        st.caption(f"{icon} **{user['name']}**")
        st.caption(f"🔵 **Multi User Mode** · {ROLES.get(role, role)}")
        _live_notification_badge(uid)
        st.divider()

        is_sa  = bool(user.get("is_super_admin"))
        is_ea  = role in ("super_admin", "event_admin")
        is_fin = role in ("super_admin", "finance_head")

        st.markdown("**Main**")
        for page, icon_s, label in [
            ("dashboard", "🏠", "Dashboard"),
            ("events",    "📅", "Events"),
        ]:
            if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                st.session_state.page = page
                st.session_state.active_event = None; st.rerun()

        if is_fin:
            st.markdown("**Finance**")
            for page, icon_s, label in [
                ("finance",   "💰", "Finance"),
                ("approvals", "📋", "Pending Approvals"),
            ]:
                if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.session_state.active_event = None; st.rerun()

        if is_ea:
            for page, icon_s, label in [
                ("sponsors", "🤝", "Sponsors"),
                ("vendors",  "🚚", "Vendors"),
            ]:
                if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.session_state.active_event = None; st.rerun()

        st.markdown("**Insights**")
        for page, icon_s, label in [
            ("analytics",   "📈", "Analytics"),
            ("ai_insights", "🤖", "AI Insights"),
            ("reports",     "📄", "Reports"),
        ]:
            if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                st.session_state.page = page
                st.session_state.active_event = None; st.rerun()

        if is_sa:
            st.markdown("**Admin**")
            for page, icon_s, label in [
                ("user_management", "👥", "User Management"),
                ("archive",         "📦", "Archive"),
                ("audit_log",       "🔍", "Audit Log"),
            ]:
                if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.session_state.active_event = None; st.rerun()

        if st.button("🔔  Notifications", key="nav_notifs", use_container_width=True):
            st.session_state.page = "notifications"
            st.session_state.active_event = None; st.rerun()

        st.markdown("**System**")
        if st.button("⚙️  Settings", key="nav_settings", use_container_width=True):
            st.session_state.page = "settings"
            st.session_state.active_event = None; st.rerun()

        st.divider()
        if st.button("🚪  Sign Out", key="logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ── Shared helpers ──────────────────────────────────────────────────────────

def section_header(title, icon=""):
    st.markdown(f"### {icon} {title}" if icon else f"### {title}")


def empty_state(icon, message, hint=""):
    st.info(f"{icon} **{message}**" + (f"\n\n{hint}" if hint else ""))


def fmt_currency(amount, symbol="₹"):
    if abs(amount) >= 10_000_000:
        return f"{symbol}{amount/10_000_000:.2f} Cr"
    if abs(amount) >= 100_000:
        return f"{symbol}{amount/100_000:.2f} L"
    if abs(amount) >= 1_000:
        return f"{symbol}{amount/1_000:.1f}K"
    return f"{symbol}{amount:,.0f}"


def role_badge(role: str) -> str:
    from utils.roles import ROLE_ICONS, ROLES
    return f"{ROLE_ICONS.get(role,'👤')} {ROLES.get(role, role)}"