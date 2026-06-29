"""EventLedger AI – Main Application Entry Point v2.0"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="EventLedger AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database.schema import init_db, seed_demo_data
init_db()
seed_demo_data()

# ── Session defaults ──────────────────────────────────────────────────────────
for key, val in [("user",None),("page","dashboard"),
                 ("active_event",None),("active_proposal",None)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not st.session_state.user:
    from pages.auth import show as show_auth
    show_auth(); st.stop()

user = st.session_state.user
from utils.app_mode import is_single_user
from components.ui import render_sidebar
render_sidebar(user)

page = st.session_state.page

# ── Pages available in BOTH modes ─────────────────────────────────────────────
if page == "dashboard":
    from pages.dashboard import show; show(user)

elif page == "events":
    from pages.events import show; show(user)

elif page == "event_detail":
    eid = st.session_state.active_event
    if eid:
        from pages.event_detail import show; show(eid)
    else:
        st.session_state.page = "events"; st.rerun()

elif page == "finance":
    from pages.finance_sponsors_vendors import show_finance; show_finance(user)

elif page == "sponsors":
    from pages.finance_sponsors_vendors import show_sponsors; show_sponsors(user)

elif page == "vendors":
    from pages.finance_sponsors_vendors import show_vendors; show_vendors(user)

elif page == "analytics":
    from pages.analytics import show; show(user)

elif page == "ai_insights":
    from pages.ai_insights import show; show(user)

elif page == "reports":
    from pages.reports_archive_settings import show_reports; show_reports(user)

elif page == "archive":
    from pages.reports_archive_settings import show_archive; show_archive(user)

elif page == "settings":
    from pages.reports_archive_settings import show_settings; show_settings(user)

elif page == "notifications":
    from pages.notifications import show; show(user)

# ── Multi-user only pages ──────────────────────────────────────────────────────
elif page == "approvals":
    if is_single_user():
        st.info("🟢 Approvals are not needed in Single User mode — you have full access.")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"; st.rerun()
    else:
        from pages.approvals import show; show(user)

elif page == "user_management":
    if is_single_user():
        st.info("🟢 User management is not available in Single User mode.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"; st.rerun()
    else:
        from pages.user_management import show; show(user)

elif page == "audit_log":
    if is_single_user():
        st.info("🟢 Audit log is a Multi User feature.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"; st.rerun()
    else:
        from pages.audit_log_page import show; show(user)

elif page == "create_proposal":
    if is_single_user():
        st.info("🟢 Budget proposals are not needed in Single User mode. Use the Planning tab directly.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"; st.rerun()
    else:
        from pages.proposal_detail import show_create; show_create(user)

elif page == "proposal_detail":
    if is_single_user():
        st.info("🟢 Budget proposals are not needed in Single User mode.")
        if st.button("← Back"):
            st.session_state.page = "dashboard"; st.rerun()
    else:
        from pages.proposal_detail import show_detail; show_detail(user)

else:
    st.error(f"Page '{page}' not found.")
    if st.button("← Dashboard"):
        st.session_state.page = "dashboard"; st.rerun()
