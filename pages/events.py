"""EventLedger AI – Events page (role-aware)"""

import streamlit as st
import datetime
import pandas as pd
from utils.helpers import get_event_summary
from utils.roles import (
    get_accessible_events, has_permission, is_super_admin, log_action
)
from utils.helpers import create_event, delete_event
from utils.currency import get_global_currency, get_symbol, CURRENCY_LABELS, CURRENCIES
from components.ui import section_header, empty_state, fmt_currency


def show(user):
    st.title("📅 Events")
    st.caption("Your event portfolio")
    st.divider()

    uid    = user["id"]
    can_create = has_permission(uid, "create_event") or is_super_admin(uid)
    events = get_accessible_events(uid)

    tabs = (["📋 All Events", "➕ Create New Event"]
            if can_create else ["📋 All Events"])
    tab_results = st.tabs(tabs)

    # ── All Events ────────────────────────────────────────────────────────────
    with tab_results[0]:
        if not events:
            if can_create:
                st.info("👋 No events yet. Go to **➕ Create New Event** tab to create your first one!")
            else:
                empty_state("📅", "No events assigned to you",
                            "Ask your Super Admin to assign you to an event.")
            return

        c_s, c_f = st.columns([3, 2])
        search = c_s.text_input("🔍 Search", placeholder="Event name…",
                                 label_visibility="collapsed")
        flt    = c_f.selectbox("Filter", ["All","active","planning","completed"],
                                label_visibility="collapsed")
        filtered = events
        if search:
            filtered = [e for e in filtered if search.lower() in e["name"].lower()]
        if flt != "All":
            filtered = [e for e in filtered if e.get("status") == flt]

        st.caption(f"{len(filtered)} event(s)")

        rows = []
        for ev in filtered:
            s      = get_event_summary(ev["id"])
            ev_sym = get_symbol(ev.get("currency"))
            rows.append({
                "Event":      ev["name"],
                "Venue":      ev.get("venue") or "—",
                "Start":      ev.get("start_date","—"),
                "End":        ev.get("end_date","—"),
                "Phase":      ev.get("phase","planning").title(),
                "Revenue":    f"{ev_sym}{s['act_income']:,.0f}",
                "Expenses":   f"{ev_sym}{s['act_expense']:,.0f}",
                "Profit":     f"{ev_sym}{s['act_profit']:,.0f}",
                "Accuracy":   f"{s['budget_accuracy']:.1f}%",
                "Attendees":  f"{ev.get('expected_attendees',0):,}",
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("**Open an event:**")
        btn_cols = st.columns(max(1, min(len(filtered), 3)))
        for i, ev in enumerate(filtered):
            with btn_cols[i % 3]:
                s      = get_event_summary(ev["id"])
                ev_sym = get_symbol(ev.get("currency"))
                st.markdown(f"**{ev['name']}**")
                st.caption(f"📍 {ev.get('venue') or '—'}  ·  {ev.get('phase','planning').upper()}")
                mc1, mc2 = st.columns(2)
                mc1.metric("Revenue", f"{ev_sym}{s['act_income']:,.0f}")
                mc2.metric("Profit",  f"{ev_sym}{s['act_profit']:,.0f}")
                if st.button("📂 Open Event", key=f"ev_open_{ev['id']}", use_container_width=True):
                    st.session_state.active_event = ev["id"]
                    st.session_state.page = "event_detail"
                    st.rerun()
                if is_super_admin(uid):
                    if st.button("🗑 Delete", key=f"ev_del_{ev['id']}",
                                 use_container_width=True, type="secondary"):
                        delete_event(ev["id"])
                        st.success(f"Deleted '{ev['name']}'")
                        st.rerun()
                st.markdown("---")

    # ── Create Event (Super Admin / Event Admin only) ─────────────────────────
    if can_create and len(tab_results) > 1:
        with tab_results[1]:
            section_header("New Event Details", "📋")
            with st.form("create_event_form", clear_on_submit=True):
                st.markdown("**Basic Information**")
                c1, c2 = st.columns(2)
                ev_name  = c1.text_input("Event Name *", placeholder="e.g. TechFest 2028")
                ev_venue = c1.text_input("Venue",        placeholder="e.g. Convention Center")
                ev_start = c1.date_input("Start Date",
                    value=datetime.date.today() + datetime.timedelta(days=30))
                ev_desc  = c2.text_area("Description", height=100)
                ev_end   = c2.date_input("End Date",
                    value=datetime.date.today() + datetime.timedelta(days=32))
                ev_att   = c2.number_input("Expected Attendees", min_value=0, value=500, step=50)

                st.markdown("**Financial Settings**")
                c3, _ = st.columns(2)
                _gcur = get_global_currency()
                _keys = list(CURRENCIES.keys())
                _idx  = _keys.index(_gcur) if _gcur in _keys else 0
                ev_currency = c3.selectbox("Currency", options=_keys,
                    format_func=lambda x: CURRENCY_LABELS.get(x,x), index=_idx)
                submitted = st.form_submit_button("🚀 Create Event", use_container_width=True)

            if submitted:
                if not ev_name.strip():
                    st.error("Event name is required.")
                elif ev_end < ev_start:
                    st.error("End date must be after start date.")
                else:
                    eid = create_event(uid, ev_name.strip(), ev_desc.strip(),
                                       ev_venue.strip(), str(ev_start), str(ev_end),
                                       ev_att, ev_currency)
                    log_action(uid, "CREATE_EVENT", "events", eid,
                               details=f"Created event: {ev_name}")
                    st.success(f"✅ Event **'{ev_name}'** created!")
                    st.session_state.active_event = eid
                    st.session_state.page = "event_detail"
                    st.rerun()
