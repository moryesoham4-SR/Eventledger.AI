"""EventLedger AI – Audit Log page (Super Admin only)"""

import streamlit as st
import pandas as pd
from utils.roles import get_audit_log, is_super_admin
from utils.helpers import get_events
from components.ui import section_header, empty_state


def show(user):
    if not is_super_admin(user["id"]):
        st.error("🔒 Super Admin only.")
        return

    st.title("🔍 Audit Log")
    st.caption("Full activity trail across all events and users")
    st.divider()

    events = get_events(user["id"])
    ev_map = {"All Events": None}
    ev_map.update({e["name"]: e["id"] for e in events})

    col1, col2 = st.columns(2)
    sel_ev     = col1.selectbox("Filter by Event", list(ev_map.keys()))
    sel_action = col2.selectbox("Filter by Action",
        ["All","CREATE_EVENT","CREATE_USER","ASSIGN_ROLE","CREATE_PROPOSAL",
         "SUBMIT_PROPOSAL","APPROVE_PROPOSAL","REJECT_PROPOSAL","RESET_PASSWORD"])

    ev_id = ev_map.get(sel_ev)
    logs  = get_audit_log(event_id=ev_id, limit=200)

    if sel_action != "All":
        logs = [l for l in logs if l["action"] == sel_action]

    st.caption(f"{len(logs)} log entries")

    if not logs:
        empty_state("🔍", "No audit log entries found")
        return

    action_icons = {
        "CREATE_EVENT":    "📅",
        "CREATE_USER":     "👤",
        "ASSIGN_ROLE":     "🎭",
        "CREATE_PROPOSAL": "📝",
        "SUBMIT_PROPOSAL": "📤",
        "APPROVE_PROPOSAL":"✅",
        "REJECT_PROPOSAL": "❌",
        "RESET_PASSWORD":  "🔒",
    }

    from utils.helpers import to_ist
    rows = [{
        "Time":    to_ist(l.get("created_at")),
        "User":    l.get("user_name","System"),
        "Action":  f"{action_icons.get(l['action'],'')} {l['action'].replace('_',' ').title()}",
        "Details": l.get("details","—"),
        "Entity":  f"{l.get('entity_type','—')} #{l.get('entity_id','')}" if l.get("entity_type") else "—",
    } for l in logs]

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)