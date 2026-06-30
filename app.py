"""EventLedger AI – Main Application Entry Point"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="EventLedger AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Glossy Electric Theme ─────────────────────────────────────────────────────
st.markdown("""
<style>
/* Base */
html, body, [data-testid="stAppViewContainer"] {
    background: #060a12 !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080e1a 0%, #060a12 100%) !important;
    border-right: 0.5px solid #1a3a5c !important;
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00d4ff33, transparent);
}

/* Cards / containers */
[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] {
    background: linear-gradient(135deg, #0d1f33cc, #091525cc);
    border: 0.5px solid #1a4060;
    border-radius: 12px;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0d1f33, #091525) !important;
    border: 0.5px solid #1a4060 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    position: relative;
    overflow: hidden;
}
[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, #00d4ff55, transparent);
}
[data-testid="stMetricValue"] {
    background: linear-gradient(135deg, #00d4ff, #7eb8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 600 !important;
}
[data-testid="stMetricLabel"] {
    color: #4a7fa8 !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00d4ff22, #0055aa33) !important;
    border: 0.5px solid #00d4ff55 !important;
    color: #00d4ff !important;
    border-radius: 20px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00d4ff44, #0055aa55) !important;
    border-color: #00d4ffaa !important;
    box-shadow: 0 0 15px #00d4ff33 !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00d4ff, #0088cc) !important;
    color: #060a12 !important;
    border: none !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 20px #00d4ff55 !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stTextArea > div > div > textarea {
    background: #0a1422 !important;
    border: 0.5px solid #1a4060 !important;
    color: #e2f0ff !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #00d4ff88 !important;
    box-shadow: 0 0 10px #00d4ff22 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0a1422 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 0.5px solid #1a4060 !important;
}
.stTabs [data-baseweb="tab"] {
    color: #4a7fa8 !important;
    border-radius: 8px !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #00d4ff22, #0055aa33) !important;
    color: #00d4ff !important;
    border: 0.5px solid #00d4ff44 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 0.5px solid #1a4060 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* Progress bars */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #0055aa, #00d4ff) !important;
    border-radius: 3px !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div {
    background: #0a1422 !important;
    border: 0.5px solid #1a4060 !important;
    border-radius: 8px !important;
}

/* Success / error / warning */
.stSuccess {
    background: linear-gradient(135deg, #003322, #004433) !important;
    border: 0.5px solid #00e5a044 !important;
    border-radius: 8px !important;
    color: #00e5a0 !important;
}
.stError {
    background: linear-gradient(135deg, #1a0505, #220808) !important;
    border: 0.5px solid #ff5a5a44 !important;
    border-radius: 8px !important;
}
.stWarning {
    background: linear-gradient(135deg, #1a1000, #221500) !important;
    border: 0.5px solid #ffaa0044 !important;
    border-radius: 8px !important;
}

/* Headings */
h1, h2, h3 {
    background: linear-gradient(135deg, #00d4ff, #7eb8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 600 !important;
}

/* Sidebar text */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    background: linear-gradient(135deg, #00d4ff, #7eb8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Divider */
hr {
    border-color: #1a4060 !important;
    background: linear-gradient(90deg, transparent, #00d4ff33, transparent) !important;
    height: 1px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #060a12; }
::-webkit-scrollbar-thumb { background: #1a4060; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #00d4ff55; }

/* Ambient glow effect */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: -200px; right: -200px;
    width: 600px; height: 600px;
    background: radial-gradient(circle, #00d4ff08 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}
</style>
""", unsafe_allow_html=True)


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
        from pages.event_detail import show; show(eid, user)
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