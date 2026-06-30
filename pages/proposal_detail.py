"""EventLedger AI – Budget Proposal Create & Detail page"""

import streamlit as st
import pandas as pd
from utils.budget_workflow import (
    create_proposal, get_proposal, get_line_items,
    add_line_item, delete_line_item, submit_proposal
)
from utils.roles import (
    get_user_dept_ids, has_permission, log_action, can_approve
)
from utils.helpers import get_departments
from utils.currency import get_symbol
from components.ui import section_header, empty_state

EXPENSE_CATS = ["Marketing","Venue","Technology","Catering","Security",
                "Logistics","Transport","Entertainment","Staffing",
                "Printing","Decoration","Equipment","Miscellaneous"]
UNITS = ["unit","pcs","kg","litre","hour","day","set","lot","trip","person","sq.ft","other"]


def show_create(user):
    """Create a new budget proposal."""
    ev_id   = st.session_state.get("proposal_event_id")
    dept_id = st.session_state.get("proposal_dept_id")
    if not ev_id or not dept_id:
        st.error("Missing event or department context.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"; st.rerun()
        return

    sym  = get_symbol()
    conn = __import__("database.schema", fromlist=["get_connection"]).get_connection()
    dept = conn.execute("SELECT * FROM departments WHERE id=?", (dept_id,)).fetchone()
    ev   = conn.execute("SELECT * FROM events WHERE id=?", (ev_id,)).fetchone()
    conn.close()

    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"; st.rerun()

    st.title(f"📋 New Budget Proposal")
    st.caption(f"🏢 {dept['name']}  ·  📅 {ev['name']}")
    st.divider()

    with st.form("create_proposal_form", clear_on_submit=True):
        title = st.text_input("Proposal Title *",
                               placeholder=f"e.g. {dept['name']} Budget — March 2027")
        notes = st.text_area("Notes / Justification",
                              placeholder="Brief description of why this budget is needed…")
        if st.form_submit_button("📝 Create Draft", use_container_width=True):
            if title.strip():
                pid = create_proposal(ev_id, dept_id, user["id"], title.strip(), notes)
                st.session_state.active_proposal = pid
                st.session_state.page = "proposal_detail"
                st.rerun()
            else:
                st.error("Title is required.")


def show_detail(user):
    """View / edit / submit a proposal."""
    if st.session_state.get("_celebrate"):
        from components.ui import celebrate_success, celebrate_launch, celebrate_sent, shake_warning
        c = st.session_state.pop("_celebrate")
        _kind = c.get("kind", "confetti")
        _fn = {"confetti": celebrate_success, "launch": celebrate_launch,
               "sent": celebrate_sent, "shake": shake_warning}.get(_kind, celebrate_success)
        _fn(c["title"], c.get("subtitle", ""))

    pid = st.session_state.get("active_proposal")
    if not pid:
        st.error("No proposal selected.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"; st.rerun()
        return

    prop  = get_proposal(pid)
    if not prop:
        st.error("Proposal not found.")
        return

    sym    = get_symbol()
    items  = get_line_items(pid)
    is_owner = prop["submitted_by"] == user["id"]
    can_edit = prop["status"] in ("draft","rejected") and is_owner
    can_app  = can_approve(user["id"], pid)

    if st.button("← Back"):
        st.session_state.page = "dashboard"; st.rerun()

    st.title(f"📋 {prop['title']}")
    status_icons = {"draft":"📝","submitted":"⏳","approved":"✅","rejected":"❌"}
    st.caption(
        f"🏢 {prop['dept_name']}  ·  "
        f"Status: {status_icons.get(prop['status'],'')} **{prop['status'].title()}**  ·  "
        f"v{prop.get('version',1)}  ·  by {prop['submitter_name']}"
    )

    if prop.get("reject_reason"):
        st.error(f"❌ **Rejection reason:** {prop['reject_reason']}")
        st.info("✏️ You can edit the line items and resubmit.")

    if prop["status"] == "approved":
        st.success(f"✅ This budget has been **approved**. Funds of {sym}{prop['total_amount']:,.0f} released.")

    st.divider()

    # ── KPIs ────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Line Items",   str(len(items)))
    c2.metric("Total Budget", f"{sym}{prop['total_amount']:,.0f}")
    c3.metric("Version",      f"v{prop.get('version',1)}")
    st.divider()

    # ── Add Line Item ────────────────────────────────────────────────────────
    if can_edit:
        section_header("Add Line Item", "➕")
        with st.expander("➕ Add Item", expanded=not bool(items)):
            with st.form("add_item_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                item_name = c1.text_input("Item Name *", placeholder="e.g. Banner Printing")
                category  = c2.selectbox("Category", EXPENSE_CATS)
                c3, c4, c5 = st.columns(3)
                qty        = c3.number_input("Quantity", min_value=0.0, value=1.0, step=1.0)
                unit       = c4.selectbox("Unit", UNITS)
                unit_price = c5.number_input(f"Unit Price ({sym})", min_value=0.0, step=100.0)
                desc  = st.text_input("Specification / Description",
                                       placeholder="e.g. 10x4 ft vinyl banner, full colour")
                notes = st.text_input("Internal Notes (optional)")
                total = qty * unit_price
                if total > 0:
                    st.info(f"Line Total: **{sym}{total:,.0f}**  ({qty:.0f} × {sym}{unit_price:,.0f})")
                if st.form_submit_button("Add Item", use_container_width=True):
                    if item_name.strip() and unit_price > 0:
                        add_line_item(pid, category, item_name.strip(),
                                      desc, qty, unit, unit_price)
                        st.rerun()
                    else:
                        st.error("Item name and unit price are required.")

    # ── Line Items Table ─────────────────────────────────────────────────────
    section_header("Line Items", "📋")
    if not items:
        empty_state("📋", "No items yet", "Add line items using the form above.")
    else:
        # Group by category
        cats = sorted(set(i["category"] for i in items))
        for cat in cats:
            cat_items = [i for i in items if i["category"] == cat]
            cat_total = sum(i["total_amount"] for i in cat_items)
            st.markdown(f"**{cat}** — {sym}{cat_total:,.0f}")
            df = pd.DataFrame([{
                "Item":         i["item_name"],
                "Qty":          f"{i['quantity']:.0f} {i['unit']}",
                f"Unit ({sym})": f"{i['unit_price']:,.0f}",
                f"Total ({sym})": f"{i['total_amount']:,.0f}",
                "Spec":         i.get("description") or "—",
            } for i in cat_items])
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.metric(f"Grand Total", f"{sym}{prop['total_amount']:,.0f}")

        if can_edit:
            with st.expander("🗑 Delete a line item"):
                labels = [f"{i['item_name']} — {sym}{i['total_amount']:,.0f}"
                          for i in items]
                sel = st.selectbox("Select item", labels, key="del_item_sel")
                if st.button("Delete Item", type="secondary", key="del_item_btn"):
                    idx = labels.index(sel)
                    delete_line_item(items[idx]["id"], pid)
                    st.rerun()

    st.divider()

    # ── Actions ──────────────────────────────────────────────────────────────
    if can_edit and items:
        section_header("Submit for Approval", "📤")
        st.info("Once submitted, the Finance Head will review your budget. "
                "If rejected, you can revise and resubmit.")
        if st.button("📤 Submit Budget for Approval", use_container_width=True):
            res = submit_proposal(pid, user["id"])
            if res["ok"]:
                st.session_state["_celebrate"] = {
                    "kind": "sent",
                    "title": "Budget sent 📤",
                    "subtitle": f"{prop['title']} is on its way for review"
                }
                st.rerun()
            else:
                st.error(res["message"])

    # ── Approver actions ─────────────────────────────────────────────────────
    if can_app and prop["status"] == "submitted":
        st.divider()
        section_header("Approval Decision", "⚖️")
        col1, col2 = st.columns(2)
        if col1.button("✅ Approve Budget", use_container_width=True):
            res = approve_proposal(pid, user["id"])
            if res["ok"]:
                st.session_state["_celebrate"] = {
                    "title": "Budget approved 🎉",
                    "subtitle": f"{prop['title']} — {sym}{prop['total_amount']:,.0f} is ready to use"
                }
            else:
                st.error(res["message"])
            st.rerun()
        if col2.button("❌ Reject Budget", use_container_width=True, type="secondary"):
            st.session_state["reject_open"] = True

        if st.session_state.get("reject_open"):
            reason = st.text_area("Rejection Reason *",
                                   placeholder="e.g. Reduce printing cost by 20%")
            ra, rb = st.columns(2)
            if ra.button("Send Rejection", use_container_width=True):
                if reason.strip():
                    from utils.budget_workflow import reject_proposal
                    res = reject_proposal(pid, user["id"], reason.strip())
                    st.session_state.pop("reject_open", None)
                    st.session_state["_celebrate"] = {
                        "kind": "shake",
                        "title": "Budget rejected",
                        "subtitle": f"{prop['title']} sent back for revision"
                    }
                    st.rerun()
                else:
                    st.error("Reason is required.")
            if rb.button("Cancel", use_container_width=True, type="secondary"):
                st.session_state.pop("reject_open", None)
                st.rerun()