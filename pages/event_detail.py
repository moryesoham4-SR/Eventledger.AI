"""EventLedger AI – Event Detail: full lifecycle with department line-item drill-down"""

import streamlit as st
import datetime
import pandas as pd

from utils.helpers import (
    get_event, get_departments, add_department, delete_department,
    get_estimated_income, add_estimated_income, delete_estimated_income,
    get_estimated_expenses, get_estimated_expenses_by_dept,
    add_estimated_expense, update_estimated_expense, delete_estimated_expense,
    get_actual_income, add_actual_income, delete_actual_income,
    get_actual_expenses, get_actual_expenses_by_dept,
    add_actual_expense, update_actual_expense, delete_actual_expense,
    get_sponsors, add_sponsor, delete_sponsor,
    get_vendors, add_vendor, delete_vendor,
    get_event_summary,
)
from utils.charts import bar_comparison, donut, dept_bar, health_gauge, sponsor_scatter, COLORS
from components.ui import section_header, empty_state
from utils.currency import get_symbol, get_global_currency

# ── Constants ────────────────────────────────────────────────────────────────
INCOME_CATS  = ["Tickets","Sponsor","Merchandise","Food & Beverage",
                "Workshop","Exhibition","Grant","Donation","Other"]
EXPENSE_CATS = ["Marketing","Venue","Technology","Catering","Security",
                "Logistics","Transport","Entertainment","Staffing",
                "Printing","Decoration","Equipment","Miscellaneous"]
PAY_MODES    = ["Cash","Bank Transfer","UPI","Card","Cheque","Online","DD"]
TIERS        = ["Platinum","Gold","Silver","Bronze","Associate","In-Kind"]
VENDOR_CATS  = ["AV Equipment","Catering","Security","Logistics","Printing",
                "Decoration","Photography","Technology","Staffing","Venue","Other"]
UNITS        = ["unit","pcs","kg","litre","hour","day","set","lot","trip","person","sq.ft","other"]

def _sym(ev):
    """Event-level currency overrides global; both fall back to INR."""
    code = ev.get("currency") or get_global_currency()
    return get_symbol(code)

def _dept_id_map(depts):
    return {d["name"]: d["id"] for d in depts}


# ══════════════════════════════════════════════════════════════════════════════
#  PLANNING TAB
# ══════════════════════════════════════════════════════════════════════════════
def _planning(ev, depts, sym):
    st.subheader("📋 Planning")
    pt = st.tabs(["🏢 Departments", "💵 Est. Income", "📤 Est. Expenses — by Dept", "📊 Budget Summary"])

    # ── Departments ──────────────────────────────────────────────────────────
    with pt[0]:
        section_header("Departments", "🏢")
        with st.expander("➕ Add Department", expanded=not bool(depts)):
            with st.form("add_dept", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                d_name = c1.text_input("Department Name *", placeholder="e.g. Logistics")
                d_head = c2.text_input("Department Head",   placeholder="e.g. Ravi Kumar")
                d_mgr  = c3.text_input("Manager",           placeholder="e.g. Priya Shah")
                if st.form_submit_button("➕ Add Department", use_container_width=True):
                    if d_name.strip():
                        add_department(ev["id"], d_name.strip(), d_head, d_mgr, "#6366f1")
                        st.success(f"Department '{d_name}' added!")
                        st.rerun()
                    else:
                        st.error("Department name is required.")

        if not depts:
            empty_state("🏢", "No departments yet",
                        "Add departments first (e.g. Logistics, Marketing, Tech, Catering)")
        else:
            df = pd.DataFrame([{
                "Dept": d["name"],
                "Head": d.get("head_name") or "—",
                "Manager": d.get("manager") or "—"
            } for d in depts])
            st.dataframe(df, use_container_width=True, hide_index=True)
            with st.expander("🗑 Delete a Department"):
                d_to_del = st.selectbox("Select department to delete",
                                         [d["name"] for d in depts], key="del_dept_sel")
                if st.button("Delete Department", type="secondary"):
                    did = _dept_id_map(depts).get(d_to_del)
                    if did:
                        delete_department(did)
                        st.rerun()

    # ── Estimated Income ─────────────────────────────────────────────────────
    with pt[1]:
        ei_rows = get_estimated_income(ev["id"])
        section_header("Estimated Income Sources", "💵")
        with st.expander("➕ Add Income Source"):
            with st.form("add_ei", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                ei_src   = c1.text_input("Source *",  placeholder="e.g. Ticket Sales")
                ei_cat   = c2.selectbox("Category",   INCOME_CATS)
                ei_amt   = c3.number_input(f"Amount ({sym})", min_value=0.0, step=100.0)
                ei_notes = st.text_input("Notes (optional)")
                if st.form_submit_button("Add", use_container_width=True):
                    if ei_src.strip():
                        add_estimated_income(ev["id"], ei_src.strip(), ei_cat, ei_amt, ei_notes)
                        st.rerun()
                    else:
                        st.error("Source name required.")

        if not ei_rows:
            empty_state("💵", "No income sources added yet")
        else:
            total = sum(r["amount"] for r in ei_rows)
            df = pd.DataFrame([{
                "Source":   r["source"],
                "Category": r["category"],
                f"Amount ({sym})": f"{r['amount']:,.0f}",
                "Notes":    r.get("notes") or "—"
            } for r in ei_rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.success(f"**Total Estimated Income: {sym}{total:,.0f}**")
            with st.expander("🗑 Delete an income source"):
                src_names = [f"{r['source']} ({sym}{r['amount']:,.0f})" for r in ei_rows]
                sel = st.selectbox("Select to delete", src_names, key="del_ei_sel")
                if st.button("Delete", type="secondary", key="del_ei_btn"):
                    idx = src_names.index(sel)
                    delete_estimated_income(ei_rows[idx]["id"])
                    st.rerun()

    # ── Estimated Expenses — Department Drill-Down ────────────────────────────
    with pt[2]:
        section_header("Estimated Expenses — by Department", "📤")

        if not depts:
            st.warning("⚠️ Please add departments first (in the 🏢 Departments tab) before adding expenses.")
        else:
            # Select which department to work on
            dept_names = [d["name"] for d in depts]
            sel_dept   = st.selectbox("📂 Select Department to view / add items",
                                       dept_names, key="ee_dept_sel")
            sel_dept_id = _dept_id_map(depts)[sel_dept]

            # Items for this dept
            dept_items = get_estimated_expenses_by_dept(ev["id"], sel_dept_id)
            dept_total = sum(r["amount"] for r in dept_items)

            st.markdown(f"### 🏢 {sel_dept}  —  Budget: **{sym}{dept_total:,.0f}**")

            # ── Add line item form ──────────────────────────────────────
            with st.expander(f"➕ Add Line Item to {sel_dept}", expanded=not bool(dept_items)):
                with st.form(f"add_ee_{sel_dept_id}", clear_on_submit=True):
                    st.markdown("**Item Details**")
                    c1, c2 = st.columns(2)
                    ee_item    = c1.text_input("Item Name *",
                        placeholder="e.g. Vehicle Rental, DJ System, Banners")
                    ee_cat_sel = c2.selectbox("Category", EXPENSE_CATS + ["Other"])

                    # "Other" — user specifies custom category
                    ee_cat_custom = ""
                    if ee_cat_sel == "Other":
                        ee_cat_custom = st.text_input(
                            "Specify Category *",
                            placeholder="e.g. Event Permit, Rain Cover, Insurance"
                        )

                    c3, c4, c5 = st.columns(3)
                    ee_qty  = c3.number_input("Quantity", min_value=0.0, value=1.0, step=1.0)
                    ee_unit = c4.selectbox("Unit", UNITS)
                    ee_amt  = c5.number_input(f"Total Amount ({sym})", min_value=0.0, step=100.0)
                    ee_desc  = st.text_input("Description / Specification",
                        placeholder="e.g. 32-seater bus, return trip, 2 days")
                    ee_notes = st.text_input("Internal Notes (optional)")
                    if st.form_submit_button(f"Add to {sel_dept}", use_container_width=True):
                        if not ee_item.strip():
                            st.error("Item name is required.")
                        elif ee_cat_sel == "Other" and not ee_cat_custom.strip():
                            st.error("Please specify the category.")
                        else:
                            final_cat = ee_cat_custom.strip() if ee_cat_sel == "Other" else ee_cat_sel
                            add_estimated_expense(
                                event_id=ev["id"], dept_id=sel_dept_id,
                                category=final_cat, item_name=ee_item.strip(),
                                description=ee_desc.strip(), amount=ee_amt,
                                quantity=ee_qty, unit=ee_unit, notes=ee_notes
                            )
                            st.rerun()

            # ── Line items table ────────────────────────────────────────
            if not dept_items:
                empty_state("📋", f"No items added to {sel_dept} yet",
                            "Use the form above to add line items.")
            else:
                # Grouped by category
                cats_in_dept = sorted(set(r["category"] for r in dept_items))
                for cat in cats_in_dept:
                    cat_items = [r for r in dept_items if r["category"] == cat]
                    cat_total = sum(r["amount"] for r in cat_items)
                    st.markdown(f"**{cat}** — {sym}{cat_total:,.0f}")

                    rows_display = []
                    for r in cat_items:
                        unit_price = r["amount"] / max(r.get("quantity") or 1, 1)
                        rows_display.append({
                            "Item":          r.get("item_name") or r.get("description") or "—",
                            "Qty":           f"{r.get('quantity') or 1:.0f} {r.get('unit') or ''}",
                            "Unit Price":    f"{sym}{unit_price:,.0f}",
                            f"Total ({sym})": f"{r['amount']:,.0f}",
                            "Spec / Notes":  r.get("description") or r.get("notes") or "—",
                        })
                    st.dataframe(pd.DataFrame(rows_display),
                                 use_container_width=True, hide_index=True)

                st.markdown(f"**{sel_dept} Total: {sym}{dept_total:,.0f}**")

                # Delete item
                with st.expander(f"🗑 Delete an item from {sel_dept}"):
                    item_labels = [
                        f"{r.get('item_name') or r.get('description','—')} ({sym}{r['amount']:,.0f})"
                        for r in dept_items
                    ]
                    del_sel = st.selectbox("Select item", item_labels, key=f"del_ee_item_{sel_dept_id}")
                    if st.button("Delete Item", type="secondary", key=f"del_ee_btn_{sel_dept_id}"):
                        idx = item_labels.index(del_sel)
                        delete_estimated_expense(dept_items[idx]["id"])
                        st.rerun()

            # ── All departments overview ────────────────────────────────
            st.divider()
            section_header("All Departments Overview", "📊")
            all_ee = get_estimated_expenses(ev["id"])
            if all_ee:
                dept_totals = {}
                for r in all_ee:
                    dn = r.get("dept_name") or "Unassigned"
                    dept_totals[dn] = dept_totals.get(dn, 0) + r["amount"]
                grand_total = sum(dept_totals.values())

                overview_rows = []
                for dn, tot in sorted(dept_totals.items(), key=lambda x: x[1], reverse=True):
                    overview_rows.append({
                        "Department":    dn,
                        f"Budget ({sym})": f"{tot:,.0f}",
                        "Share":         f"{(tot/max(grand_total,1)*100):.1f}%",
                    })
                    st.write(f"**{dn}** — {sym}{tot:,.0f}  ({(tot/max(grand_total,1)*100):.1f}%)")
                    st.progress(tot / max(grand_total, 1))

                st.success(f"**Grand Total Estimated Budget: {sym}{grand_total:,.0f}**")

    # ── Budget Summary ────────────────────────────────────────────────────────
    with pt[3]:
        section_header("Budget Summary", "📊")
        ei_all = get_estimated_income(ev["id"])
        ee_all = get_estimated_expenses(ev["id"])
        t_inc  = sum(r["amount"] for r in ei_all)
        t_exp  = sum(r["amount"] for r in ee_all)
        surplus = t_inc - t_exp
        margin  = (surplus / max(t_inc, 1)) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Est. Income",   f"{sym}{t_inc:,.0f}")
        c2.metric("Est. Expenses", f"{sym}{t_exp:,.0f}")
        c3.metric("Surplus",       f"{sym}{surplus:,.0f}")
        c4.metric("Margin",        f"{margin:.1f}%")

        if ei_all or ee_all:
            col1, col2 = st.columns(2)
            with col1:
                if ei_all:
                    fig = donut([r["source"] for r in ei_all],
                                [r["amount"] for r in ei_all], "Income Sources")
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            with col2:
                if ee_all:
                    dept_totals = {}
                    for r in ee_all:
                        dn = r.get("dept_name") or "Unassigned"
                        dept_totals[dn] = dept_totals.get(dn, 0) + r["amount"]
                    fig2 = donut(list(dept_totals.keys()), list(dept_totals.values()),
                                 "Budget by Department")
                    fig2.update_layout(height=300)
                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
#  EXECUTION TAB
# ══════════════════════════════════════════════════════════════════════════════
def _execution(ev, depts, sym):
    st.subheader("💰 Execution")
    et = st.tabs(["💵 Income", "📤 Expenses — by Dept", "🤝 Sponsors", "🚚 Vendors"])

    # ── Actual Income ─────────────────────────────────────────────────────────
    with et[0]:
        ai_rows = get_actual_income(ev["id"])
        section_header("Actual Income Received", "💵")
        st.info("💡 **Sponsor amounts are auto-added here** when you add a sponsor in the Sponsors tab. No need to enter them manually.")
        with st.expander("➕ Record Income"):
            with st.form("add_ai", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                ai_src  = c1.text_input("Source *", placeholder="e.g. Online Ticket Sales")
                ai_cat  = c2.selectbox("Category", INCOME_CATS)
                ai_amt  = c3.number_input(f"Amount ({sym})", min_value=0.0, step=100.0)
                c4, c5, c6 = st.columns(3)
                ai_date = c4.date_input("Received On", value=datetime.date.today())
                ai_mode = c5.selectbox("Payment Mode", PAY_MODES)
                ai_ref  = c6.text_input("Reference / TXN #")
                ai_notes = st.text_input("Notes")
                if st.form_submit_button("Record Income", use_container_width=True):
                    if ai_src.strip():
                        add_actual_income(ev["id"], ai_src.strip(), ai_cat, ai_amt,
                                          str(ai_date), ai_mode, ai_ref, ai_notes)
                        st.rerun()
                    else:
                        st.error("Source is required.")

        if not ai_rows:
            empty_state("💵", "No income recorded yet")
        else:
            total = sum(r["amount"] for r in ai_rows)
            df = pd.DataFrame([{
                "Source":    r["source"],
                "Category":  r["category"],
                f"Amount ({sym})": f"{r['amount']:,.0f}",
                "Date":      r.get("received_on", "—"),
                "Mode":      r.get("payment_mode", "—"),
                "Reference": r.get("reference") or "—",
                "Type":      "🤝 Sponsor" if r.get("sponsor_id") else "✏️ Manual",
            } for r in ai_rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.success(f"**Total Actual Income: {sym}{total:,.0f}**")
            with st.expander("🗑 Delete an entry"):
                manual_rows = [r for r in ai_rows if not r.get("sponsor_id")]
                if not manual_rows:
                    st.caption("No manual entries to delete. Sponsor entries are deleted via the Sponsors tab.")
                else:
                    labels = [f"{r['source']} — {sym}{r['amount']:,.0f} ({r.get('received_on','—')})"
                              for r in manual_rows]
                    sel = st.selectbox("Select", labels, key="del_ai_sel")
                    if st.button("Delete", type="secondary", key="del_ai_btn"):
                        delete_actual_income(manual_rows[labels.index(sel)]["id"])
                        st.rerun()

    # ── Actual Expenses — Department Drill-Down ───────────────────────────────
    with et[1]:
        section_header("Actual Expenses — by Department", "📤")

        if not depts:
            st.warning("⚠️ Add departments first (Planning → Departments tab).")
        else:
            dept_names  = [d["name"] for d in depts]
            sel_dept    = st.selectbox("📂 Select Department",
                                        dept_names, key="ae_dept_sel")
            sel_dept_id = _dept_id_map(depts)[sel_dept]

            dept_items  = get_actual_expenses_by_dept(ev["id"], sel_dept_id)
            dept_total  = sum(r["amount"] for r in dept_items)

            # Also get estimated for this dept to show variance
            est_items = get_estimated_expenses_by_dept(ev["id"], sel_dept_id)
            est_total = sum(r["amount"] for r in est_items)
            variance  = dept_total - est_total
            var_label = f"⚠️ Over by {sym}{abs(variance):,.0f}" if variance > 0 else \
                        f"✅ Under by {sym}{abs(variance):,.0f}" if variance < 0 else "✔ On Track"

            c1, c2, c3 = st.columns(3)
            c1.metric("Est. Budget",  f"{sym}{est_total:,.0f}")
            c2.metric("Actual Spent", f"{sym}{dept_total:,.0f}")
            c3.metric("Variance",     var_label)

            # ── Add actual expense line item ────────────────────────────
            with st.expander(f"➕ Add Expense to {sel_dept}", expanded=not bool(dept_items)):
                with st.form(f"add_ae_{sel_dept_id}", clear_on_submit=True):
                    st.markdown("**Expense Details**")
                    c1, c2 = st.columns(2)
                    ae_item    = c1.text_input("Item Name *",
                        placeholder="e.g. Vehicle Rental, Sound System")
                    ae_cat_sel = c2.selectbox("Category", EXPENSE_CATS + ["Other"])

                    # "Other" — user specifies custom category
                    ae_cat_custom = ""
                    if ae_cat_sel == "Other":
                        ae_cat_custom = st.text_input(
                            "Specify Category *",
                            placeholder="e.g. Generator Rental, Medical Kit, Lost & Found"
                        )

                    c3, c4, c5 = st.columns(3)
                    ae_qty  = c3.number_input("Quantity", min_value=0.0, value=1.0, step=1.0)
                    ae_unit = c4.selectbox("Unit", UNITS)
                    ae_amt  = c5.number_input(f"Total Amount ({sym})", min_value=0.0, step=100.0)
                    ae_desc = st.text_input("Description / Invoice Detail",
                        placeholder="e.g. Invoice #1234, Vendor: XYZ")
                    c6, c7, c8 = st.columns(3)
                    ae_date = c6.date_input("Paid On", value=datetime.date.today())
                    ae_mode = c7.selectbox("Payment Mode", PAY_MODES)
                    ae_stat = c8.selectbox("Status", ["paid", "pending", "partial"])
                    ae_ref  = st.text_input("Reference / Receipt #")
                    if st.form_submit_button(f"Add to {sel_dept}", use_container_width=True):
                        if not ae_item.strip():
                            st.error("Item name is required.")
                        elif ae_cat_sel == "Other" and not ae_cat_custom.strip():
                            st.error("Please specify the category.")
                        else:
                            final_cat = ae_cat_custom.strip() if ae_cat_sel == "Other" else ae_cat_sel
                            add_actual_expense(
                                event_id=ev["id"], dept_id=sel_dept_id,
                                category=final_cat, item_name=ae_item.strip(),
                                description=ae_desc.strip(), amount=ae_amt,
                                paid_on=str(ae_date), payment_mode=ae_mode,
                                status=ae_stat, quantity=ae_qty, unit=ae_unit,
                                reference=ae_ref
                            )
                            st.rerun()

            # ── Expense items grouped by category ───────────────────────
            if not dept_items:
                empty_state("📋", f"No expenses recorded for {sel_dept} yet")
            else:
                cats_in_dept = sorted(set(r["category"] for r in dept_items))
                for cat in cats_in_dept:
                    cat_items = [r for r in dept_items if r["category"] == cat]
                    cat_total = sum(r["amount"] for r in cat_items)
                    st.markdown(f"**{cat}** — {sym}{cat_total:,.0f}")

                    rows_display = []
                    for r in cat_items:
                        unit_price = r["amount"] / max(r.get("quantity") or 1, 1)
                        stat_icon  = {"paid": "✅", "pending": "⏳", "partial": "⚠️"}.get(
                            r.get("status", "paid"), "—")
                        rows_display.append({
                            "Item":          r.get("item_name") or r.get("description") or "—",
                            "Qty":           f"{r.get('quantity') or 1:.0f} {r.get('unit') or ''}",
                            "Unit Price":    f"{sym}{unit_price:,.0f}",
                            f"Total ({sym})": f"{r['amount']:,.0f}",
                            "Date":          r.get("paid_on") or "—",
                            "Mode":          r.get("payment_mode") or "—",
                            "Status":        f"{stat_icon} {r.get('status','paid')}",
                            "Ref":           r.get("reference") or "—",
                        })
                    st.dataframe(pd.DataFrame(rows_display),
                                 use_container_width=True, hide_index=True)

                st.error(f"**{sel_dept} Total Spent: {sym}{dept_total:,.0f}**")

                with st.expander(f"🗑 Delete an item from {sel_dept}"):
                    item_labels = [
                        f"{r.get('item_name') or r.get('description','—')} ({sym}{r['amount']:,.0f})"
                        for r in dept_items
                    ]
                    del_sel = st.selectbox("Select item", item_labels, key=f"del_ae_item_{sel_dept_id}")
                    if st.button("Delete Item", type="secondary", key=f"del_ae_btn_{sel_dept_id}"):
                        idx = item_labels.index(del_sel)
                        delete_actual_expense(dept_items[idx]["id"])
                        st.rerun()

            # ── All departments overview ────────────────────────────────
            st.divider()
            section_header("All Departments — Spend Overview", "📊")
            all_ae  = get_actual_expenses(ev["id"])
            all_ee2 = get_estimated_expenses(ev["id"])
            if all_ae or all_ee2:
                dept_est2, dept_act2 = {}, {}
                for r in all_ee2:
                    dn = r.get("dept_name") or "Unassigned"
                    dept_est2[dn] = dept_est2.get(dn, 0) + r["amount"]
                for r in all_ae:
                    dn = r.get("dept_name") or "Unassigned"
                    dept_act2[dn] = dept_act2.get(dn, 0) + r["amount"]
                all_depts2 = sorted(set(list(dept_est2) + list(dept_act2)))
                for dn in all_depts2:
                    est_v = dept_est2.get(dn, 0)
                    act_v = dept_act2.get(dn, 0)
                    pct   = (act_v / max(est_v, 1))
                    var_s = f"⚠️ Over" if act_v > est_v else "✅ Under" if act_v < est_v else "✔ On Track"
                    st.write(f"**{dn}** — Spent: {sym}{act_v:,.0f} / Budget: {sym}{est_v:,.0f}  {var_s}")
                    st.progress(min(pct, 1.0))

    # ── Sponsors ─────────────────────────────────────────────────────────────
    with et[2]:
        sp_rows = get_sponsors(ev["id"])
        section_header("Sponsors", "🤝")
        with st.expander("➕ Add Sponsor"):
            with st.form("add_sp", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                sp_name = c1.text_input("Sponsor Name *")
                sp_tier = c2.selectbox("Tier", TIERS)
                sp_amt  = c3.number_input(f"Amount ({sym})", min_value=0.0, step=500.0)
                c4, c5  = st.columns(2)
                sp_cn   = c4.text_input("Contact Name")
                sp_ce   = c5.text_input("Contact Email")
                if st.form_submit_button("Add Sponsor", use_container_width=True):
                    if sp_name.strip():
                        add_sponsor(ev["id"], sp_name.strip(), sp_tier, sp_cn, sp_ce, sp_amt)
                        st.rerun()

        if not sp_rows:
            empty_state("🤝", "No sponsors added yet")
        else:
            total_sp = sum(s["amount"] for s in sp_rows)
            df = pd.DataFrame([{
                "Sponsor":   s["name"],
                "Tier":      s["tier"],
                "Contact":   s.get("contact_name") or "—",
                "Email":     s.get("contact_email") or "—",
                f"Amount ({sym})": f"{s['amount']:,.0f}",
                "Status":    s.get("status", "confirmed"),
            } for s in sp_rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.success(f"**Total Sponsor Funds: {sym}{total_sp:,.0f}**")
            with st.expander("🗑 Delete a sponsor"):
                labels = [f"{s['name']} — {sym}{s['amount']:,.0f}" for s in sp_rows]
                sel = st.selectbox("Select", labels, key="del_sp_sel")
                if st.button("Delete", type="secondary", key="del_sp_btn"):
                    delete_sponsor(sp_rows[labels.index(sel)]["id"])
                    st.rerun()

    # ── Vendors ───────────────────────────────────────────────────────────────
    with et[3]:
        vd_rows = get_vendors(ev["id"])
        section_header("Vendors", "🚚")
        with st.expander("➕ Add Vendor"):
            with st.form("add_vd", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                vd_name = c1.text_input("Vendor Name *", placeholder="e.g. AudioVision Pro")
                vd_cat_sel = c2.selectbox("Category", VENDOR_CATS + ["Other"])
                vd_cv   = c3.number_input(f"Contract Value ({sym})", min_value=0.0, step=100.0)

                # "Other" category — let user specify
                vd_cat_custom = ""
                if vd_cat_sel == "Other":
                    vd_cat_custom = st.text_input("Specify Category *",
                        placeholder="e.g. Event Insurance, Waste Management, Permissions")

                # Department — which dept is this vendor serving?
                dept_opts = {"No specific department": None}
                dept_opts.update({d["name"]: d["id"] for d in depts})
                vd_dept = st.selectbox("Expense Dept (which dept bears this cost?)",
                                        list(dept_opts.keys()))

                c4, c5 = st.columns(2)
                vd_cn = c4.text_input("Contact Name")
                vd_ce = c5.text_input("Contact Email")
                vd_notes = st.text_input("Notes (optional)")

                if st.form_submit_button("Add Vendor", use_container_width=True):
                    if not vd_name.strip():
                        st.error("Vendor name is required.")
                    elif vd_cat_sel == "Other" and not vd_cat_custom.strip():
                        st.error("Please specify the category.")
                    else:
                        final_cat = vd_cat_custom.strip() if vd_cat_sel == "Other" else vd_cat_sel
                        final_dept = dept_opts[vd_dept]
                        add_vendor(ev["id"], vd_name.strip(), final_cat,
                                   vd_cn, vd_ce, vd_cv, dept_id=final_dept,
                                   notes=vd_notes)
                        st.success(f"✅ Vendor **{vd_name}** added and expense of "
                                   f"{sym}{vd_cv:,.0f} auto-recorded!")
                        st.rerun()

        if not vd_rows:
            empty_state("🚚", "No vendors added yet")
        else:
            total_v = sum(v["contract_value"] for v in vd_rows)
            df = pd.DataFrame([{
                "Vendor":    v["name"],
                "Category":  v["category"],
                "Contact":   v.get("contact_name") or "—",
                f"Contract ({sym})": f"{v['contract_value']:,.0f}",
                "Status":    v.get("status", "active"),
                "Notes":     v.get("notes") or "—",
            } for v in vd_rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"**Total Contract Value: {sym}{total_v:,.0f}**  ·  "
                    f"Auto-added to actual expenses ✅")
            with st.expander("🗑 Delete a vendor"):
                labels = [f"{v['name']} — {sym}{v['contract_value']:,.0f}" for v in vd_rows]
                sel = st.selectbox("Select", labels, key="del_vd_sel")
                if st.button("Delete", type="secondary", key="del_vd_btn"):
                    delete_vendor(vd_rows[labels.index(sel)]["id"])
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  COMPARISON TAB
# ══════════════════════════════════════════════════════════════════════════════
def _comparison(ev, depts, sym, s):
    st.subheader("📊 Comparison & Variance Analysis")

    c1, c2, c3 = st.columns(3)
    c1.metric("Est. Income",  f"{sym}{s['est_income']:,.0f}")
    c2.metric("Act. Income",  f"{sym}{s['act_income']:,.0f}",
              delta=f"{sym}{s['income_variance']:+,.0f}")
    c3.metric("Income Var",   f"{sym}{s['income_variance']:+,.0f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Est. Expenses", f"{sym}{s['est_expense']:,.0f}")
    c5.metric("Act. Expenses", f"{sym}{s['act_expense']:,.0f}",
              delta=f"{sym}{s['expense_variance']:+,.0f}", delta_color="inverse")
    c6.metric("Budget Accuracy", f"{s['budget_accuracy']:.1f}%")

    c7, c8, c9 = st.columns(3)
    c7.metric("Est. Profit",  f"{sym}{s['est_profit']:,.0f}")
    c8.metric("Act. Profit",  f"{sym}{s['act_profit']:,.0f}",
              delta=f"{sym}{s['act_profit']-s['est_profit']:+,.0f}")
    margin = (s["act_profit"] / max(s["act_income"], 1)) * 100
    c9.metric("Profit Margin", f"{margin:.1f}%")

    st.divider()
    col1, col2 = st.columns([3, 2])
    with col1:
        section_header("Budget vs Actual", "📊")
        fig = bar_comparison(
            ["Income", "Expenses", "Profit"],
            [s["est_income"], s["est_expense"], s["est_profit"]],
            [s["act_income"], s["act_expense"], s["act_profit"]]
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        section_header("Health Score", "🏥")
        profit_ratio = max(0, s["act_profit"] / max(s["act_income"], 1)) * 100
        health = min(100, s["budget_accuracy"] * 0.5 + profit_ratio * 0.5)
        fig_g  = health_gauge(health)
        st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})
        lbl = "🟢 Excellent" if health>=75 else ("🟡 Good" if health>=50 else "🔴 Needs Attention")
        st.markdown(f"**{lbl}** — {health:.1f}/100")

    # Department drill-down comparison
    st.divider()
    section_header("Department-level Variance", "🏢")
    ee_all = get_estimated_expenses(ev["id"])
    ae_all = get_actual_expenses(ev["id"])

    if depts and (ee_all or ae_all):
        dept_est, dept_act = {}, {}
        for r in ee_all:
            dn = r.get("dept_name") or "Unassigned"
            dept_est[dn] = dept_est.get(dn, 0) + r["amount"]
        for r in ae_all:
            dn = r.get("dept_name") or "Unassigned"
            dept_act[dn] = dept_act.get(dn, 0) + r["amount"]
        all_depts = sorted(set(list(dept_est) + list(dept_act)))

        fig_d = dept_bar(all_depts,
                         [dept_est.get(d, 0) for d in all_depts],
                         [dept_act.get(d, 0) for d in all_depts])
        fig_d.update_layout(height=max(250, len(all_depts) * 60))
        st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})

        rows = []
        for dn in all_depts:
            est = dept_est.get(dn, 0); act = dept_act.get(dn, 0)
            var = act - est; pct = (var / max(est, 1)) * 100
            rows.append({
                "Department": dn,
                f"Estimated ({sym})": f"{est:,.0f}",
                f"Actual ({sym})":    f"{act:,.0f}",
                f"Variance ({sym})":  f"{var:+,.0f}",
                "% Over/Under":       f"{pct:+.1f}%",
                "Status": "⚠️ Over" if var>0 else "✅ Under" if var<0 else "✔ On Track",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Line-item drill-down per department
        st.divider()
        section_header("Line-item Drill-down", "🔍")
        sel_dept_cmp = st.selectbox("View line items for department",
                                     [d["name"] for d in depts], key="cmp_dept_sel")
        did_cmp = _dept_id_map(depts)[sel_dept_cmp]
        est_items_cmp = get_estimated_expenses_by_dept(ev["id"], did_cmp)
        act_items_cmp = get_actual_expenses_by_dept(ev["id"], did_cmp)

        col_e, col_a = st.columns(2)
        with col_e:
            st.markdown(f"**📋 Estimated — {sel_dept_cmp}**")
            if est_items_cmp:
                df_e = pd.DataFrame([{
                    "Item":     r.get("item_name") or r.get("description") or "—",
                    "Category": r["category"],
                    "Qty":      f"{r.get('quantity') or 1:.0f} {r.get('unit') or ''}",
                    f"Amt ({sym})": f"{r['amount']:,.0f}",
                } for r in est_items_cmp])
                st.dataframe(df_e, use_container_width=True, hide_index=True)
                st.caption(f"Total: {sym}{sum(r['amount'] for r in est_items_cmp):,.0f}")
            else:
                st.info("No estimated items for this department.")

        with col_a:
            st.markdown(f"**💰 Actual — {sel_dept_cmp}**")
            if act_items_cmp:
                df_a = pd.DataFrame([{
                    "Item":     r.get("item_name") or r.get("description") or "—",
                    "Category": r["category"],
                    "Qty":      f"{r.get('quantity') or 1:.0f} {r.get('unit') or ''}",
                    f"Amt ({sym})": f"{r['amount']:,.0f}",
                    "Status":   r.get("status", "—"),
                } for r in act_items_cmp])
                st.dataframe(df_a, use_container_width=True, hide_index=True)
                st.caption(f"Total: {sym}{sum(r['amount'] for r in act_items_cmp):,.0f}")
            else:
                st.info("No actual expenses recorded for this department.")
    else:
        empty_state("📊", "Add departments & expenses to see comparison")


# ══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS TAB
# ══════════════════════════════════════════════════════════════════════════════
def _analytics(ev, depts, sym, s):
    st.subheader("📈 Analytics")
    ai_all = get_actual_income(ev["id"])
    ae_all = get_actual_expenses(ev["id"])
    sp_all = get_sponsors(ev["id"])
    ee_all = get_estimated_expenses(ev["id"])

    c1, c2 = st.columns(2)
    with c1:
        section_header("Revenue by Category", "💵")
        if ai_all:
            cats = {}
            for r in ai_all: cats[r["category"]] = cats.get(r["category"], 0) + r["amount"]
            fig = donut(list(cats.keys()), list(cats.values()))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            empty_state("💵", "No income data yet")

    with c2:
        section_header("Expenses by Department", "📤")
        if ae_all:
            dept_totals = {}
            for r in ae_all:
                dn = r.get("dept_name") or "Unassigned"
                dept_totals[dn] = dept_totals.get(dn, 0) + r["amount"]
            fig2 = donut(list(dept_totals.keys()), list(dept_totals.values()))
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            empty_state("📤", "No expense data yet")

    if sp_all:
        st.divider()
        section_header("Sponsor Breakdown", "🤝")
        fig_sp = sponsor_scatter([s["name"] for s in sp_all],
                                  [s["tier"] for s in sp_all],
                                  [s["amount"] for s in sp_all])
        fig_sp.update_layout(height=280)
        st.plotly_chart(fig_sp, use_container_width=True, config={"displayModeBar": False})

    if depts:
        st.divider()
        section_header("Dept Budget Utilization", "🏢")
        dept_est, dept_act = {}, {}
        for r in ee_all:
            dn = r.get("dept_name","—"); dept_est[dn] = dept_est.get(dn,0) + r["amount"]
        for r in ae_all:
            dn = r.get("dept_name","—"); dept_act[dn] = dept_act.get(dn,0) + r["amount"]
        for d in depts:
            dn  = d["name"]
            est = dept_est.get(dn, 0)
            act = dept_act.get(dn, 0)
            pct = min(act / max(est, 1), 1.0)
            var_txt = f"⚠️ Over by {sym}{act-est:,.0f}" if act > est else \
                      f"✅ Under by {sym}{est-act:,.0f}" if act < est else "✔ On Track"
            st.write(f"**{dn}** — {sym}{act:,.0f} / {sym}{est:,.0f}  |  {var_txt}")
            st.progress(pct)

    st.divider()
    section_header("Financial KPIs", "🎯")
    kpis = {
        "Total Revenue":         f"{sym}{s['act_income']:,.0f}",
        "Total Expenses":        f"{sym}{s['act_expense']:,.0f}",
        "Net Profit":            f"{sym}{s['act_profit']:,.0f}",
        "Profit Margin":         f"{(s['act_profit']/max(s['act_income'],1)*100):.1f}%",
        "Budget Accuracy":       f"{s['budget_accuracy']:.1f}%",
        "Income Variance":       f"{sym}{s['income_variance']:+,.0f}",
        "Expense Variance":      f"{sym}{s['expense_variance']:+,.0f}",
        "Sponsor Contributions": f"{sym}{s['sponsors_total']:,.0f}",
    }
    st.dataframe(pd.DataFrame(list(kpis.items()), columns=["KPI", "Value"]),
                 use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  REPORTS TAB
# ══════════════════════════════════════════════════════════════════════════════
def _reports(ev, depts, sym, s):
    st.subheader("📄 Reports")
    ai_all = get_actual_income(ev["id"])
    ae_all = get_actual_expenses(ev["id"])
    sp_all = get_sponsors(ev["id"])
    vd_all = get_vendors(ev["id"])
    ee_all = get_estimated_expenses(ev["id"])

    dept_map = {d["name"]: {"name": d["name"], "est": 0, "act": 0} for d in depts}
    for r in ee_all:
        dn = r.get("dept_name","—"); dept_map.setdefault(dn,{"name":dn,"est":0,"act":0})["est"]+=r["amount"]
    for r in ae_all:
        dn = r.get("dept_name","—"); dept_map.setdefault(dn,{"name":dn,"est":0,"act":0})["act"]+=r["amount"]
    dept_rows = list(dept_map.values())

    from utils.export_engine import generate_pdf, generate_excel
    c1, c2 = st.columns(2)
    with c1:
        pdf_b = generate_pdf(ev, s, ai_all, ae_all, sp_all, vd_all)
        st.download_button("📄 Download PDF", data=pdf_b,
            file_name=f"{ev['name'].replace(' ','_')}_Report_{datetime.date.today()}.pdf",
            mime="application/pdf", use_container_width=True)
    with c2:
        xl_b = generate_excel(ev, s, ai_all, ae_all, sp_all, vd_all, dept_rows)
        st.download_button("📊 Download Excel", data=xl_b,
            file_name=f"{ev['name'].replace(' ','_')}_Report_{datetime.date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)

    st.divider()
    st.markdown(f"### {ev['name']} — Summary")
    st.caption(f"📍 {ev.get('venue','—')}  ·  {ev.get('start_date','—')} → {ev.get('end_date','—')}")
    r1,r2,r3 = st.columns(3)
    r1.metric("Revenue",  f"{sym}{s['act_income']:,.0f}")
    r2.metric("Expenses", f"{sym}{s['act_expense']:,.0f}")
    r3.metric("Profit",   f"{sym}{s['act_profit']:,.0f}")
    st.divider()
    pl = pd.DataFrame([
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
    st.dataframe(pl, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def show(event_id):
    ev = get_event(event_id)
    if not ev:
        st.error("Event not found.")
        return

    depts = get_departments(event_id)
    sym   = _sym(ev)
    s     = get_event_summary(event_id)

    if st.button("← Back to Events", key="back_btn"):
        st.session_state.page = "events"
        st.session_state.active_event = None
        st.rerun()

    ph = ev.get("phase", "planning")
    st.title(f"🗂️ {ev['name']}")
    st.caption(
        f"📍 {ev.get('venue','—')}  ·  "
        f"📆 {ev.get('start_date','—')} → {ev.get('end_date','—')}  ·  "
        f"👥 {ev.get('expected_attendees',0):,} attendees  ·  "
        f"Phase: **{ph.title()}**  ·  "
        f"💱 {ev.get('currency','USD')}"
    )
    st.divider()

    tabs = st.tabs(["📋 Planning", "💰 Execution", "📊 Comparison", "📈 Analytics", "📄 Reports"])
    with tabs[0]: _planning(ev, depts, sym)
    with tabs[1]: _execution(ev, depts, sym)
    with tabs[2]: _comparison(ev, depts, sym, s)
    with tabs[3]: _analytics(ev, depts, sym, s)
    with tabs[4]: _reports(ev, depts, sym, s)
