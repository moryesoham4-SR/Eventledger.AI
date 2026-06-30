"""EventLedger AI – Database helpers (complete, fixed)"""

import hashlib
import streamlit as st
from database.schema import get_connection


# ── Auth ────────────────────────────────────────────────────────────────────

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def authenticate(email: str, password: str):
    conn = get_connection()
    row  = conn.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, hash_password(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def register_user(name, email, password, org, role="admin"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (name, email, password, role, org_name) VALUES (?,?,?,?,?)",
            (name, email, hash_password(password), role, org)
        )
        conn.commit()
        # Return the newly created user so caller can log them in directly
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return dict(row) if row else True
    except Exception:
        return False
    finally:
        conn.close()


# ── Events ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_events(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM events WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@st.cache_data(ttl=30)
def get_event(event_id):
    conn = get_connection()
    row  = conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_event(user_id, name, description, venue, start_date, end_date, attendees, currency):
    conn = get_connection()
    c    = conn.execute(
        """INSERT INTO events
           (user_id, name, description, venue, start_date, end_date,
            expected_attendees, currency, status, phase)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (user_id, name, description, venue, start_date, end_date,
         attendees, currency, "active", "planning")
    )
    eid = c.lastrowid
    conn.commit()
    conn.close()
    return eid


def update_event_phase(event_id, phase):
    conn = get_connection()
    conn.execute("UPDATE events SET phase=? WHERE id=?", (phase, event_id))
    conn.commit()
    conn.close()


def update_event_status(event_id, status):
    conn = get_connection()
    conn.execute("UPDATE events SET status=? WHERE id=?", (status, event_id))
    conn.commit()
    conn.close()


def delete_event(event_id):
    conn = get_connection()
    # Delete all child records first
    for tbl in ["estimated_income","estimated_expenses","actual_income",
                "actual_expenses","sponsors","vendors","departments"]:
        conn.execute(f"DELETE FROM {tbl} WHERE event_id=?", (event_id,))
    conn.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()


# ── Departments ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_departments(event_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM departments WHERE event_id=? ORDER BY name", (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_department(event_id, name, head, manager, color):
    conn = get_connection()
    conn.execute(
        "INSERT INTO departments (event_id, name, head_name, manager, color) VALUES (?,?,?,?,?)",
        (event_id, name, head, manager, color)
    )
    conn.commit()
    conn.close()


def delete_department(dept_id):
    conn = get_connection()
    conn.execute("DELETE FROM departments WHERE id=?", (dept_id,))
    conn.commit()
    conn.close()


# ── Estimated Income ─────────────────────────────────────────────────────────

def get_estimated_income(event_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM estimated_income WHERE event_id=? ORDER BY created_at", (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_estimated_income(event_id, source, category, amount, notes=""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO estimated_income (event_id, source, category, amount, notes) VALUES (?,?,?,?,?)",
        (event_id, source, category, amount, notes)
    )
    conn.commit()
    conn.close()


def delete_estimated_income(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM estimated_income WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


# ── Estimated Expenses ───────────────────────────────────────────────────────

def get_estimated_expenses(event_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT ee.*, d.name as dept_name, d.color as dept_color
           FROM estimated_expenses ee
           LEFT JOIN departments d ON ee.department_id = d.id
           WHERE ee.event_id=? ORDER BY d.name, ee.category, ee.created_at""",
        (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_estimated_expenses_by_dept(event_id, dept_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM estimated_expenses
           WHERE event_id=? AND department_id=?
           ORDER BY category, created_at""",
        (event_id, dept_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_estimated_expense(event_id, dept_id, category, item_name, description,
                           amount, quantity=1, unit="unit", notes=""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO estimated_expenses
           (event_id, department_id, category, item_name, description,
            amount, quantity, unit, notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (event_id, dept_id, category, item_name, description,
         amount, quantity, unit, notes)
    )
    conn.commit()
    conn.close()


def update_estimated_expense(row_id, category, item_name, description, amount, quantity, unit, notes):
    conn = get_connection()
    conn.execute(
        """UPDATE estimated_expenses
           SET category=?, item_name=?, description=?, amount=?, quantity=?, unit=?, notes=?
           WHERE id=?""",
        (category, item_name, description, amount, quantity, unit, notes, row_id)
    )
    conn.commit()
    conn.close()


def delete_estimated_expense(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM estimated_expenses WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


# ── Actual Income ────────────────────────────────────────────────────────────

def get_actual_income(event_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM actual_income WHERE event_id=? ORDER BY created_at", (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_actual_income(event_id, source, category, amount, received_on,
                      payment_mode, reference="", notes=""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO actual_income
           (event_id, source, category, amount, received_on, payment_mode, reference, notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (event_id, source, category, amount, received_on, payment_mode, reference, notes)
    )
    conn.commit()
    conn.close()


def delete_actual_income(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM actual_income WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


# ── Actual Expenses ──────────────────────────────────────────────────────────

def get_actual_expenses(event_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT ae.*, d.name as dept_name, d.color as dept_color
           FROM actual_expenses ae
           LEFT JOIN departments d ON ae.department_id = d.id
           WHERE ae.event_id=? ORDER BY d.name, ae.category, ae.created_at""",
        (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_actual_expenses_by_dept(event_id, dept_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM actual_expenses
           WHERE event_id=? AND department_id=?
           ORDER BY category, created_at""",
        (event_id, dept_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_actual_expense(event_id, dept_id, category, item_name, description,
                       amount, paid_on, payment_mode, status,
                       quantity=1, unit="unit", reference="", notes=""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO actual_expenses
           (event_id, department_id, category, item_name, description,
            amount, quantity, unit, paid_on, payment_mode, status, reference, notes)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (event_id, dept_id, category, item_name, description,
         amount, quantity, unit, paid_on, payment_mode, status, reference, notes)
    )
    conn.commit()
    conn.close()


def update_actual_expense(row_id, category, item_name, description, amount,
                           quantity, unit, paid_on, payment_mode, status, notes):
    conn = get_connection()
    conn.execute(
        """UPDATE actual_expenses
           SET category=?, item_name=?, description=?, amount=?,
               quantity=?, unit=?, paid_on=?, payment_mode=?, status=?, notes=?
           WHERE id=?""",
        (category, item_name, description, amount,
         quantity, unit, paid_on, payment_mode, status, notes, row_id)
    )
    conn.commit()
    conn.close()


def delete_actual_expense(row_id):
    conn = get_connection()
    conn.execute("DELETE FROM actual_expenses WHERE id=?", (row_id,))
    conn.commit()
    conn.close()


# ── Sponsors ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_sponsors(event_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sponsors WHERE event_id=? ORDER BY amount DESC", (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_sponsor(event_id, name, tier, contact_name, contact_email, amount, notes=""):
    """Add sponsor and automatically record their amount as actual income."""
    import datetime
    conn = get_connection()

    # Insert into sponsors
    cur = conn.execute(
        """INSERT INTO sponsors
           (event_id, name, tier, contact_name, contact_email, amount, income_synced, notes)
           VALUES (?,?,?,?,?,?,1,?)""",
        (event_id, name, tier, contact_name, contact_email, amount, notes)
    )
    sponsor_id = cur.lastrowid

    # Auto-insert into actual_income so sponsor money counts in event revenue
    if amount > 0:
        conn.execute(
            """INSERT INTO actual_income
               (event_id, source, category, amount, received_on, payment_mode, sponsor_id, notes)
               VALUES (?,?,?,?,?,?,?,?)""",
            (event_id, f"Sponsor: {name}", "Sponsor", amount,
             str(datetime.date.today()), "Bank Transfer", sponsor_id,
             f"{tier} Sponsor — {notes}" if notes else f"{tier} Sponsor")
        )

    conn.commit()
    conn.close()
    return sponsor_id


def delete_sponsor(sid):
    """Delete sponsor and its linked income entry."""
    conn = get_connection()
    # Remove linked income entry first
    conn.execute("DELETE FROM actual_income WHERE sponsor_id=?", (sid,))
    conn.execute("DELETE FROM sponsors WHERE id=?", (sid,))
    conn.commit()
    conn.close()


# ── Vendors ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_vendors(event_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM vendors WHERE event_id=? ORDER BY contract_value DESC", (event_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_vendor(event_id, name, category, contact_name, contact_email,
               contract_value, dept_id=None, notes=""):
    """Add vendor and auto-create an actual expense entry linked to it."""
    import datetime
    conn = get_connection()

    # Insert vendor
    cur = conn.execute(
        """INSERT INTO vendors
           (event_id, name, category, contact_name, contact_email, contract_value, notes)
           VALUES (?,?,?,?,?,?,?)""",
        (event_id, name, category, contact_name, contact_email, contract_value, notes)
    )
    vendor_id = cur.lastrowid

    # Auto-create actual expense so vendor cost appears in financials
    if contract_value > 0:
        conn.execute(
            """INSERT INTO actual_expenses
               (event_id, department_id, vendor_id, category, item_name,
                description, amount, paid_on, payment_mode, status, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (event_id, dept_id, vendor_id, category,
             f"Vendor: {name}",
             f"Contract with {name}{(' — ' + notes) if notes else ''}",
             contract_value,
             str(datetime.date.today()), "Bank Transfer", "pending",
             f"Auto-created from vendor entry")
        )

    conn.commit()
    conn.close()
    return vendor_id


def delete_vendor(vid):
    """Delete vendor and its linked expense entry."""
    conn = get_connection()
    conn.execute("DELETE FROM actual_expenses WHERE vendor_id=?", (vid,))
    conn.execute("DELETE FROM vendors WHERE id=?", (vid,))
    conn.commit()
    conn.close()


# ── Financial Summary ────────────────────────────────────────────────────────

@st.cache_data(ttl=5)
def get_event_summary(event_id):
    conn = get_connection()

    est_inc = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM estimated_income WHERE event_id=?", (event_id,)
    ).fetchone()[0]
    est_exp = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM estimated_expenses WHERE event_id=?", (event_id,)
    ).fetchone()[0]
    act_inc = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM actual_income WHERE event_id=?", (event_id,)
    ).fetchone()[0]
    act_exp = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM actual_expenses WHERE event_id=?", (event_id,)
    ).fetchone()[0]
    spon    = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM sponsors WHERE event_id=?", (event_id,)
    ).fetchone()[0]

    conn.close()
    return {
        "est_income":       est_inc,
        "est_expense":      est_exp,
        "est_profit":       est_inc - est_exp,
        "act_income":       act_inc,
        "act_expense":      act_exp,
        "act_profit":       act_inc - act_exp,
        "sponsors_total":   spon,
        "income_variance":  act_inc - est_inc,
        "expense_variance": act_exp - est_exp,
        "budget_accuracy":  max(0, (1 - abs(act_exp - est_exp) / max(est_exp, 1)) * 100),
    }