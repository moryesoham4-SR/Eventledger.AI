"""EventLedger AI – Approvals page (Finance Head + Super Admin)"""

import streamlit as st
import pandas as pd
from utils.budget_workflow import (
    get_proposals, get_pending_proposals, get_line_items,
    approve_proposal, reject_proposal
)
from utils.roles import get_accessible_events, has_permission, log_action
from utils.currency import get_symbol
from components.ui import section_header, empty_state

def _fmt_date(val, default="—"):
    if val is None: return default
    import datetime
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()[:10]
    return str(val)[:10] if val else default



def show(user):
    if not has_permission(user["id"], "approve_budget"):
        st.error("🔒 Access denied. Finance Head or Super Admin only.")
        return

    st.title("📋 Budget Approvals")
    st.caption("Review, approve or reject department budget proposals")
    st.divider()

    sym    = get_symbol()
    events = get_accessible_events(user["id"])
    if not events:
        empty_state("📅", "No events accessible"); return

    tab_pending, tab_all, tab_history = st.tabs(
        ["⏳ Pending", "📋 All Proposals", "📜 History"])

    # ── Pending ──────────────────────────────────────────────────────────────
    with tab_pending:
        pending = get_pending_proposals(user["id"])
        if not pending:
            st.success("✅ No pending budgets. You're all caught up!")
        else:
            st.info(f"**{len(pending)} budget(s) awaiting your review**")
            for p in pending:
                ev_sym = get_symbol()
                with st.expander(
                    f"{'⏳'} {p['dept_name']} — {ev_sym}{p['total_amount']:,.0f}"
                    f"   ·   v{p.get('version',1)}   ·   by {p['submitter_name']}",
                    expanded=True
                ):
                    # Conflict check
                    if p["submitted_by"] == user["id"]:
                        st.error("⚠️ You submitted this proposal. It has been escalated to another approver.")
                        continue

                    # Line items
                    items = get_line_items(p["id"])
                    if items:
                        st.markdown("**Line Items:**")
                        df = pd.DataFrame([{
                            "Item":      i["item_name"],
                            "Category":  i["category"],
                            "Qty":       f"{i['quantity']:.0f} {i['unit']}",
                            "Unit Price":f"{ev_sym}{i['unit_price']:,.0f}",
                            "Total":     f"{ev_sym}{i['total_amount']:,.0f}",
                            "Notes":     i.get("notes") or "—",
                        } for i in items])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        st.metric("Grand Total", f"{ev_sym}{p['total_amount']:,.0f}")

                    if p.get("notes"):
                        st.info(f"📝 Notes from submitter: {p['notes']}")

                    c1, c2 = st.columns(2)
                    if c1.button("✅ Approve", key=f"app_{p['id']}", use_container_width=True):
                        res = approve_proposal(p["id"], user["id"])
                        if res["ok"]:
                            st.success(res["message"])
                        else:
                            st.error(res["message"])
                        st.rerun()

                    if c2.button("❌ Reject", key=f"rej_{p['id']}", use_container_width=True,
                                 type="secondary"):
                        st.session_state[f"rej_open_{p['id']}"] = True

                    if st.session_state.get(f"rej_open_{p['id']}"):
                        reason = st.text_area(
                            "Rejection reason *",
                            placeholder="e.g. Please reduce printing cost by 20% and resubmit",
                            key=f"rej_text_{p['id']}"
                        )
                        ra, rb = st.columns(2)
                        if ra.button("Send Rejection", key=f"send_rej_{p['id']}",
                                     use_container_width=True):
                            if reason.strip():
                                res = reject_proposal(p["id"], user["id"], reason.strip())
                                st.session_state.pop(f"rej_open_{p['id']}", None)
                                st.rerun()
                            else:
                                st.error("Please provide a reason.")
                        if rb.button("Cancel", key=f"cancel_rej_{p['id']}",
                                     use_container_width=True, type="secondary"):
                            st.session_state.pop(f"rej_open_{p['id']}", None)
                            st.rerun()

    # ── All Proposals ────────────────────────────────────────────────────────
    with tab_all:
        section_header("All Budget Proposals", "📋")
        ev_map = {e["name"]: e for e in events}
        sel_ev = st.selectbox("Filter by Event", ["All Events"] + list(ev_map.keys()),
                              key="all_prop_ev")
        sel_status = st.selectbox("Filter by Status",
                                   ["All", "draft","submitted","approved","rejected"],
                                   key="all_prop_status")

        all_props = []
        for ev in (events if sel_ev == "All Events" else [ev_map[sel_ev]]):
            props = get_proposals(ev["id"],
                                   status=None if sel_status=="All" else sel_status)
            for p in props:
                p["event_name"] = ev["name"]
            all_props.extend(props)

        if not all_props:
            empty_state("📋", "No proposals found")
        else:
            status_icons = {"draft":"📝","submitted":"⏳","approved":"✅","rejected":"❌"}
            rows = [{
                "Event":      p.get("event_name","—"),
                "Department": p["dept_name"],
                "Title":      p["title"],
                "Amount":     f"{sym}{p['total_amount']:,.0f}",
                "Status":     f"{status_icons.get(p['status'],'')} {p['status'].title()}",
                "Version":    f"v{p.get('version',1)}",
                "Submitted By": p["submitter_name"],
                "Submitted":  _fmt_date(p.get("submitted_at")),
            } for p in all_props]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── History ──────────────────────────────────────────────────────────────
    with tab_history:
        section_header("Approval History", "📜")
        from utils.roles import get_audit_log
        logs = get_audit_log(limit=50)
        approval_logs = [l for l in logs
                         if l["action"] in ("APPROVE_PROPOSAL","REJECT_PROPOSAL","SUBMIT_PROPOSAL")]
        if not approval_logs:
            empty_state("📜", "No approval history yet")
        else:
            icons = {"APPROVE_PROPOSAL":"✅","REJECT_PROPOSAL":"❌","SUBMIT_PROPOSAL":"📤"}
            rows  = [{
                "Action":  f"{icons.get(l['action'],'')} {l['action'].replace('_',' ').title()}",
                "By":      l.get("user_name","—"),
                "Details": l.get("details","—"),
                "Time":    l.get("created_at","—")[:16],
            } for l in approval_logs]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)