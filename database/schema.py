"""
EventLedger AI – Database Schema v2.0 (PostgreSQL / Neon)
Drop-in replacement for the SQLite schema.
All ? placeholders are converted to %s transparently via the
PgConnection wrapper, so helpers.py and every other file
require zero changes.
"""

import os
import re
import psycopg2
import psycopg2.extras
import streamlit as st


# ── Connection ────────────────────────────────────────────────────────────────

def _get_dsn() -> str:
    """Return the DATABASE_URL from env or Streamlit secrets."""
    dsn = os.environ.get("DATABASE_URL") or st.secrets.get("DATABASE_URL", "")
    if not dsn:
        raise RuntimeError(
            "DATABASE_URL not set. Add it to your environment variables or "
            ".streamlit/secrets.toml"
        )
    return dsn


class PgCursor:
    """
    Wraps a psycopg2 cursor to:
      - convert SQLite ? placeholders → %s
      - expose .lastrowid (via RETURNING id)
      - make fetchone() / fetchall() return dict-like RealDictRow objects
    """

    def __init__(self, cur):
        self._cur = cur
        self.lastrowid = None

    @staticmethod
    def _fix(sql: str) -> str:
        """Replace ? with %s, fix SQLite-only syntax."""
        sql = re.sub(r'\?', '%s', sql)
        # AUTOINCREMENT → nothing (SERIAL handles it)
        sql = re.sub(r'\bAUTOINCREMENT\b', '', sql, flags=re.IGNORECASE)
        # INTEGER PRIMARY KEY → SERIAL PRIMARY KEY
        sql = re.sub(
            r'\bINTEGER\s+PRIMARY\s+KEY\b',
            'SERIAL PRIMARY KEY',
            sql, flags=re.IGNORECASE
        )
        # datetime('now') → NOW()
        sql = re.sub(r"datetime\('now'\)", 'NOW()', sql, flags=re.IGNORECASE)
        # TEXT DEFAULT (datetime('now')) already handled above
        # PRAGMA → ignore (we'll skip pragma calls)
        # INSERT OR IGNORE → INSERT ... ON CONFLICT DO NOTHING
        sql = re.sub(
            r'\bINSERT\s+OR\s+IGNORE\b',
            'INSERT',
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r'\bINSERT\s+OR\s+REPLACE\b',
            'INSERT',
            sql, flags=re.IGNORECASE
        )
        return sql

    def execute(self, sql: str, params=None):
        # Skip SQLite pragmas silently
        if sql.strip().upper().startswith("PRAGMA"):
            return self

        sql = self._fix(sql)

        # Handle INSERT OR IGNORE → ON CONFLICT DO NOTHING
        is_insert = sql.strip().upper().startswith("INSERT")
        needs_returning = is_insert and "RETURNING" not in sql.upper()

        if needs_returning:
            # Check if table has an id column — add RETURNING id
            sql = sql.rstrip().rstrip(";") + " RETURNING id"

        # Handle INSERT ... ON CONFLICT DO NOTHING
        if "INSERT OR IGNORE" in sql.upper() or re.search(
            r'INSERT\s+OR\s+IGNORE', sql, re.IGNORECASE
        ):
            sql = sql.rstrip().rstrip(";")
            if "ON CONFLICT" not in sql.upper():
                sql += " ON CONFLICT DO NOTHING"
            if needs_returning:
                sql += " RETURNING id"

        if params:
            self._cur.execute(sql, params)
        else:
            self._cur.execute(sql)

        if is_insert:
            try:
                row = self._cur.fetchone()
                self.lastrowid = row["id"] if row else None
            except Exception:
                self.lastrowid = None

        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __iter__(self):
        return iter(self._cur)


class PgConnection:
    """
    Wraps a psycopg2 connection to look like sqlite3.connect() output.
    - execute() / cursor() return PgCursor
    - commit() / close() pass through
    - row_factory is handled via RealDictCursor (rows are dict-like)
    """

    def __init__(self, dsn: str):
        self._conn = psycopg2.connect(
            dsn,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        self._conn.autocommit = False

    def cursor(self):
        return PgCursor(self._conn.cursor())

    def execute(self, sql: str, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_connection() -> PgConnection:
    return PgConnection(_get_dsn())


# ── Schema creation ───────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id             SERIAL PRIMARY KEY,
    name           TEXT    NOT NULL,
    email          TEXT    UNIQUE NOT NULL,
    password       TEXT    NOT NULL,
    role           TEXT    NOT NULL DEFAULT 'member',
    is_super_admin INTEGER DEFAULT 0,
    org_name       TEXT,
    avatar_color   TEXT    DEFAULT '#6366f1',
    is_active      INTEGER DEFAULT 1,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_event_roles (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    event_id    INTEGER,
    role        TEXT    NOT NULL,
    dept_id     INTEGER,
    assigned_by INTEGER,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, event_id, role, dept_id)
);

CREATE TABLE IF NOT EXISTS events (
    id                 SERIAL PRIMARY KEY,
    user_id            INTEGER NOT NULL,
    name               TEXT    NOT NULL,
    description        TEXT,
    venue              TEXT,
    start_date         TEXT,
    end_date           TEXT,
    expected_attendees INTEGER DEFAULT 0,
    status             TEXT    DEFAULT 'planning',
    phase              TEXT    DEFAULT 'planning',
    currency           TEXT    DEFAULT 'INR',
    is_locked          INTEGER DEFAULT 0,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS departments (
    id         SERIAL PRIMARY KEY,
    event_id   INTEGER NOT NULL,
    name       TEXT    NOT NULL,
    head_name  TEXT,
    manager    TEXT,
    color      TEXT    DEFAULT '#6366f1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget_proposals (
    id              SERIAL PRIMARY KEY,
    event_id        INTEGER NOT NULL,
    department_id   INTEGER NOT NULL,
    submitted_by    INTEGER NOT NULL,
    title           TEXT    NOT NULL,
    total_amount    REAL    DEFAULT 0,
    status          TEXT    DEFAULT 'draft',
    version         INTEGER DEFAULT 1,
    submitted_at    TEXT,
    reviewed_by     INTEGER,
    reviewed_at     TEXT,
    approved_by     INTEGER,
    approved_at     TEXT,
    rejected_by     INTEGER,
    rejected_at     TEXT,
    reject_reason   TEXT,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget_line_items (
    id           SERIAL PRIMARY KEY,
    proposal_id  INTEGER NOT NULL,
    category     TEXT    NOT NULL,
    item_name    TEXT    NOT NULL,
    description  TEXT,
    quantity     REAL    DEFAULT 1,
    unit         TEXT    DEFAULT 'unit',
    unit_price   REAL    DEFAULT 0,
    total_amount REAL    DEFAULT 0,
    notes        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS estimated_income (
    id         SERIAL PRIMARY KEY,
    event_id   INTEGER NOT NULL,
    source     TEXT    NOT NULL,
    category   TEXT    DEFAULT 'Other',
    amount     REAL    DEFAULT 0,
    notes      TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS estimated_expenses (
    id            SERIAL PRIMARY KEY,
    event_id      INTEGER NOT NULL,
    department_id INTEGER,
    proposal_id   INTEGER,
    category      TEXT    NOT NULL,
    item_name     TEXT,
    description   TEXT,
    quantity      REAL    DEFAULT 1,
    unit          TEXT    DEFAULT 'unit',
    amount        REAL    DEFAULT 0,
    status        TEXT    DEFAULT 'draft',
    submitted_at  TEXT,
    approved_at   TEXT,
    approved_by   INTEGER,
    rejected_at   TEXT,
    rejected_by   INTEGER,
    reject_reason TEXT,
    version       INTEGER DEFAULT 1,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS actual_income (
    id           SERIAL PRIMARY KEY,
    event_id     INTEGER NOT NULL,
    source       TEXT    NOT NULL,
    category     TEXT    DEFAULT 'Other',
    amount       REAL    DEFAULT 0,
    received_on  TEXT,
    payment_mode TEXT    DEFAULT 'Cash',
    reference    TEXT,
    sponsor_id   INTEGER DEFAULT NULL,
    notes        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS actual_expenses (
    id            SERIAL PRIMARY KEY,
    event_id      INTEGER NOT NULL,
    department_id INTEGER,
    vendor_id     INTEGER,
    category      TEXT    NOT NULL,
    item_name     TEXT,
    description   TEXT,
    quantity      REAL    DEFAULT 1,
    unit          TEXT    DEFAULT 'unit',
    amount        REAL    DEFAULT 0,
    paid_on       TEXT,
    payment_mode  TEXT    DEFAULT 'Cash',
    status        TEXT    DEFAULT 'paid',
    reference     TEXT,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sponsors (
    id            SERIAL PRIMARY KEY,
    event_id      INTEGER NOT NULL,
    name          TEXT    NOT NULL,
    tier          TEXT    DEFAULT 'Bronze',
    contact_name  TEXT,
    contact_email TEXT,
    amount        REAL    DEFAULT 0,
    status        TEXT    DEFAULT 'confirmed',
    income_synced INTEGER DEFAULT 0,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendors (
    id             SERIAL PRIMARY KEY,
    event_id       INTEGER NOT NULL,
    name           TEXT    NOT NULL,
    category       TEXT    DEFAULT 'Other',
    contact_name   TEXT,
    contact_email  TEXT,
    contract_value REAL    DEFAULT 0,
    status         TEXT    DEFAULT 'active',
    notes          TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    event_id   INTEGER,
    title      TEXT    NOT NULL,
    message    TEXT    NOT NULL,
    type       TEXT    DEFAULT 'info',
    is_read    INTEGER DEFAULT 0,
    link_page  TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER,
    event_id    INTEGER,
    action      TEXT    NOT NULL,
    entity_type TEXT,
    entity_id   INTEGER,
    details     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS org_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init_db():
    conn = get_connection()
    cur = conn._conn.cursor()
    for statement in _DDL.strip().split(";"):
        stmt = statement.strip()
        if stmt:
            cur.execute(stmt)
    # Default settings
    cur.execute(
        "INSERT INTO org_settings (key,value) VALUES ('currency','INR') "
        "ON CONFLICT (key) DO NOTHING"
    )
    cur.execute(
        "INSERT INTO org_settings (key,value) VALUES ('app_mode','single_user') "
        "ON CONFLICT (key) DO NOTHING"
    )
    conn.commit()
    conn.close()


def migrate_db():
    """No-op for PostgreSQL — schema is created fresh via init_db."""
    pass


# ── Seed data ─────────────────────────────────────────────────────────────────

def seed_demo_data():
    conn = get_connection()
    c    = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    row = c.fetchone()
    count = list(row.values())[0] if row else 0
    if count > 0:
        conn.close()
        return

    import hashlib
    def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()

    def ins(sql, params):
        """Insert and return lastrowid."""
        sql2 = sql.rstrip().rstrip(";") + " RETURNING id"
        c._cur.execute(sql2, params)
        row = c._cur.fetchone()
        return row["id"] if row else None

    # Users
    sa_id = ins(
        "INSERT INTO users (name,email,password,role,is_super_admin,org_name,avatar_color) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        ("Alex Morgan","demo@eventledger.ai",hp("demo123"),"super_admin",1,"EventPro Inc.","#6366f1")
    )
    ea_id = ins(
        "INSERT INTO users (name,email,password,role,org_name,avatar_color) VALUES (%s,%s,%s,%s,%s,%s)",
        ("Rahul Sharma","rahul@eventledger.ai",hp("rahul123"),"event_admin","EventPro Inc.","#f59e0b")
    )
    fh_id = ins(
        "INSERT INTO users (name,email,password,role,org_name,avatar_color) VALUES (%s,%s,%s,%s,%s,%s)",
        ("Priya Patel","priya@eventledger.ai",hp("priya123"),"finance_head","EventPro Inc.","#10b981")
    )
    mktg_head_id = ins(
        "INSERT INTO users (name,email,password,role,org_name,avatar_color) VALUES (%s,%s,%s,%s,%s,%s)",
        ("Amit Kumar","amit@eventledger.ai",hp("amit123"),"dept_head","EventPro Inc.","#ef4444")
    )
    ops_head_id = ins(
        "INSERT INTO users (name,email,password,role,org_name,avatar_color) VALUES (%s,%s,%s,%s,%s,%s)",
        ("Neha Singh","neha@eventledger.ai",hp("neha123"),"dept_head","EventPro Inc.","#8b5cf6")
    )

    # Event
    eid = ins(
        """INSERT INTO events (user_id,name,description,venue,start_date,end_date,
           expected_attendees,status,phase,currency) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (sa_id,"TechFest 2027","Annual technology festival","SMT CHM College",
         "2027-03-15","2027-03-17",2000,"active","planning","INR")
    )

    # Roles
    for uid, role in [(ea_id,"event_admin"),(fh_id,"finance_head"),
                       (mktg_head_id,"dept_head"),(ops_head_id,"dept_head")]:
        c._cur.execute(
            "INSERT INTO user_event_roles (user_id,event_id,role,assigned_by) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (uid, eid, role, sa_id)
        )

    # Departments
    dept_ids = []
    for nm, hd, col in [("Marketing","Amit Kumar","#f59e0b"),
                         ("Operations","Neha Singh","#10b981"),
                         ("Tech & AV","Rahul Sharma","#6366f1"),
                         ("Catering","TBD","#ef4444")]:
        did = ins(
            "INSERT INTO departments (event_id,name,head_name,color) VALUES (%s,%s,%s,%s)",
            (eid,nm,hd,col)
        )
        dept_ids.append(did)

    c._cur.execute(
        "INSERT INTO user_event_roles (user_id,event_id,role,dept_id,assigned_by) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        (mktg_head_id, eid, "dept_head", dept_ids[0], sa_id)
    )
    c._cur.execute(
        "INSERT INTO user_event_roles (user_id,event_id,role,dept_id,assigned_by) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
        (ops_head_id, eid, "dept_head", dept_ids[1], sa_id)
    )

    # Estimated income
    for src,cat,amt in [("Ticket Sales","Tickets",80000),
                         ("Sponsorships","Sponsor",50000),
                         ("Merchandise","Sales",15000)]:
        ins("INSERT INTO estimated_income (event_id,source,category,amount) VALUES (%s,%s,%s,%s)",
            (eid,src,cat,amt))

    # Budget proposals
    proposals = [
        (dept_ids[0], mktg_head_id, "Marketing Budget Q1", 35000, "approved"),
        (dept_ids[1], ops_head_id,  "Operations Budget",   45000, "submitted"),
        (dept_ids[2], ea_id,        "Tech & AV Budget",    28000, "draft"),
        (dept_ids[3], sa_id,        "Catering Budget",     25000, "rejected"),
    ]
    prop_ids = []
    for did, uid, title, amt, status in proposals:
        sub_at = "2027-01-10" if status != "draft" else None
        app_by = fh_id if status == "approved" else None
        app_at = "2027-01-12" if status == "approved" else None
        rej_by = fh_id if status == "rejected" else None
        rej_at = "2027-01-11" if status == "rejected" else None
        rej_rsn = "Please reduce catering staff cost by 20%" if status == "rejected" else None
        pid = ins(
            """INSERT INTO budget_proposals
               (event_id,department_id,submitted_by,title,total_amount,status,
                submitted_at,approved_by,approved_at,rejected_by,rejected_at,reject_reason)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (eid,did,uid,title,amt,status,sub_at,app_by,app_at,rej_by,rej_at,rej_rsn)
        )
        prop_ids.append(pid)

    # Line items
    for pid,cat,item,desc,qty,unit,up,tot in [
        (prop_ids[0],"Marketing","Social Media Ads","Facebook & Instagram",1,"campaign",12000,12000),
        (prop_ids[0],"Marketing","Print Materials","Banners 10x4ft",10,"pcs",800,8000),
        (prop_ids[0],"Marketing","Promotional Gifts","T-Shirts & Caps",100,"pcs",150,15000),
    ]:
        ins(
            """INSERT INTO budget_line_items
               (proposal_id,category,item_name,description,quantity,unit,unit_price,total_amount)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (pid,cat,item,desc,qty,unit,up,tot)
        )

    # Estimated expenses
    for cat,item,amt in [("Marketing","Social Media Ads",12000),
                          ("Marketing","Print Materials",8000),
                          ("Marketing","Promotional Gifts",15000)]:
        ins(
            "INSERT INTO estimated_expenses (event_id,department_id,proposal_id,category,item_name,amount) VALUES (%s,%s,%s,%s,%s,%s)",
            (eid,dept_ids[0],prop_ids[0],cat,item,amt)
        )

    # Actual income
    for src,cat,amt,dt,mode in [
        ("Ticket Sales","Tickets",85000,"2027-03-01","Online"),
        ("Merchandise","Sales",11000,"2027-03-16","Cash")
    ]:
        ins(
            "INSERT INTO actual_income (event_id,source,category,amount,received_on,payment_mode) VALUES (%s,%s,%s,%s,%s,%s)",
            (eid,src,cat,amt,dt,mode)
        )

    # Sponsors
    for name,tier,amt in [("TechCorp Inc.","Platinum",25000),("DataSoft","Gold",15000)]:
        sp_id = ins(
            "INSERT INTO sponsors (event_id,name,tier,amount,income_synced) VALUES (%s,%s,%s,%s,%s)",
            (eid,name,tier,amt,1)
        )
        ins(
            "INSERT INTO actual_income (event_id,source,category,amount,received_on,payment_mode,sponsor_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (eid,f"Sponsor: {name}","Sponsor",amt,"2027-02-20","Bank Transfer",sp_id)
        )

    # Actual expenses
    for did,cat,item,amt,dt in [
        (dept_ids[0],"Marketing","Social Media Ads",13500,"2027-02-28"),
        (dept_ids[0],"Marketing","Print Materials",3800,"2027-03-01"),
        (dept_ids[1],"Operations","Venue Rental",30000,"2027-03-01"),
    ]:
        ins(
            "INSERT INTO actual_expenses (event_id,department_id,category,item_name,amount,paid_on,status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (eid,did,cat,item,amt,dt,"paid")
        )

    # Notifications
    for uid,evid,title,msg,typ in [
        (sa_id,eid,"Budget Submitted","Marketing submitted budget for ₹35,000","info"),
        (sa_id,eid,"⚠️ Overspending Alert","Marketing is 12.5% over estimated budget","warning"),
        (fh_id,eid,"Budget to Review","Operations submitted budget for ₹45,000","info"),
        (mktg_head_id,eid,"✅ Budget Approved","Your Marketing budget has been approved","success"),
    ]:
        ins(
            "INSERT INTO notifications (user_id,event_id,title,message,type) VALUES (%s,%s,%s,%s,%s)",
            (uid,evid,title,msg,typ)
        )

    # Audit log
    for uid,evid,action,etype,eid_,details in [
        (sa_id,eid,"CREATE_EVENT","events",eid,"Created TechFest 2027"),
        (mktg_head_id,eid,"SUBMIT_BUDGET","budget_proposals",prop_ids[0],"Marketing submitted budget ₹35,000"),
        (fh_id,eid,"APPROVE_BUDGET","budget_proposals",prop_ids[0],"Finance approved Marketing budget"),
        (fh_id,eid,"REJECT_BUDGET","budget_proposals",prop_ids[3],"Finance rejected Catering budget"),
    ]:
        ins(
            "INSERT INTO audit_log (user_id,event_id,action,entity_type,entity_id,details) VALUES (%s,%s,%s,%s,%s,%s)",
            (uid,evid,action,etype,eid_,details)
        )

    conn.commit()
    conn.close()
