"""EventLedger AI – Dashboard (mode-aware: single user vs multi user)"""

import streamlit as st
import pandas as pd
from utils.helpers import get_events, get_event_summary
from utils.roles import (
    get_primary_role, get_accessible_events,
    get_audit_log, ROLE_ICONS, ROLES, is_super_admin
)
from utils.budget_workflow import get_pending_proposals
from utils.app_mode import is_single_user
from utils.charts import bar_comparison, donut, COLORS
from utils.currency import get_symbol
from components.ui import section_header, empty_state, fmt_currency


@st.fragment(run_every=8)
def _live_event_summary(event_id, event_name, ev_sym):
    """
    Auto-refreshes every 8 seconds so approved budgets, new expenses,
    or income show up live for EVERY user assigned to this event —
    no manual page refresh needed (similar to a live notification feed).
    """
    s = get_event_summary(event_id)
    st.subheader(f"📊 {event_name} — Whole Event Overview")
    st.caption("🟢 Live · Visible to everyone assigned to this event")
    ec1, ec2, ec3, ec4 = st.columns(4)
    ec1.metric("💰 Total Budget", f"{ev_sym}{s.get('est_expense',0):,.0f}")
    ec2.metric("💸 Total Spent",  f"{ev_sym}{s.get('act_expense',0):,.0f}")
    ec3.metric("💚 Remaining",    f"{ev_sym}{(s.get('est_expense',0)-s.get('act_expense',0)):,.0f}")
    ec4.metric("📈 Total Income", f"{ev_sym}{s.get('act_income',0):,.0f}")
    if s.get('est_expense', 0) > 0:
        st.progress(min(s.get('act_expense',0)/s.get('est_expense',1), 1.0))
        st.caption(f"{s.get('act_expense',0)/s.get('est_expense',1)*100:.1f}% of total event budget spent")


def show(user):
    if is_single_user():
        _single_user_dashboard(user)
    else:
        role = get_primary_role(user["id"])
        if is_super_admin(user["id"]):
            _super_admin_dashboard(user)
        elif role == "finance_head":
            _finance_dashboard(user)
        elif role == "dept_head":
            _dept_dashboard(user)
        elif role == "event_admin":
            _event_admin_dashboard(user)
        else:
            _default_dashboard(user)


# ══════════════════════════════════════════════════════════════════════════════
#  SINGLE USER DASHBOARD — full access, no roles
# ══════════════════════════════════════════════════════════════════════════════

def _single_user_dashboard(user):
    sym    = get_symbol()
    events = get_events(user["id"])

    st.title(f"👋 Welcome back, {user['name'].split()[0]}")
    st.caption(f"🏢 {user.get('org_name','')}  ·  🟢 Single User Mode")
    st.divider()

    if not events:
        st.info("📅 No events yet. Go to **Events** → **Create New Event** to get started.")
        if st.button("➕ Create First Event", use_container_width=False):
            st.session_state.page = "events"; st.rerun()
        return

    # ── Aggregate KPIs ────────────────────────────────────────────────────
    summaries   = {ev["id"]: get_event_summary(ev["id"]) for ev in events}
    total_inc   = sum(s["act_income"]     for s in summaries.values())
    total_exp   = sum(s["act_expense"]    for s in summaries.values())
    total_pft   = total_inc - total_exp
    total_spon  = sum(s["sponsors_total"] for s in summaries.values())
    active_cnt  = sum(1 for e in events if e.get("status") == "active")
    avg_acc     = sum(s["budget_accuracy"] for s in summaries.values()) / len(summaries)

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("📅 Events",      str(len(events)))
    c2.metric("🔴 Active",      str(active_cnt))
    c3.metric("💰 Revenue",     f"{sym}{total_inc:,.0f}")
    c4.metric("📤 Expenses",    f"{sym}{total_exp:,.0f}")
    c5.metric("📈 Net Profit",  f"{sym}{total_pft:,.0f}",
              delta=f"{'+' if total_pft>=0 else ''}{sym}{abs(total_pft):,.0f}")
    c6.metric("🎯 Avg Accuracy",f"{avg_acc:.1f}%")
    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────
    col1, col2 = st.columns([3,2])
    with col1:
        section_header("Revenue vs Expenses", "📊")
        fig = bar_comparison(
            [e["name"] for e in events],
            [summaries[e["id"]]["act_income"]  for e in events],
            [summaries[e["id"]]["act_expense"] for e in events],
        )
        fig.update_layout(height=260)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with col2:
        section_header("Budget Split", "🥧")
        est_inc = sum(s["est_income"]  for s in summaries.values())
        est_exp = sum(s["est_expense"] for s in summaries.values())
        surplus = max(0, est_inc - est_exp)
        if est_inc + est_exp > 0:
            fig2 = donut(["Planned Income","Planned Expense","Surplus"],
                         [est_inc, est_exp, surplus])
            fig2.update_layout(height=260, legend=dict(orientation="h", y=-0.15))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    st.divider()

    # ── Event cards ───────────────────────────────────────────────────────
    section_header("Your Events", "📅")
    cols = st.columns(max(1, min(len(events), 3)))
    for i, ev in enumerate(events):
        s      = summaries[ev["id"]]
        ev_sym = get_symbol(ev.get("currency"))
        ph     = ev.get("phase","planning")
        with cols[i % 3]:
            st.markdown(f"**{ev['name']}**")
            st.caption(f"📍 {ev.get('venue') or '—'}  ·  {ph.upper()}")
            m1,m2,m3 = st.columns(3)
            m1.metric("Revenue",  f"{ev_sym}{s['act_income']:,.0f}")
            m2.metric("Expenses", f"{ev_sym}{s['act_expense']:,.0f}")
            m3.metric("Profit",   f"{ev_sym}{s['act_profit']:,.0f}")
            if st.button("📂 Open", key=f"su_open_{ev['id']}", use_container_width=True):
                st.session_state.active_event = ev["id"]
                st.session_state.page = "event_detail"; st.rerun()
            st.markdown("---")

    # ── Quick stats ───────────────────────────────────────────────────────
    st.divider()
    section_header("Quick Stats", "⚡")
    qa, qb, qc = st.columns(3)
    with qa:
        st.markdown("**Phase Distribution**")
        phase_counts = {}
        for e in events:
            ph = e.get("phase","planning")
            phase_counts[ph] = phase_counts.get(ph,0)+1
        for ph, cnt in phase_counts.items():
            st.write(f"{ph.title()}: {cnt}")
            st.progress(cnt / len(events))
    with qb:
        st.metric("📊 Avg Budget Accuracy", f"{avg_acc:.1f}%")
        st.caption("Across all events")
    with qc:
        margin = (total_pft / max(total_inc,1)) * 100
        st.metric("💹 Profit Margin", f"{margin:.1f}%",
                  delta=f"{'+' if total_pft>=0 else ''}{sym}{abs(total_pft):,.0f}")
        st.caption("Overall portfolio")


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI USER — SUPER ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def _super_admin_dashboard(user):
    sym = get_symbol()
    st.title("👑 Super Admin Dashboard")
    st.caption(f"🏢 {user.get('org_name','')}  ·  🔵 Multi User Mode  ·  Full system overview")
    st.divider()

    from database.schema import get_connection
    conn = get_connection()
    total_events    = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    active_events   = conn.execute("SELECT COUNT(*) FROM events WHERE status='active'").fetchone()[0]
    total_users     = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    pending_budgets = conn.execute("SELECT COUNT(*) FROM budget_proposals WHERE status='submitted'").fetchone()[0]
    total_inc  = conn.execute("SELECT COALESCE(SUM(amount),0) FROM actual_income").fetchone()[0]
    total_exp  = conn.execute("SELECT COALESCE(SUM(amount),0) FROM actual_expenses").fetchone()[0]
    conn.close()
    profit = total_inc - total_exp

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("📅 Total Events",    str(total_events))
    c2.metric("🔴 Active",          str(active_events))
    c3.metric("👥 Users",           str(total_users))
    c4.metric("⏳ Pending Budgets", str(pending_budgets))
    c5.metric("💰 Revenue",         f"{sym}{total_inc:,.0f}")
    c6.metric("📈 Profit",          f"{sym}{profit:,.0f}")
    st.divider()

    col1, col2 = st.columns([2,1])

    with col1:
        section_header("All Events", "📅")
        events = get_accessible_events(user["id"])
        if events:
            rows = []
            for ev in events:
                s      = get_event_summary(ev["id"])
                ev_sym = get_symbol(ev.get("currency"))
                rows.append({
                    "Event":    ev["name"],
                    "Status":   ev.get("status","—").title(),
                    "Phase":    ev.get("phase","—").title(),
                    "Revenue":  f"{ev_sym}{s['act_income']:,.0f}",
                    "Expenses": f"{ev_sym}{s['act_expense']:,.0f}",
                    "Profit":   f"{ev_sym}{s['act_profit']:,.0f}",
                    "Accuracy": f"{s['budget_accuracy']:.1f}%",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            bcols = st.columns(max(1, min(len(events),3)))
            for i, ev in enumerate(events):
                with bcols[i%3]:
                    if st.button(f"📂 {ev['name'][:18]}", key=f"sa_open_{ev['id']}",
                                 use_container_width=True):
                        st.session_state.active_event = ev["id"]
                        st.session_state.page = "event_detail"; st.rerun()
        else:
            empty_state("📅","No events yet")

    with col2:
        section_header("Pending Approvals", "⏳")
        pending = get_pending_proposals(user["id"])
        if pending:
            for p in pending[:5]:
                st.markdown(f"**{p['dept_name']}**")
                ev_name = p.get("event_name","")
                st.caption(f"{ev_name}  ·  {sym}{p['total_amount']:,.0f}  ·  {p['submitter_name']}")
                ca, cb = st.columns(2)
                if ca.button("✅", key=f"sa_app_{p['id']}", use_container_width=True):
                    from utils.budget_workflow import approve_proposal
                    res = approve_proposal(p["id"], user["id"])
                    st.success(res["message"]) if res["ok"] else st.error(res["message"])
                    st.rerun()
                if cb.button("❌", key=f"sa_rej_{p['id']}", use_container_width=True):
                    st.session_state[f"sa_rej_{p['id']}"] = True
                if st.session_state.get(f"sa_rej_{p['id']}"):
                    reason = st.text_input("Reason", key=f"sa_rej_r_{p['id']}")
                    if st.button("Send", key=f"sa_rej_s_{p['id']}"):
                        from utils.budget_workflow import reject_proposal
                        reject_proposal(p["id"], user["id"], reason)
                        st.session_state.pop(f"sa_rej_{p['id']}", None)
                        st.rerun()
                st.markdown("---")
        else:
            st.success("✅ No pending approvals")

    st.divider()
    col3, col4 = st.columns(2)
    with col3:
        section_header("Recent Activity", "📋")
        logs = get_audit_log(limit=8)
        icons = {"CREATE_EVENT":"📅","SUBMIT_PROPOSAL":"📋",
                 "APPROVE_PROPOSAL":"✅","REJECT_PROPOSAL":"❌","CREATE_USER":"👤"}
        for log in logs:
            icon = icons.get(log["action"],"•")
            st.write(f"{icon} **{log.get('user_name','System')}** — {log['action'].replace('_',' ').title()}")
            st.caption(f"{log.get('details','—')[:60]}  ·  {log['created_at'][:16]}")

    with col4:
        section_header("AI Alerts", "🤖")
        events_list = get_accessible_events(user["id"])
        alerts = False
        for ev in events_list[:5]:
            s = get_event_summary(ev["id"])
            if s["est_expense"] > 0:
                util = s["act_expense"] / s["est_expense"] * 100
                if util > 90:
                    st.error(f"🚨 **{ev['name']}**: Budget at {util:.0f}%")
                    alerts = True
            if s["act_profit"] < 0 and s["act_income"] > 0:
                st.error(f"📉 **{ev['name']}**: Running at a loss")
                alerts = True
        if not alerts:
            st.success("✅ All events within healthy parameters")


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI USER — FINANCE HEAD DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def _finance_dashboard(user):
    sym     = get_symbol()
    pending = get_pending_proposals(user["id"])
    events  = get_accessible_events(user["id"])

    st.title("💰 Finance Dashboard")
    st.caption("Budget approvals & financial overview  ·  🔵 Multi User Mode")
    st.divider()

    total_inc = sum(get_event_summary(e["id"])["act_income"]  for e in events)
    total_exp = sum(get_event_summary(e["id"])["act_expense"] for e in events)
    c1,c2,c3 = st.columns(3)
    c1.metric("⏳ Pending Approvals", str(len(pending)))
    c2.metric("💰 Total Revenue",     f"{sym}{total_inc:,.0f}")
    c3.metric("📈 Total Profit",      f"{sym}{total_inc-total_exp:,.0f}")
    st.divider()

    col1, col2 = st.columns([3,2])
    with col1:
        section_header("Budgets Awaiting Approval", "📋")
        if not pending:
            st.success("✅ No pending budgets")
        else:
            for p in pending:
                ev_sym = get_symbol()
                with st.container():
                    c1b,c2b = st.columns([3,1])
                    with c1b:
                        st.markdown(f"**{p['dept_name']}**  ·  {p.get('event_name','')}")
                        st.caption(f"by {p['submitter_name']}  ·  v{p.get('version',1)}")
                        st.metric("Amount", f"{ev_sym}{p['total_amount']:,.0f}")
                    with c2b:
                        if st.button("✅ Approve", key=f"f_app_{p['id']}", use_container_width=True):
                            from utils.budget_workflow import approve_proposal
                            res = approve_proposal(p["id"], user["id"])
                            st.success(res["message"]) if res["ok"] else st.error(res["message"])
                            st.rerun()
                        if st.button("❌ Reject", key=f"f_rej_{p['id']}", use_container_width=True,
                                     type="secondary"):
                            st.session_state[f"f_rej_{p['id']}"] = True
                    if st.session_state.get(f"f_rej_{p['id']}"):
                        reason = st.text_input("Rejection reason *", key=f"f_r_{p['id']}")
                        ra,rb  = st.columns(2)
                        if ra.button("Send", key=f"f_rs_{p['id']}"):
                            if reason.strip():
                                from utils.budget_workflow import reject_proposal
                                reject_proposal(p["id"], user["id"], reason.strip())
                                st.session_state.pop(f"f_rej_{p['id']}", None)
                                st.rerun()
                            else:
                                st.error("Reason required.")
                        if rb.button("Cancel", key=f"f_rc_{p['id']}"):
                            st.session_state.pop(f"f_rej_{p['id']}", None)
                            st.rerun()
                    st.markdown("---")

    with col2:
        section_header("Events Summary", "📊")
        for ev in events[:6]:
            s      = get_event_summary(ev["id"])
            ev_sym = get_symbol(ev.get("currency"))
            st.markdown(f"**{ev['name']}**")
            m1,m2  = st.columns(2)
            m1.metric("Revenue",  f"{ev_sym}{s['act_income']:,.0f}")
            m2.metric("Accuracy", f"{s['budget_accuracy']:.0f}%")
            st.progress(min(s["act_expense"]/max(s["est_expense"],1),1.0))
            st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI USER — DEPARTMENT HEAD DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def _dept_dashboard(user):
    st.title("🏢 Department Dashboard")
    st.caption("Your budget proposals & expenses  ·  🔵 Multi User Mode")
    st.divider()

    from utils.roles import get_user_dept_ids
    from utils.budget_workflow import get_proposals
    from utils.helpers import get_actual_expenses
    from database.schema import get_connection

    events = get_accessible_events(user["id"])
    if not events:
        empty_state("📅","No events assigned to you",
                    "Ask your Event Admin to assign you to an event.")
        return

    ev_map = {e["name"]: e for e in events}
    sel_ev = st.selectbox("Select Event", list(ev_map.keys()))
    ev     = ev_map[sel_ev]
    ev_sym = get_symbol(ev.get("currency"))

    dept_ids = get_user_dept_ids(user["id"], ev["id"])

    # ── Whole-Event Summary (visible to EVERY user, live-refreshing) ──────────
    _live_event_summary(ev["id"], ev["name"], ev_sym)
    st.divider()

    if not dept_ids:
        st.info("ℹ️ You are not assigned as head of any specific department, "
                "so you have view-only access above. Department-level budget "
                "editing is restricted to assigned Department Heads, Finance Head, "
                "Event Admin, or Super Admin.")
        return


    conn = get_connection()
    dept = conn.execute("SELECT * FROM departments WHERE id=?", (dept_ids[0],)).fetchone()
    conn.close()
    if not dept:
        return

    st.subheader(f"🏢 My Department: {dept['name']}")
    st.caption("Editable — you are Head of this department")
    st.divider()

    proposals     = get_proposals(ev["id"], dept_ids[0])
    approved_total= sum(p["total_amount"] for p in proposals if p["status"]=="approved")
    ae_all        = get_actual_expenses(ev["id"])
    dept_exp      = sum(r["amount"] for r in ae_all if r.get("department_id")==dept_ids[0])
    remaining     = approved_total - dept_exp
    pending_amt   = sum(p["total_amount"] for p in proposals if p["status"]=="submitted")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📋 Approved Budget", f"{ev_sym}{approved_total:,.0f}")
    c2.metric("💸 Spent",           f"{ev_sym}{dept_exp:,.0f}")
    c3.metric("💚 Remaining",       f"{ev_sym}{remaining:,.0f}")
    c4.metric("⏳ Pending",         f"{ev_sym}{pending_amt:,.0f}")

    if approved_total > 0:
        st.progress(min(dept_exp/approved_total, 1.0))
        st.caption(f"{dept_exp/approved_total*100:.1f}% of approved budget spent")

    st.divider()
    section_header("My Budget Proposals", "📋")

    if st.button("➕ Create New Budget Proposal"):
        st.session_state.page = "create_proposal"
        st.session_state.proposal_event_id = ev["id"]
        st.session_state.proposal_dept_id  = dept_ids[0]
        st.rerun()

    status_icons = {"draft":"📝","submitted":"⏳","approved":"✅","rejected":"❌"}
    if not proposals:
        empty_state("📋","No proposals yet","Click 'Create New Budget Proposal' to start.")
    else:
        for p in proposals:
            st.markdown(f"**{p['title']}**  ·  {status_icons.get(p['status'],'')} {p['status'].title()}")
            st.caption(f"v{p.get('version',1)}  ·  {ev_sym}{p['total_amount']:,.0f}")
            if p.get("reject_reason"):
                st.warning(f"💬 Reason: {p['reject_reason']}")
            ba,bb = st.columns(2)
            if ba.button("📂 View/Edit", key=f"dh_v_{p['id']}", use_container_width=True):
                st.session_state.page = "proposal_detail"
                st.session_state.active_proposal = p["id"]; st.rerun()
            if p["status"] in ("draft","rejected") and \
               bb.button("📤 Submit", key=f"dh_s_{p['id']}", use_container_width=True):
                from utils.budget_workflow import submit_proposal
                res = submit_proposal(p["id"], user["id"])
                st.success(res["message"]) if res["ok"] else st.error(res["message"])
                st.rerun()
            st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI USER — EVENT ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def _event_admin_dashboard(user):
    sym    = get_symbol()
    events = get_accessible_events(user["id"])

    st.title("🎯 Event Admin Dashboard")
    st.caption("🔵 Multi User Mode")
    st.divider()

    if not events:
        empty_state("📅","No events assigned yet"); return

    ev_map = {e["name"]: e for e in events}
    sel_ev = st.selectbox("Select Event", list(ev_map.keys()))
    ev     = ev_map[sel_ev]
    ev_sym = get_symbol(ev.get("currency"))
    s      = get_event_summary(ev["id"])

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💰 Revenue",  f"{ev_sym}{s['act_income']:,.0f}")
    c2.metric("📤 Expenses", f"{ev_sym}{s['act_expense']:,.0f}")
    c3.metric("📈 Profit",   f"{ev_sym}{s['act_profit']:,.0f}")
    c4.metric("🎯 Accuracy", f"{s['budget_accuracy']:.1f}%")
    st.divider()

    from utils.helpers import get_departments
    from utils.budget_workflow import get_proposals

    col1, col2 = st.columns(2)
    with col1:
        section_header("Departments","🏢")
        depts = get_departments(ev["id"])
        if depts:
            for d in depts:
                st.write(f"**{d['name']}**  ·  Head: {d.get('head_name') or 'TBD'}")
        else:
            empty_state("🏢","No departments yet")
        if st.button("📂 Open Event →", use_container_width=True):
            st.session_state.active_event = ev["id"]
            st.session_state.page = "event_detail"; st.rerun()

    with col2:
        section_header("Budget Status","📋")
        proposals = get_proposals(ev["id"])
        status_counts = {}
        for p in proposals:
            status_counts[p["status"]] = status_counts.get(p["status"],0)+1
        icons = {"draft":"📝","submitted":"⏳","approved":"✅","rejected":"❌"}
        if status_counts:
            for status,cnt in status_counts.items():
                st.write(f"{icons.get(status,'•')} {status.title()}: **{cnt}**")
        else:
            st.caption("No proposals yet")


# ══════════════════════════════════════════════════════════════════════════════
#  DEFAULT (member / unknown role)
# ══════════════════════════════════════════════════════════════════════════════

def _default_dashboard(user):
    st.title("📊 Dashboard")
    st.caption("🔵 Multi User Mode")
    st.divider()
    events = get_accessible_events(user["id"])
    if not events:
        empty_state("📅","No events accessible","Contact your admin to get assigned.")
        return
    for ev in events:
        s      = get_event_summary(ev["id"])
        ev_sym = get_symbol(ev.get("currency"))
        st.markdown(f"**{ev['name']}**")
        c1,c2 = st.columns(2)
        c1.metric("Revenue", f"{ev_sym}{s['act_income']:,.0f}")
        c2.metric("Profit",  f"{ev_sym}{s['act_profit']:,.0f}")
        if st.button(f"Open {ev['name']}", key=f"def_open_{ev['id']}"):
            st.session_state.active_event = ev["id"]
            st.session_state.page = "event_detail"; st.rerun()
        st.markdown("---")