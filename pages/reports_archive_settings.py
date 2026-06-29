"""EventLedger AI – Reports, Archive, Settings (native Streamlit)"""

import streamlit as st
import datetime
import pandas as pd
from utils.helpers import (
    get_events, get_event_summary, get_actual_income, get_actual_expenses,
    get_sponsors, get_vendors, get_estimated_expenses, get_departments, authenticate
)
from utils.export_engine import generate_pdf, generate_excel
from components.ui import section_header, empty_state
from utils.app_mode import get_app_mode, set_app_mode, is_single_user
from utils.currency import (get_global_currency, set_global_currency,
                            get_symbol, CURRENCIES, CURRENCY_LABELS)


def _dept_rows(event_id):
    depts   = get_departments(event_id)
    ee      = get_estimated_expenses(event_id)
    ae      = get_actual_expenses(event_id)
    dm = {d["name"]:{"name":d["name"],"est":0,"act":0} for d in depts}
    for r in ee:
        dn=r.get("dept_name","—"); dm.setdefault(dn,{"name":dn,"est":0,"act":0})["est"]+=r["amount"]
    for r in ae:
        dn=r.get("dept_name","—"); dm.setdefault(dn,{"name":dn,"est":0,"act":0})["act"]+=r["amount"]
    return list(dm.values())


# ── Reports ────────────────────────────────────────────────────────────────

def show_reports(user):
    st.title("📄 Reports")
    st.caption("Generate, preview & export financial reports")
    st.divider()

    events = get_events(user["id"])
    if not events:
        empty_state("📄","No events to report on"); return

    col_ev, col_rt = st.columns(2)
    with col_ev:
        ev_map   = {e["name"]: e for e in events}
        sel_name = st.selectbox("Select Event", list(ev_map.keys()))
    with col_rt:
        rtype = st.selectbox("Report Type", [
            "📋 Executive Summary","📊 Profit & Loss","💵 Income Report",
            "📤 Expense Report","🤝 Sponsor Report","🚚 Vendor Report",
            "🏢 Department Report","📦 Full Report"])

    ev      = ev_map[sel_name]
    ev_id   = ev["id"]
    s       = get_event_summary(ev_id)
    sym     = get_symbol(ev.get("currency") or get_global_currency())
    inc     = get_actual_income(ev_id)
    exp     = get_actual_expenses(ev_id)
    spo     = get_sponsors(ev_id)
    vnd     = get_vendors(ev_id)
    dr      = _dept_rows(ev_id)

    # Export buttons
    col_pdf, col_xl = st.columns(2)
    with col_pdf:
        pdf_b = generate_pdf(ev, s, inc, exp, spo, vnd)
        st.download_button("📄 Download PDF", data=pdf_b,
            file_name=f"{sel_name.replace(' ','_')}_{datetime.date.today()}.pdf",
            mime="application/pdf", use_container_width=True)
    with col_xl:
        xl_b = generate_excel(ev, s, inc, exp, spo, vnd, dr)
        st.download_button("📊 Download Excel", data=xl_b,
            file_name=f"{sel_name.replace(' ','_')}_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

    st.divider()
    rt = rtype.split(" ",1)[1]

    if rt in ("Executive Summary","Full Report"):
        _exec(ev, s, sym)
    if rt in ("Profit & Loss","Full Report"):
        _pl(ev, s, sym)
    if rt in ("Income Report","Full Report"):
        _income(ev, s, sym, inc)
    if rt in ("Expense Report","Full Report"):
        _expense(ev, s, sym, exp)
    if rt in ("Sponsor Report","Full Report"):
        _sponsor(ev, sym, spo)
    if rt in ("Vendor Report","Full Report"):
        _vendor(ev, sym, vnd)
    if rt in ("Department Report","Full Report"):
        _dept_report(ev, sym, dr)


def _exec(ev, s, sym):
    section_header("Executive Summary","📋")
    margin = (s["act_profit"]/max(s["act_income"],1))*100
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Revenue",    f"{sym}{s['act_income']:,.0f}")
    c2.metric("Expenses",   f"{sym}{s['act_expense']:,.0f}")
    c3.metric("Net Profit", f"{sym}{s['act_profit']:,.0f}")
    c4.metric("Margin",     f"{margin:.1f}%")
    c5.metric("Accuracy",   f"{s['budget_accuracy']:.1f}%")
    c6.metric("Sponsors",   f"{sym}{s['sponsors_total']:,.0f}")
    st.info(f"📍 **{ev.get('venue','—')}**  ·  📆 {ev.get('start_date','—')} → {ev.get('end_date','—')}  ·  👥 {ev.get('expected_attendees',0):,} attendees  ·  Report: {datetime.date.today()}")


def _pl(ev, s, sym):
    section_header("Profit & Loss Statement","📊")
    df = pd.DataFrame([
        {"Line Item":"Estimated Income",   "Amount":f"{sym}{s['est_income']:,.2f}"},
        {"Line Item":"Actual Income",      "Amount":f"{sym}{s['act_income']:,.2f}"},
        {"Line Item":"Income Variance",    "Amount":f"{sym}{s['income_variance']:+,.2f}"},
        {"Line Item":"Estimated Expenses", "Amount":f"{sym}{s['est_expense']:,.2f}"},
        {"Line Item":"Actual Expenses",    "Amount":f"{sym}{s['act_expense']:,.2f}"},
        {"Line Item":"Expense Variance",   "Amount":f"{sym}{s['expense_variance']:+,.2f}"},
        {"Line Item":"Estimated Profit",   "Amount":f"{sym}{s['est_profit']:,.2f}"},
        {"Line Item":"Actual Profit",      "Amount":f"{sym}{s['act_profit']:,.2f}"},
        {"Line Item":"Budget Accuracy",    "Amount":f"{s['budget_accuracy']:.1f}%"},
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _income(ev, s, sym, rows):
    section_header("Income Report","💵")
    c1,c2,c3 = st.columns(3)
    c1.metric("Estimated", f"{sym}{s['est_income']:,.0f}")
    c2.metric("Actual",    f"{sym}{s['act_income']:,.0f}")
    c3.metric("Variance",  f"{sym}{s['income_variance']:+,.0f}")
    if not rows:
        empty_state("💵","No income recorded"); return
    df = pd.DataFrame([{"Source":r["source"],"Category":r["category"],
                         "Amount":f"{sym}{r['amount']:,.0f}","Date":r.get("received_on","—"),
                         "Mode":r.get("payment_mode","—"),"Ref":r.get("reference","—")} for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.success(f"**Total: {sym}{sum(r['amount'] for r in rows):,.0f}**")


def _expense(ev, s, sym, rows):
    section_header("Expense Report","📤")
    c1,c2,c3 = st.columns(3)
    c1.metric("Estimated", f"{sym}{s['est_expense']:,.0f}")
    c2.metric("Actual",    f"{sym}{s['act_expense']:,.0f}")
    over = s["expense_variance"] > 0
    c3.metric("Over Budget" if over else "Saved", f"{sym}{abs(s['expense_variance']):,.0f}")
    if not rows:
        empty_state("📤","No expenses recorded"); return
    df = pd.DataFrame([{"Dept":r.get("dept_name","—"),"Category":r["category"],
                         "Description":r.get("description",""),"Amount":f"{sym}{r['amount']:,.0f}",
                         "Date":r.get("paid_on","—"),"Status":r.get("status","—")} for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.error(f"**Total: {sym}{sum(r['amount'] for r in rows):,.0f}**")


def _sponsor(ev, sym, rows):
    section_header("Sponsor Report","🤝")
    if not rows:
        empty_state("🤝","No sponsors for this event"); return
    total = sum(s["amount"] for s in rows)
    c1,c2 = st.columns(2)
    c1.metric("Total Sponsors", str(len(rows)))
    c2.metric("Total Funds",    f"{sym}{total:,.0f}")
    df = pd.DataFrame([{"Sponsor":s["name"],"Tier":s["tier"],
                         "Contact":s.get("contact_name","—"),"Email":s.get("contact_email","—"),
                         "Amount":f"{sym}{s['amount']:,.0f}",
                         "Share":f"{(s['amount']/max(total,1)*100):.1f}%",
                         "Status":s.get("status","confirmed")}
                        for s in sorted(rows,key=lambda x:x["amount"],reverse=True)])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _vendor(ev, sym, rows):
    section_header("Vendor Report","🚚")
    if not rows:
        empty_state("🚚","No vendors for this event"); return
    total = sum(v["contract_value"] for v in rows)
    c1,c2 = st.columns(2)
    c1.metric("Total Vendors",   str(len(rows)))
    c2.metric("Contract Value",  f"{sym}{total:,.0f}")
    df = pd.DataFrame([{"Vendor":v["name"],"Category":v["category"],
                         "Contact":v.get("contact_name","—"),
                         "Contract Value":f"{sym}{v['contract_value']:,.0f}",
                         "Share":f"{(v['contract_value']/max(total,1)*100):.1f}%",
                         "Status":v.get("status","active")}
                        for v in sorted(rows,key=lambda x:x["contract_value"],reverse=True)])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _dept_report(ev, sym, rows):
    section_header("Department Budget Report","🏢")
    if not rows or not any(d["est"] or d["act"] for d in rows):
        empty_state("🏢","No department data"); return
    t_est = sum(d["est"] for d in rows)
    t_act = sum(d["act"] for d in rows)
    t_var = t_act - t_est
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Departments",   str(len(rows)))
    c2.metric("Est. Budget",   f"{sym}{t_est:,.0f}")
    c3.metric("Actual Spend",  f"{sym}{t_act:,.0f}")
    c4.metric("Variance",      f"{sym}{t_var:+,.0f}")
    for d in sorted(rows, key=lambda x: x["act"], reverse=True):
        var = d["act"]-d["est"]; pct=(var/max(d["est"],1))*100
        util = min(d["act"]/max(d["est"],1), 1.0)
        status = "⚠️ Over" if var>0 else "✅ Under" if var<0 else "✔ On Track"
        st.write(f"**{d['name']}** — {sym}{d['act']:,.0f} / {sym}{d['est']:,.0f}  |  {pct:+.1f}%  |  {status}")
        st.progress(util)


# ── Archive ────────────────────────────────────────────────────────────────

def show_archive(user):
    st.title("📦 Archive")
    st.caption("Historical events & financial records")
    st.divider()

    events    = get_events(user["id"])
    completed = [e for e in events if e.get("status")=="completed" or e.get("phase") in ("comparison","completed")]

    if not completed:
        empty_state("📦","No archived events yet","Events with phase 'comparison' or 'completed' appear here."); return

    st.caption(f"{len(completed)} archived event(s)")
    for ev in completed:
        s = get_event_summary(ev["id"])
        margin = (s["act_profit"]/max(s["act_income"],1))*100
        with st.container():
            st.markdown(f"**📁 {ev['name']}**")
            st.caption(f"📍 {ev.get('venue','—')}  ·  📆 {ev.get('start_date','—')} → {ev.get('end_date','—')}  ·  👥 {ev.get('expected_attendees',0):,}")
            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Revenue",   f"${s['act_income']:,.0f}")
            c2.metric("Expenses",  f"${s['act_expense']:,.0f}")
            c3.metric("Profit",    f"${s['act_profit']:,.0f}")
            c4.metric("Accuracy",  f"{s['budget_accuracy']:.1f}%")
            c5.metric("Margin",    f"{margin:.1f}%")
            if st.button(f"📂 Open {ev['name'][:20]}", key=f"arch_{ev['id']}"):
                st.session_state.active_event = ev["id"]
                st.session_state.page = "event_detail"
                st.rerun()
            st.divider()


# ── Settings ───────────────────────────────────────────────────────────────

def show_settings(user):
    st.title("⚙️ Settings")
    st.caption("Account, preferences & security")
    st.divider()

    tab1, tab2, tab3 = st.tabs(["👤 Profile","🔒 Security","ℹ️ About"])

    with tab1:
        section_header("Organization Profile","🏢")
        with st.form("profile_form"):
            c1,c2 = st.columns(2)
            p_name = c1.text_input("Full Name",    value=user.get("name",""))
            p_org  = c2.text_input("Organization", value=user.get("org_name",""))
            st.text_input("Email", value=user.get("email",""), disabled=True)
            st.text_input("Role",  value=user.get("role",""),  disabled=True)
            if st.form_submit_button("💾 Save Profile", use_container_width=True):
                from database.schema import get_connection
                conn = get_connection()
                conn.execute("UPDATE users SET name=?,org_name=? WHERE id=?",
                             (p_name.strip(), p_org.strip(), user["id"]))
                conn.commit(); conn.close()
                st.session_state.user["name"]     = p_name.strip()
                st.session_state.user["org_name"] = p_org.strip()
                st.success("✅ Profile updated!")

        st.divider()
        section_header("App Info","🎨")
        st.info("**Theme:** Dark  ·  **DB:** SQLite  ·  **Version:** EventLedger AI v2.0  ·  **Export:** ReportLab + OpenPyXL")

        st.divider()
        section_header("App Mode", "🔄")
        st.caption("Switch between Single User (you alone) and Multi User (team with roles & approvals).")

        current_mode = get_app_mode()

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            su_type  = "primary" if current_mode == "single_user" else "secondary"
            su_label = "✅ Single User (Active)" if current_mode == "single_user" else "👤 Single User"
            if st.button(su_label, key="mode_single", use_container_width=True,
                         type=su_type if su_type == "primary" else "secondary"):
                if current_mode != "single_user":
                    set_app_mode("single_user")
                    st.session_state.pop("app_mode", None)
                    st.success("✅ Switched to **Single User** mode. Refresh page.")
                    st.rerun()
        with col_m2:
            mu_type  = "primary" if current_mode == "multi_user" else "secondary"
            mu_label = "✅ Multi User (Active)" if current_mode == "multi_user" else "👥 Multi User"
            if st.button(mu_label, key="mode_multi", use_container_width=True,
                         type=mu_type if mu_type == "primary" else "secondary"):
                if current_mode != "multi_user":
                    set_app_mode("multi_user")
                    st.session_state.pop("app_mode", None)
                    st.success("✅ Switched to **Multi User** mode. Refresh page.")
                    st.rerun()

        if current_mode == "single_user":
            st.info(
                "🟢 **Single User Mode** — You have full access to everything. "
                "No roles, no approval workflows. "
                "Perfect for solo event managers."
            )
        else:
            st.info(
                "🔵 **Multi User Mode** — Role-based access with approval workflows. "
                "Super Admin → Event Admin → Finance Head → Department Heads. "
                "Perfect for teams managing large events."
            )

        st.divider()
        section_header("Global Currency", "💱")
        st.caption("This currency applies across all pages, dashboards, and reports. Each event can also override it individually.")

        cur_code   = get_global_currency()
        cur_keys   = list(CURRENCIES.keys())
        cur_idx    = cur_keys.index(cur_code) if cur_code in cur_keys else 0

        col_cur, col_btn = st.columns([3, 1])
        with col_cur:
            new_cur = st.selectbox(
                "Select Default Currency",
                options=cur_keys,
                format_func=lambda x: CURRENCY_LABELS.get(x, x),
                index=cur_idx,
                key="global_cur_sel",
                label_visibility="collapsed",
            )
        with col_btn:
            st.markdown("<div style='margin-top:0px'></div>", unsafe_allow_html=True)
            if st.button("💾 Save Currency", use_container_width=True, key="save_cur_btn"):
                set_global_currency(new_cur)
                st.success(f"✅ Default currency changed to **{CURRENCY_LABELS.get(new_cur, new_cur)}**")
                st.rerun()

        from utils.currency import get_symbol as _gs
        st.markdown(f"**Current:** {CURRENCY_LABELS.get(cur_code, cur_code)}  ·  Symbol: **{_gs(cur_code)}**")

    with tab2:
        section_header("Change Password","🔒")
        with st.form("pw_form"):
            old_pw  = st.text_input("Current Password", type="password")
            new_pw  = st.text_input("New Password",     type="password")
            new_pw2 = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("🔐 Update Password", use_container_width=True):
                if not all([old_pw, new_pw, new_pw2]):
                    st.error("All fields required.")
                elif new_pw != new_pw2:
                    st.error("Passwords do not match.")
                elif len(new_pw) < 6:
                    st.error("Minimum 6 characters.")
                else:
                    if not authenticate(user["email"], old_pw):
                        st.error("Current password incorrect.")
                    else:
                        from utils.helpers import hash_password
                        from database.schema import get_connection
                        conn = get_connection()
                        conn.execute("UPDATE users SET password=? WHERE id=?",
                                     (hash_password(new_pw), user["id"]))
                        conn.commit(); conn.close()
                        st.success("✅ Password updated!")
        st.divider()
        st.warning("⚠️ **Danger Zone** — Account deletion is permanent. Contact support to delete your account.")

    with tab3:
        st.markdown("""
### EventLedger AI v1.0

**Stack:** Streamlit · Python · SQLite · Plotly · ReportLab · OpenPyXL

**Phases Complete:**
- ✅ Phase 1 – Foundation (Auth, Dashboard, Events, Departments)
- ✅ Phase 2 – Planning (Estimated Budget, Income, Expenses)
- ✅ Phase 3 – Execution (Actual Income, Expenses, Sponsors, Vendors)
- ✅ Phase 4 – Comparison (Variance Analysis, Health Score)
- ✅ Phase 5 – Analytics (Charts, KPIs, Rankings, Waterfall)
- ✅ Phase 6 – Reports (7 report types, PDF & Excel Export)
- ✅ Phase 7 – AI Insights (Smart Alerts, Recommendations, Forecasting)
- ✅ Phase 8 – Administration (Archive, Settings, Password Change)
        """)
