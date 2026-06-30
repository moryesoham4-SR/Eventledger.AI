"""
EventLedger AI – Budget Proposal Workflow
Handles create/submit/approve/reject cycle with conflict detection.
"""

import datetime
from database.schema import get_connection
from utils.roles import (
    can_approve, create_notification, log_action,
    get_user_roles, get_event_role_assignments
)


def get_proposals(event_id: int, dept_id: int = None, status: str = None) -> list:
    conn  = get_connection()
    q     = """SELECT bp.*, d.name as dept_name, d.color as dept_color,
                      u.name as submitter_name
               FROM budget_proposals bp
               JOIN departments d ON bp.department_id = d.id
               JOIN users u ON bp.submitted_by = u.id
               WHERE bp.event_id=?"""
    args  = [event_id]
    if dept_id:
        q   += " AND bp.department_id=?"; args.append(dept_id)
    if status:
        q   += " AND bp.status=?";        args.append(status)
    q    += " ORDER BY bp.created_at DESC"
    rows  = conn.execute(q, args).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_proposal(proposal_id: int) -> dict:
    conn = get_connection()
    row  = conn.execute(
        """SELECT bp.*, d.name as dept_name, u.name as submitter_name
           FROM budget_proposals bp
           JOIN departments d ON bp.department_id = d.id
           JOIN users u ON bp.submitted_by = u.id
           WHERE bp.id=?""", (proposal_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_line_items(proposal_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM budget_line_items WHERE proposal_id=? ORDER BY created_at",
        (proposal_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_proposal(event_id: int, dept_id: int, submitted_by: int, title: str, notes: str = "") -> int:
    conn = get_connection()
    c    = conn.execute(
        """INSERT INTO budget_proposals
           (event_id, department_id, submitted_by, title, status, notes)
           VALUES (?,?,?,?,?,?)""",
        (event_id, dept_id, submitted_by, title, "draft", notes)
    )
    pid = c.lastrowid
    conn.commit()
    conn.close()
    log_action(submitted_by, "CREATE_PROPOSAL", "budget_proposals", pid,
               event_id, f"Created budget proposal: {title}")
    return pid


def add_line_item(proposal_id: int, category: str, item_name: str,
                   description: str, quantity: float, unit: str,
                   unit_price: float) -> int:
    total = quantity * unit_price
    conn  = get_connection()
    c     = conn.execute(
        """INSERT INTO budget_line_items
           (proposal_id, category, item_name, description, quantity, unit, unit_price, total_amount)
           VALUES (?,?,?,?,?,?,?,?)""",
        (proposal_id, category, item_name, description, quantity, unit, unit_price, total)
    )
    lid = c.lastrowid
    # Recalculate proposal total
    conn.execute(
        """UPDATE budget_proposals SET total_amount =
           (SELECT COALESCE(SUM(total_amount),0) FROM budget_line_items WHERE proposal_id=?)
           WHERE id=?""", (proposal_id, proposal_id)
    )
    conn.commit()
    conn.close()
    return lid


def delete_line_item(item_id: int, proposal_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM budget_line_items WHERE id=?", (item_id,))
    conn.execute(
        """UPDATE budget_proposals SET total_amount =
           (SELECT COALESCE(SUM(total_amount),0) FROM budget_line_items WHERE proposal_id=?)
           WHERE id=?""", (proposal_id, proposal_id)
    )
    conn.commit()
    conn.close()


def submit_proposal(proposal_id: int, submitted_by: int) -> dict:
    """Submit for approval. Returns {ok, message}."""
    conn = get_connection()
    prop = conn.execute("SELECT * FROM budget_proposals WHERE id=?", (proposal_id,)).fetchone()
    if not prop:
        conn.close(); return {"ok": False, "message": "Proposal not found."}
    if prop["status"] not in ("draft", "rejected"):
        conn.close(); return {"ok": False, "message": f"Cannot submit a proposal with status '{prop['status']}'."}

    items = conn.execute("SELECT COUNT(*) FROM budget_line_items WHERE proposal_id=?",
                         (proposal_id,)).fetchone()[0]
    if items == 0:
        conn.close(); return {"ok": False, "message": "Add at least one line item before submitting."}

    # Increment version if resubmitting
    new_version = (prop["version"] or 1) + (1 if prop["status"] == "rejected" else 0)
    conn.execute(
        """UPDATE budget_proposals
           SET status='submitted', submitted_at=?, version=?, rejected_at=NULL,
               rejected_by=NULL, reject_reason=NULL
           WHERE id=?""",
        (str(datetime.datetime.now()), new_version, proposal_id)
    )
    conn.commit()

    # Notify finance heads
    finance_heads = conn.execute(
        """SELECT user_id FROM user_event_roles
           WHERE event_id=? AND role='finance_head'""",
        (prop["event_id"],)
    ).fetchall()
    dept = conn.execute("SELECT name FROM departments WHERE id=?",
                        (prop["department_id"],)).fetchone()
    dept_name = dept["name"] if dept else "Department"
    conn.close()

    for fh in finance_heads:
        create_notification(
            fh["user_id"], "📋 New Budget for Review",
            f"{dept_name} submitted a budget of ₹{prop['total_amount']:,.0f} for your approval.",
            prop["event_id"], "info"
        )
    log_action(submitted_by, "SUBMIT_PROPOSAL", "budget_proposals", proposal_id,
               prop["event_id"], f"Submitted budget ₹{prop['total_amount']:,.0f}")

    # Email finance heads
    try:
        from utils.email_engine import send_budget_submitted_email
        conn2 = get_connection()
        for fh in finance_heads:
            u = conn2.execute("SELECT name, email FROM users WHERE id=?",
                              (fh["user_id"],)).fetchone()
            if u and u.get("email"):
                send_budget_submitted_email(u["email"], u["name"], dept_name, prop["total_amount"])
        conn2.close()
    except Exception as e:
        print(f"[budget_workflow] submit email failed: {e}")

    return {"ok": True, "message": "Budget submitted for approval."}


def approve_proposal(proposal_id: int, approved_by: int) -> dict:
    """Approve a proposal."""
    if not can_approve(approved_by, proposal_id):
        return {"ok": False, "message": "You cannot approve your own budget or lack permission."}

    conn = get_connection()
    prop = conn.execute("SELECT * FROM budget_proposals WHERE id=?", (proposal_id,)).fetchone()
    if not prop or prop["status"] != "submitted":
        conn.close(); return {"ok": False, "message": "Proposal is not in submitted state."}

    conn.execute(
        """UPDATE budget_proposals
           SET status='approved', approved_by=?, approved_at=?
           WHERE id=?""",
        (approved_by, str(datetime.datetime.now()), proposal_id)
    )

    # Copy line items → estimated_expenses
    items = conn.execute(
        "SELECT * FROM budget_line_items WHERE proposal_id=?", (proposal_id,)
    ).fetchall()
    # Clear previous estimates for this dept from this proposal
    conn.execute("DELETE FROM estimated_expenses WHERE proposal_id=?", (proposal_id,))
    for item in items:
        conn.execute(
            """INSERT INTO estimated_expenses
               (event_id, department_id, proposal_id, category, item_name,
                description, quantity, unit, amount)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (prop["event_id"], prop["department_id"], proposal_id,
             item["category"], item["item_name"], item["description"],
             item["quantity"], item["unit"], item["total_amount"])
        )
    conn.commit()

    # Notify submitter
    submitter_name = conn.execute("SELECT name FROM users WHERE id=?",
                                   (prop["submitted_by"],)).fetchone()
    dept = conn.execute("SELECT name FROM departments WHERE id=?",
                        (prop["department_id"],)).fetchone()
    conn.close()

    create_notification(
        prop["submitted_by"], "✅ Budget Approved!",
        f"Your budget for {dept['name'] if dept else 'your department'} "
        f"(₹{prop['total_amount']:,.0f}) has been approved.",
        prop["event_id"], "success"
    )
    log_action(approved_by, "APPROVE_PROPOSAL", "budget_proposals", proposal_id,
               prop["event_id"], f"Approved budget ₹{prop['total_amount']:,.0f}")

    # Email the submitter
    try:
        from utils.email_engine import send_budget_approved_email
        conn3 = get_connection()
        u = conn3.execute("SELECT name, email FROM users WHERE id=?",
                          (prop["submitted_by"],)).fetchone()
        conn3.close()
        if u and u.get("email"):
            send_budget_approved_email(
                u["email"], u["name"],
                dept["name"] if dept else "your department",
                prop["total_amount"]
            )
    except Exception as e:
        print(f"[budget_workflow] approve email failed: {e}")

    return {"ok": True, "message": "Budget approved and funds released to department."}


def reject_proposal(proposal_id: int, rejected_by: int, reason: str) -> dict:
    """Reject with reason — allows dept head to resubmit."""
    if not can_approve(rejected_by, proposal_id):
        return {"ok": False, "message": "You cannot reject your own budget or lack permission."}

    conn = get_connection()
    prop = conn.execute("SELECT * FROM budget_proposals WHERE id=?", (proposal_id,)).fetchone()
    if not prop or prop["status"] != "submitted":
        conn.close(); return {"ok": False, "message": "Proposal is not in submitted state."}

    conn.execute(
        """UPDATE budget_proposals
           SET status='rejected', rejected_by=?, rejected_at=?, reject_reason=?
           WHERE id=?""",
        (rejected_by, str(datetime.datetime.now()), reason, proposal_id)
    )
    conn.commit()
    dept = conn.execute("SELECT name FROM departments WHERE id=?",
                        (prop["department_id"],)).fetchone()
    conn.close()

    create_notification(
        prop["submitted_by"], "❌ Budget Rejected",
        f"Your budget for {dept['name'] if dept else 'your department'} was rejected. "
        f"Reason: {reason}",
        prop["event_id"], "error"
    )
    log_action(rejected_by, "REJECT_PROPOSAL", "budget_proposals", proposal_id,
               prop["event_id"], f"Rejected: {reason}")

    # Email the submitter
    try:
        from utils.email_engine import send_budget_rejected_email
        conn4 = get_connection()
        u = conn4.execute("SELECT name, email FROM users WHERE id=?",
                          (prop["submitted_by"],)).fetchone()
        conn4.close()
        if u and u.get("email"):
            send_budget_rejected_email(
                u["email"], u["name"],
                dept["name"] if dept else "your department",
                prop["total_amount"], reason
            )
    except Exception as e:
        print(f"[budget_workflow] reject email failed: {e}")

    return {"ok": True, "message": "Budget rejected. Department head can revise and resubmit."}


def get_pending_proposals(user_id: int, event_id: int = None) -> list:
    """Get proposals waiting for THIS user's approval."""
    from utils.roles import has_permission, get_accessible_events
    conn = get_connection()

    if event_id:
        rows = conn.execute(
            """SELECT bp.*, d.name as dept_name, u.name as submitter_name
               FROM budget_proposals bp
               JOIN departments d ON bp.department_id = d.id
               JOIN users u ON bp.submitted_by = u.id
               WHERE bp.event_id=? AND bp.status='submitted'
               AND bp.submitted_by != ?
               ORDER BY bp.submitted_at""",
            (event_id, user_id)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT bp.*, d.name as dept_name, u.name as submitter_name,
                      e.name as event_name
               FROM budget_proposals bp
               JOIN departments d  ON bp.department_id = d.id
               JOIN users u        ON bp.submitted_by  = u.id
               JOIN events e       ON bp.event_id      = e.id
               WHERE bp.status='submitted'
               AND bp.submitted_by != ?
               ORDER BY bp.submitted_at""",
            (user_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]