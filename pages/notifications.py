"""EventLedger AI – Notifications page"""

import streamlit as st
import pandas as pd
from utils.roles import get_notifications, mark_notifications_read
from components.ui import section_header, empty_state


def show(user):
    st.title("🔔 Notifications")
    st.divider()

    notifs = get_notifications(user["id"])

    if not notifs:
        empty_state("🔔", "No notifications yet", "Activity will appear here as events progress.")
        return

    unread = [n for n in notifs if not n["is_read"]]
    read   = [n for n in notifs if n["is_read"]]

    col1, col2 = st.columns([1, 3])
    col1.metric("🔴 Unread", str(len(unread)))
    col2.metric("Total",     str(len(notifs)))

    if unread and st.button("✅ Mark All as Read", use_container_width=False):
        mark_notifications_read(user["id"])
        st.rerun()

    st.divider()

    type_icons = {"info":"ℹ️","success":"✅","warning":"⚠️","error":"❌"}

    for n in notifs:
        icon = type_icons.get(n.get("type","info"), "•")
        is_read = bool(n["is_read"])
        with st.container():
            if not is_read:
                st.markdown(f"**{icon} {n['title']}** 🆕")
            else:
                st.markdown(f"{icon} {n['title']}")
            st.caption(n["message"])
            st.caption(f"🕐 {n.get('created_at','—')[:16]}")
            st.markdown("---")
