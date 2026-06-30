"""
EventLedger AI – Backup & Restore Engine
Exports the entire database to a single JSON file and restores from it.
Handles datetime/date serialization automatically.
"""

import json
import datetime
from database.schema import get_connection

# Tables in dependency order (parents before children) so restore
# can be done safely without foreign-key violations.
TABLES = [
    "users",
    "events",
    "departments",
    "user_event_roles",
    "budget_proposals",
    "budget_line_items",
    "estimated_income",
    "estimated_expenses",
    "actual_income",
    "actual_expenses",
    "sponsors",
    "vendors",
    "notifications",
    "audit_log",
    "org_settings",
]


def _json_default(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    return str(obj)


def export_backup() -> bytes:
    """
    Returns a JSON backup of every table as UTF-8 bytes,
    ready to hand to st.download_button.
    """
    conn = get_connection()
    backup = {
        "_meta": {
            "app": "EventLedger AI",
            "exported_at": datetime.datetime.utcnow().isoformat(),
            "version": 1,
        }
    }
    for table in TABLES:
        try:
            rows = conn.execute(f"SELECT * FROM {table}").fetchall()
            backup[table] = [dict(r) for r in rows]
        except Exception as e:
            backup[table] = {"_error": str(e)}
    conn.close()
    return json.dumps(backup, default=_json_default, indent=2).encode("utf-8")


def validate_backup(file_bytes: bytes) -> dict:
    """
    Parses and sanity-checks a backup file before restore.
    Returns {"ok": bool, "data": dict|None, "message": str, "counts": dict}
    """
    try:
        data = json.loads(file_bytes.decode("utf-8"))
    except Exception as e:
        return {"ok": False, "data": None, "message": f"Invalid JSON file: {e}", "counts": {}}

    if "_meta" not in data or data.get("_meta", {}).get("app") != "EventLedger AI":
        return {"ok": False, "data": None,
                "message": "This doesn't look like an EventLedger AI backup file.",
                "counts": {}}

    counts = {t: len(data.get(t, [])) for t in TABLES if isinstance(data.get(t), list)}
    return {"ok": True, "data": data, "message": "Valid backup file", "counts": counts}


def restore_backup(data: dict, wipe_existing: bool = True) -> dict:
    """
    Restores all tables from a parsed backup dict.
    wipe_existing=True clears current data first (full restore).
    Returns {"ok": bool, "message": str, "restored": dict}
    """
    conn = get_connection()
    restored = {}
    try:
        if wipe_existing:
            # Delete children first, in reverse dependency order
            for table in reversed(TABLES):
                try:
                    conn.execute(f"DELETE FROM {table}")
                except Exception:
                    pass

        for table in TABLES:
            rows = data.get(table)
            if not isinstance(rows, list) or not rows:
                restored[table] = 0
                continue

            cols = list(rows[0].keys())
            col_str = ", ".join(cols)
            placeholders = ", ".join(["?"] * len(cols))
            sql = f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})"

            count = 0
            for row in rows:
                values = tuple(row.get(c) for c in cols)
                try:
                    conn.execute(sql, values)
                    count += 1
                except Exception:
                    pass
            restored[table] = count

        conn.commit()

        # Reset auto-increment sequences so new rows don't collide
        # with the restored explicit IDs.
        for table in TABLES:
            if table == "org_settings":
                continue  # uses 'key' as PK, not 'id'
            try:
                conn.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                )
            except Exception:
                pass
        conn.commit()

        return {"ok": True, "message": "Restore completed successfully.", "restored": restored}
    except Exception as e:
        conn.rollback()
        return {"ok": False, "message": f"Restore failed: {e}", "restored": restored}
    finally:
        conn.close()
