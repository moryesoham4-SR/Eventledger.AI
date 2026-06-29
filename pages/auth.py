"""EventLedger AI – Auth page"""

import streamlit as st
from utils.helpers import authenticate, register_user
from utils.app_mode import get_app_mode, is_single_user


def show():

    # ── Boot animation (only on first ever load) ──────────────────────────────
    if "boot_done" not in st.session_state:
        st.session_state.boot_done = True
        st.markdown("""
<style>
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}
@keyframes expandLine {
    from { width: 0; }
    to   { width: 180px; }
}
@keyframes fadeOut {
    0%   { opacity: 1; }
    80%  { opacity: 1; }
    100% { opacity: 0; pointer-events: none; }
}
.boot-overlay {
    position: fixed;
    inset: 0;
    background: #060a12;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    animation: fadeOut 2.8s ease forwards;
}
.boot-logo {
    font-size: 48px;
    font-weight: 700;
    background: linear-gradient(135deg, #00d4ff, #7eb8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: fadeInUp 0.6s ease forwards;
    letter-spacing: -1px;
}
.boot-icon {
    font-size: 56px;
    animation: fadeInUp 0.3s ease forwards;
    margin-bottom: 16px;
}
.boot-tagline {
    font-size: 14px;
    color: #4a7fa8;
    margin-top: 8px;
    animation: fadeInUp 0.9s ease forwards;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-family: sans-serif;
}
.boot-line {
    height: 2px;
    background: linear-gradient(90deg, #00d4ff, #0055aa);
    border-radius: 1px;
    margin-top: 24px;
    animation: expandLine 1s ease 0.5s forwards;
    width: 0;
}
.boot-dots {
    margin-top: 32px;
    display: flex;
    gap: 8px;
    animation: fadeInUp 1.2s ease forwards;
}
.boot-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #00d4ff;
}
.boot-dot:nth-child(1) { animation: pulse 1s ease 0.8s infinite; }
.boot-dot:nth-child(2) { animation: pulse 1s ease 1.0s infinite; }
.boot-dot:nth-child(3) { animation: pulse 1s ease 1.2s infinite; }
</style>
<div class="boot-overlay">
    <div class="boot-icon">⚡</div>
    <div class="boot-logo">EventLedger AI</div>
    <div class="boot-tagline">Event Financial Intelligence</div>
    <div class="boot-line"></div>
    <div class="boot-dots">
        <div class="boot-dot"></div>
        <div class="boot-dot"></div>
        <div class="boot-dot"></div>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── Login form ────────────────────────────────────────────────────────────
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("""
<div style='text-align:center; padding: 2rem 0 1rem;'>
  <div style='font-size:36px; margin-bottom:8px;'>⚡</div>
  <div style='font-size:24px; font-weight:700; background: linear-gradient(135deg, #00d4ff, #7eb8ff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>EventLedger AI</div>
  <div style='font-size:12px; color:#4a7fa8; letter-spacing:2px; text-transform:uppercase;
    margin-top:4px;'>Event Financial Intelligence</div>
</div>
""", unsafe_allow_html=True)

        st.divider()

        mode = get_app_mode()
        tab_login, tab_reg = st.tabs(["Sign In", "Create Account"])

        # ── Sign In ───────────────────────────────────────────────────────
        with tab_login:
            with st.form("login_form"):
                email    = st.text_input("Email",    placeholder="you@company.com")
                password = st.text_input("Password", placeholder="••••••••", type="password")
                c1, c2   = st.columns(2)
                do_login = c1.form_submit_button("Sign In",  use_container_width=True)
                do_demo  = c2.form_submit_button("Use Demo", use_container_width=True)

            if do_login:
                if not email or not password:
                    st.error("Please enter email and password.")
                else:
                    user = authenticate(email.strip().lower(), password)
                    if user:
                        st.session_state.user = user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

            if do_demo:
                user = authenticate("demo@eventledger.ai", "demo123")
                if user:
                    st.session_state.user = user
                    st.session_state.page = "dashboard"
                    st.rerun()

            st.divider()
            if is_single_user():
                st.caption("**Demo:** `demo@eventledger.ai` / `demo123`")
            else:
                st.caption("**Demo Accounts:**")
                demos = [
                    ("Super Admin",    "demo@eventledger.ai",  "demo123"),
                    ("Event Admin",    "rahul@eventledger.ai", "rahul123"),
                    ("Finance Head",   "priya@eventledger.ai", "priya123"),
                    ("Dept Head (Mkt)","amit@eventledger.ai",  "amit123"),
                    ("Dept Head (Ops)","neha@eventledger.ai",  "neha123"),
                ]
                for label, em, pw in demos:
                    st.caption(f"{label}: `{em}` / `{pw}`")

        # ── Create Account ────────────────────────────────────────────────
        with tab_reg:
            with st.form("register_form", clear_on_submit=False):
                r_name  = st.text_input("Full Name *",        placeholder="Alex Morgan")
                r_org   = st.text_input("Organization *",     placeholder="EventPro Inc.")
                r_email = st.text_input("Email *",            placeholder="you@company.com")
                r_pw    = st.text_input("Password *",         placeholder="Min 6 chars", type="password")
                r_pw2   = st.text_input("Confirm Password *", placeholder="Repeat password", type="password")
                do_reg  = st.form_submit_button("Create Account", use_container_width=True)

            if do_reg:
                if not all([r_name.strip(), r_org.strip(), r_email.strip(), r_pw, r_pw2]):
                    st.error("All fields are required.")
                elif r_pw != r_pw2:
                    st.error("Passwords do not match.")
                elif len(r_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif "@" not in r_email:
                    st.error("Please enter a valid email.")
                else:
                    result = register_user(
                        r_name.strip(), r_email.strip().lower(),
                        r_pw, r_org.strip(), role="super_admin"
                    )
                    if result is False:
                        st.error("Email already registered.")
                    else:
                        from database.schema import get_connection
                        conn = get_connection()
                        conn.execute("UPDATE users SET is_super_admin=1 WHERE email=%s",
                                     (r_email.strip().lower(),))
                        conn.commit()
                        conn.close()
                        user = authenticate(r_email.strip().lower(), r_pw)
                        if user:
                            st.session_state.user = user
                            st.session_state.page = "events"
                            st.rerun()