"""
EventLedger AI – Role Engine
Handles multi-role assignment, permission checks, approval routing.
"""

from database.schema import get_connection

# ── Role definitions ────────────────────────────────────────────────────────

ROLES = {
    "super_admin":  "Super Admin",
    "event_admin":  "Event Admin",
    "finance_head": "Finance Head",
    "dept_head":    "Department Head",
    "member":       "Member",
}

ROLE_COLORS = {
    "super_admin":  "#6366f1",
    "event_admin":  "#f59e0b",
    "finance_head": "#10b981",
    "dept_head":    "#ef4444",
    "member":       "#7b7b9a",
}

ROLE_ICONS = {
    "super_admin":  "👑",
    "event_admin":  "🎯",
    "finance_head": "💰",
    "dept_head":    "🏢",
    "member":       "👤",
}

# Permission sets per role
PERMISSIONS = {
    "super_admin": {
        "create_event", "delete_event", "lock_event", "archive_event",
        "create_user", "reset_password", "assign_roles",
        "view_all_events", "view_all_budgets", "view_all_expenses",
        "approve_budget", "reject_budget", "override_approval",
        "create_dept", "view_reports", "view_analytics",
        "manage_settings", "view_audit_log",
        "add_income", "add_expense", "add_sponsor", "add_vendor",
    },
    "event_admin": {
        "create_dept", "assign_dept_head",
        "set_event_budget", "view_all_depts",
        "view_reports", "view_analytics",
        "approve_budget",   # only if NOT the submitter
        "view_expenses", "view_income",
        "add_sponsor", "add_vendor",
    },
    "finance_head": {
        "review_budget", "approve_budget", "reject_budget",
        "release_funds", "verify_bills",
        "approve_reimbursement", "pay_vendor",
        "view_all_budgets", "view_all_expenses",
        "view_reports", "view_analytics",
        "add_income",
    },
    "dept_head": {
        "create_budget", "edit_budget_draft", "submit_budget",
        "upload_quotation", "add_expense", "upload_bill",
        "view_own_dept",
    },
    "member": {
        "view_own_dept",
    },
}


# ── Role queries ────────────────────────────────────────────────────────────

def get_user_roles(user_id: int, event_id: int = None) -> list:
    """Return all roles for a user (optionally scoped to an event)."""
    conn = get_connection()
    if event_id:
        rows = conn.execute(
            """SELECT role, dept_id, event_id FROM user_event_roles
               WHERE user_id=? AND (event_id=? OR event_id IS NULL)""",
            (user_id, event_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT role, dept_id, event_id FROM user_event_roles WHERE user_id=?",
            (user_id,)
        ).fetchall()
    conn.close()

    # Also include base role from users table
    conn2 = get_connection()
    user  = conn2.execute("SELECT role, is_super_admin FROM users WHERE id=?", (user_id,)).fetchone()
    conn2.close()

    result = [dict(r) for r in rows]
    if user:
        if user["is_super_admin"]:
            result.append({"role": "super_admin", "dept_id": None, "event_id": None})
        elif user["role"] not in [r["role"] for r in result]:
            result.append({"role": user["role"], "dept_id": None, "event_id": None})
    return result


def get_primary_role(user_id: int, event_id: int = None) -> str:
    """Return the highest-priority role for display purposes."""
    priority = ["super_admin", "event_admin", "finance_head", "dept_head", "member"]
    roles    = [r["role"] for r in get_user_roles(user_id, event_id)]
    for p in priority:
        if p in roles:
            return p
    return "member"


def has_permission(user_id: int, permission: str, event_id: int = None) -> bool:
    """Check if user has a specific permission."""
    roles = [r["role"] for r in get_user_roles(user_id, event_id)]
    for role in roles:
        if permission in PERMISSIONS.get(role, set()):
            return True
    return False


def is_super_admin(user_id: int) -> bool:
    conn = get_connection()
    row  = conn.execute("SELECT is_super_admin FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return bool(row and row["is_super_admin"])


def get_user_dept_ids(user_id: int, event_id: int) -> list:
    """Return dept_ids the user is head of for this event."""
    conn  = get_connection()
    rows  = conn.execute(
        """SELECT dept_id FROM user_event_roles
           WHERE user_id=? AND event_id=? AND role='dept_head' AND dept_id IS NOT NULL""",
        (user_id, event_id)
    ).fetchall()
    conn.close()
    return [r["dept_id"] for r in rows]


def get_accessible_events(user_id: int) -> list:
    """Events a user can see based on their roles."""
    conn = get_connection()
    # Super admin sees all
    user = conn.execute("SELECT is_super_admin FROM users WHERE id=?", (user_id,)).fetchone()
    if user and user["is_super_admin"]:
        rows = conn.execute("SELECT * FROM events ORDER BY created_at DESC").fetchall()
    else:
        rows = conn.execute(
            """SELECT DISTINCT e.* FROM events e
               LEFT JOIN user_event_roles r ON e.id = r.event_id AND r.user_id=?
               WHERE e.user_id=? OR r.user_id=?
               ORDER BY e.created_at DESC""",
            (user_id, user_id, user_id)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── User management ─────────────────────────────────────────────────────────

def get_all_users():
    conn  = get_connection()
    rows  = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_org_users():
    """All non-super-admin users for role assignment."""
    conn  = get_connection()
    rows  = conn.execute(
        "SELECT * FROM users WHERE is_active=1 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def assign_role(user_id: int, event_id: int, role: str,
                dept_id: int = None, assigned_by: int = None):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO user_event_roles
               (user_id, event_id, role, dept_id, assigned_by) VALUES (?,?,?,?,?)""",
            (user_id, event_id, role, dept_id, assigned_by)
        )
        conn.commit()
        return True
    except Exception as e:
        return False
    finally:
        conn.close()


def revoke_role(user_id: int, event_id: int, role: str, dept_id: int = None):
    conn = get_connection()
    if dept_id:
        conn.execute(
            """DELETE FROM user_event_roles
               WHERE user_id=? AND event_id=? AND role=? AND dept_id=?""",
            (user_id, event_id, role, dept_id)
        )
    else:
        conn.execute(
            "DELETE FROM user_event_roles WHERE user_id=? AND event_id=? AND role=?",
            (user_id, event_id, role)
        )
    conn.commit()
    conn.close()


def get_event_role_assignments(event_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.*, u.name as user_name, u.email,
                  d.name as dept_name
           FROM user_event_roles r
           JOIN users u ON r.user_id = u.id
           LEFT JOIN departments d ON r.dept_id = d.id
           WHERE r.event_id=?
           ORDER BY r.role, u.name""",
        (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_user(name, email, password, org_name, base_role="member"):
    import hashlib
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO users (name, email, password, role, org_name)
               VALUES (?,?,?,?,?)""",
            (name, email, hashlib.sha256(password.encode()).hexdigest(),
             base_role, org_name)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else None
    except Exception:
        return None
    finally:
        conn.close()


def reset_password(user_id: int, new_password: str):
    import hashlib
    conn = get_connection()
    conn.execute("UPDATE users SET password=? WHERE id=?",
                 (hashlib.sha256(new_password.encode()).hexdigest(), user_id))
    conn.commit()
    conn.close()


# ── Approval engine ─────────────────────────────────────────────────────────

def get_approval_chain(proposal_id: int) -> list:
    """
    Dynamic approval chain:
    - If submitter == event_admin → skip to finance_head
    - If finance_head == submitter → goes to super_admin
    - Otherwise: dept_head → finance_head → (optional super_admin)
    """
    conn = get_connection()
    prop = conn.execute(
        "SELECT * FROM budget_proposals WHERE id=?", (proposal_id,)
    ).fetchone()
    conn.close()
    if not prop:
        return []

    submitter_id = prop["submitted_by"]
    event_id     = prop["event_id"]

    # Get event admin IDs
    conn2 = get_connection()
    event_admins = [r["user_id"] for r in conn2.execute(
        "SELECT user_id FROM user_event_roles WHERE event_id=? AND role='event_admin'",
        (event_id,)
    ).fetchall()]
    finance_heads = [r["user_id"] for r in conn2.execute(
        "SELECT user_id FROM user_event_roles WHERE event_id=? AND role='finance_head'",
        (event_id,)
    ).fetchall()]
    super_admins = [r["id"] for r in conn2.execute(
        "SELECT id FROM users WHERE is_super_admin=1"
    ).fetchall()]
    conn2.close()

    chain = []

    # Step 1: Finance Head (skip if submitter is finance head)
    valid_fh = [fh for fh in finance_heads if fh != submitter_id]
    if valid_fh:
        chain.append({"step": "finance_head", "approver_ids": valid_fh, "label": "Finance Head"})
    else:
        # Finance head is the submitter → escalate to super admin
        chain.append({"step": "super_admin", "approver_ids": super_admins, "label": "Super Admin"})

    return chain


def can_approve(user_id: int, proposal_id: int) -> bool:
    """Check if user can approve this proposal (not their own)."""
    conn  = get_connection()
    prop  = conn.execute("SELECT * FROM budget_proposals WHERE id=?", (proposal_id,)).fetchone()
    conn.close()
    if not prop:
        return False
    if prop["submitted_by"] == user_id:
        return False   # Cannot approve own submission
    return has_permission(user_id, "approve_budget", prop["event_id"])


# ── Notifications ────────────────────────────────────────────────────────────

def create_notification(user_id: int, title: str, message: str,
                         event_id: int = None, notif_type: str = "info",
                         link_page: str = None):
    conn = get_connection()
    conn.execute(
        """INSERT INTO notifications
           (user_id, event_id, title, message, type, link_page)
           VALUES (?,?,?,?,?,?)""",
        (user_id, event_id, title, message, notif_type, link_page)
    )
    conn.commit()
    conn.close()


def get_notifications(user_id: int, unread_only: bool = False) -> list:
    conn  = get_connection()
    query = "SELECT * FROM notifications WHERE user_id=?"
    if unread_only:
        query += " AND is_read=0"
    query += " ORDER BY created_at DESC LIMIT 50"
    rows  = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_notifications_read(user_id: int):
    conn = get_connection()
    conn.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def unread_count(user_id: int) -> int:
    conn = get_connection()
    n    = conn.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user_id,)
    ).fetchone()[0]
    conn.close()
    return n


# ── Audit log ────────────────────────────────────────────────────────────────

def log_action(user_id: int, action: str, entity_type: str = None,
               entity_id: int = None, event_id: int = None, details: str = None):
    conn = get_connection()
    conn.execute(
        """INSERT INTO audit_log
           (user_id, event_id, action, entity_type, entity_id, details)
           VALUES (?,?,?,?,?,?)""",
        (user_id, event_id, action, entity_type, entity_id, details)
    )
    conn.commit()
    conn.close()


def get_audit_log(event_id: int = None, limit: int = 100) -> list:
    conn  = get_connection()
    if event_id:
        rows = conn.execute(
            """SELECT a.*, u.name as user_name FROM audit_log a
               LEFT JOIN users u ON a.user_id = u.id
               WHERE a.event_id=? ORDER BY a.created_at DESC LIMIT ?""",
            (event_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT a.*, u.name as user_name FROM audit_log a
               LEFT JOIN users u ON a.user_id = u.id
               ORDER BY a.created_at DESC LIMIT ?""",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
