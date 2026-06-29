"""EventLedger AI – Auth page (mode-aware)"""

import streamlit as st
from utils.helpers import authenticate, register_user
from utils.app_mode import get_app_mode, is_single_user


def show():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("## 📊 EventLedger AI")
        st.caption("Event Financial Lifecycle Management Platform")
        st.divider()

        mode = get_app_mode()

        tab_login, tab_reg = st.tabs(["🔑 Sign In", "📝 Create Account"])

        # ── Sign In ──────────────────────────────────────────────────────
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
                        st.error("❌ Invalid email or password.")

            if do_demo:
                user = authenticate("demo@eventledger.ai", "demo123")
                if user:
                    st.session_state.user = user
                    st.session_state.page = "dashboard"
                    st.rerun()

            # Show demo accounts based on mode
            st.divider()
            if is_single_user():
                st.caption("**Demo:** `demo@eventledger.ai` / `demo123`")
            else:
                st.caption("**Demo Accounts (Multi-User Mode):**")
                demos = [
                    ("👑 Super Admin",            "demo@eventledger.ai",  "demo123"),
                    ("🎯 Event Admin",             "rahul@eventledger.ai", "rahul123"),
                    ("💰 Finance Head",            "priya@eventledger.ai", "priya123"),
                    ("🏢 Dept Head (Marketing)",  "amit@eventledger.ai",  "amit123"),
                    ("🏢 Dept Head (Operations)", "neha@eventledger.ai",  "neha123"),
                ]
                for label, em, pw in demos:
                    st.caption(f"{label}: `{em}` / `{pw}`")

        # ── Create Account ───────────────────────────────────────────────
        with tab_reg:
            with st.form("register_form", clear_on_submit=False):
                r_name  = st.text_input("Full Name *",        placeholder="Alex Morgan")
                r_org   = st.text_input("Organization *",     placeholder="EventPro Inc.")
                r_email = st.text_input("Email *",            placeholder="you@company.com")
                r_pw    = st.text_input("Password *",         placeholder="Min 6 chars", type="password")
                r_pw2   = st.text_input("Confirm Password *", placeholder="Repeat password", type="password")
                do_reg  = st.form_submit_button("🚀 Create Account", use_container_width=True)

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
                        st.error("❌ Email already registered.")
                    else:
                        # Mark as super admin
                        from database.schema import get_connection
                        conn = get_connection()
                        conn.execute("UPDATE users SET is_super_admin=1 WHERE email=?",
                                     (r_email.strip().lower(),))
                        conn.commit()
                        conn.close()
                        user = authenticate(r_email.strip().lower(), r_pw)
                        if user:
                            st.session_state.user = user
                            st.session_state.page = "events"
                            st.rerun()
