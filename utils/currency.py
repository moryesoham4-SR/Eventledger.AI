"""
EventLedger AI – Currency Utilities
Single source of truth for currency symbol and global setting.
"""

import streamlit as st
from database.schema import get_connection

# ── Supported currencies ────────────────────────────────────────────────────
CURRENCIES = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "AED": "AED ",
    "SGD": "S$",
    "JPY": "¥",
    "CAD": "C$",
    "AUD": "A$",
    "BDT": "৳",
    "NPR": "Rs.",
    "MYR": "RM",
}

CURRENCY_LABELS = {
    "INR": "INR (₹) — Indian Rupee",
    "USD": "USD ($) — US Dollar",
    "EUR": "EUR (€) — Euro",
    "GBP": "GBP (£) — British Pound",
    "AED": "AED — UAE Dirham",
    "SGD": "SGD (S$) — Singapore Dollar",
    "JPY": "JPY (¥) — Japanese Yen",
    "CAD": "CAD (C$) — Canadian Dollar",
    "AUD": "AUD (A$) — Australian Dollar",
    "BDT": "BDT (৳) — Bangladeshi Taka",
    "NPR": "NPR (Rs.) — Nepalese Rupee",
    "MYR": "MYR (RM) — Malaysian Ringgit",
}


def _ensure_settings_table():
    """Create org_settings table if it doesn't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS org_settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    # Seed default = INR
    conn.execute("""
        INSERT OR IGNORE INTO org_settings (key, value) VALUES ('currency', 'INR')
    """)
    conn.commit()
    conn.close()


def get_global_currency() -> str:
    """Return the org-level currency code, defaulting to INR."""
    # Check session state cache first (avoids DB hit on every render)
    if "global_currency" in st.session_state:
        return st.session_state.global_currency
    try:
        _ensure_settings_table()
        conn = get_connection()
        row  = conn.execute(
            "SELECT value FROM org_settings WHERE key='currency'"
        ).fetchone()
        conn.close()
        code = row[0] if row else "INR"
    except Exception:
        code = "INR"
    st.session_state.global_currency = code
    return code


def set_global_currency(code: str):
    """Persist a new global currency and update session cache."""
    _ensure_settings_table()
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO org_settings (key, value) VALUES ('currency', ?)",
        (code,)
    )
    conn.commit()
    conn.close()
    st.session_state.global_currency = code


def get_symbol(code: str = None) -> str:
    """Return the currency symbol for the given code (or global if None)."""
    if code is None:
        code = get_global_currency()
    return CURRENCIES.get(code, code + " ")


def fmt(amount: float, code: str = None) -> str:
    """Format a number with the currency symbol."""
    sym = get_symbol(code)
    if abs(amount) >= 1_000_000:
        return f"{sym}{amount/1_000_000:.2f}M"
    if abs(amount) >= 1_000:
        return f"{sym}{amount/1_000:.1f}K"
    return f"{sym}{amount:,.0f}"
