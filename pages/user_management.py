"""EventLedger AI – User Management (Super Admin only)"""

import streamlit as st
import pandas as pd
from utils.roles import (
    get_all_users, create_user, reset_password,
    assign_role, revoke_role, get_event_role_assignments,
    get_accessible_events, ROLES, ROLE_ICONS, log_action
)
from utils.helpers import get_events, get_departments, add_department
from database.schema import get_connection
from components.ui import section_header, empty_state

def _fmt_date(val, default="—"):
    """Safely format a date/datetime/string to YYYY-MM-DD."""
    if val is None:
        return default
    import datetime
    if isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()[:10]
    return str(val)[:10] if val else default



def show(user):
    if not user.get("is_super_admin"):
        st.error("🔒 Access denied. Super Admin only.")
        return

    st.title("👥 User Management")
    st.caption("Create users, assign roles, manage departments")
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 All Users",
        "➕ Create User",
        "🎭 Assign Roles",
        "🏢 Departments",
    ])

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 1 — ALL USERS
    # ══════════════════════════════════════════════════════════════════════
    with tab1:
        section_header("All Users", "👥")
        users = get_all_users()
        if not users:
            empty_state("👥","No users yet")
        else:
            rows = []
            for u in users:
                conn     = get_connection()
                ev_roles = conn.execute(
                    "SELECT DISTINCT role FROM user_event_roles WHERE user_id=?",
                    (u["id"],)
                ).fetchall()
                conn.close()
                base  = "super_admin" if u.get("is_super_admin") else u.get("role","member")
                extra = [r["role"] for r in ev_roles if r["role"] != base]
                rows.append({
                    "Name":        u["name"],
                    "Email":       u["email"],
                    "Base Role":   f"{ROLE_ICONS.get(base,'')} {ROLES.get(base,base)}",
                    "Event Roles": ", ".join(ROLES.get(r,r) for r in extra) or "—",
                    "Active":      "✅" if u.get("is_active",1) else "❌",
                    "Joined":      _fmt_date(u.get("created_at")),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.divider()
        section_header("Reset Password", "🔒")
        users_excl = [u for u in users if u["id"] != user["id"]]
        if users_excl:
            with st.form("reset_pw_form", clear_on_submit=True):
                sel_email = st.selectbox("Select User",
                    [f"{u['name']} ({u['email']})" for u in users_excl])
                new_pw    = st.text_input("New Password", type="password",
                                           placeholder="Min 6 chars")
                if st.form_submit_button("🔐 Reset Password", use_container_width=True):
                    if len(new_pw) >= 6:
                        idx    = [f"{u['name']} ({u['email']})" for u in users_excl].index(sel_email)
                        target = users_excl[idx]
                        reset_password(target["id"], new_pw)
                        log_action(user["id"],"RESET_PASSWORD","users",target["id"],
                                   details=f"Reset password for {target['name']}")
                        st.success(f"✅ Password reset for **{target['name']}**")
                    else:
                        st.error("Password must be at least 6 characters.")

        st.divider()
        section_header("Toggle Active Status", "🔄")
        if users_excl:
            with st.form("toggle_form", clear_on_submit=True):
                sel_tgl = st.selectbox("Select User",
                    [f"{u['name']} — {'Active' if u.get('is_active',1) else 'Inactive'}"
                     for u in users_excl], key="tgl_sel")
                if st.form_submit_button("Toggle Active/Inactive", use_container_width=True):
                    idx    = [f"{u['name']} — {'Active' if u.get('is_active',1) else 'Inactive'}"
                              for u in users_excl].index(sel_tgl)
                    target = users_excl[idx]
                    new_s  = 0 if target.get("is_active",1) else 1
                    conn   = get_connection()
                    conn.execute("UPDATE users SET is_active=? WHERE id=?", (new_s, target["id"]))
                    conn.commit(); conn.close()
                    st.success(f"User **{target['name']}** {'activated' if new_s else 'deactivated'}")
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 2 — CREATE USER
    # ══════════════════════════════════════════════════════════════════════
    with tab2:
        section_header("Create New User & Assign to Event", "➕")
        st.caption("Create a user and optionally assign them directly to an event with a role.")

        events   = get_events(user["id"])
        ev_names = ["— No event assignment —"] + [e["name"] for e in events]
        ev_map   = {e["name"]: e for e in events}

        with st.form("create_user_form", clear_on_submit=True):
            st.markdown("**User Details**")
            c1, c2 = st.columns(2)
            u_name  = c1.text_input("Full Name *",   placeholder="Rahul Sharma")
            u_email = c2.text_input("Email *",        placeholder="rahul@org.com")
            c3, c4  = st.columns(2)
            u_pw    = c3.text_input("Password *",     placeholder="Min 6 chars", type="password")
            u_org   = c4.text_input("Organization",   value=user.get("org_name",""))

            st.markdown("**Event Assignment (optional)**")
            sel_ev_name = st.selectbox("Assign to Event", ev_names)
            sel_ev_obj  = ev_map.get(sel_ev_name)

            # Role selector — shown always, used only if event is selected
            role_keys  = ["event_admin","finance_head","dept_head","member"]
            role_labels= [f"{ROLE_ICONS.get(r,'')} {ROLES.get(r,r)}" for r in role_keys]
            sel_role_idx= st.selectbox("Role in Event",
                options=list(range(len(role_keys))),
                format_func=lambda i: role_labels[i])
            sel_role = role_keys[sel_role_idx]

            sel_dept_id = None
            if sel_ev_obj:
                depts = get_departments(sel_ev_obj["id"])
                if sel_role == "dept_head" and depts:
                    dept_opts  = {d["name"]: d["id"] for d in depts}
                    sel_d_name = st.selectbox("Department (for Dept Head)",
                                               list(dept_opts.keys()))
                    sel_dept_id = dept_opts[sel_d_name]
                elif sel_role == "dept_head":
                    st.warning("⚠️ No departments in this event yet. Create departments first.")

            submitted = st.form_submit_button("➕ Create User", use_container_width=True)

        if submitted:
            if not all([u_name.strip(), u_email.strip(), u_pw]):
                st.error("Name, email and password are required.")
            elif len(u_pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif "@" not in u_email:
                st.error("Enter a valid email.")
            else:
                new_u = create_user(u_name.strip(), u_email.strip().lower(),
                                    u_pw, u_org.strip(), base_role=sel_role)
                if new_u:
                    # Assign to event if selected
                    if sel_ev_obj:
                        assign_role(new_u["id"], sel_ev_obj["id"],
                                    sel_role, sel_dept_id, user["id"])
                        conn = get_connection()
                        conn.execute("UPDATE users SET role=? WHERE id=?",
                                     (sel_role, new_u["id"]))
                        conn.commit(); conn.close()
                        log_action(user["id"],"CREATE_USER","users",new_u["id"],
                                   sel_ev_obj["id"],
                                   f"Created {u_name} as {sel_role} for {sel_ev_obj['name']}")
                        st.success(
                            f"✅ User **{u_name}** created and assigned as "
                            f"**{ROLES.get(sel_role,sel_role)}** to **{sel_ev_obj['name']}**"
                        )
                    else:
                        log_action(user["id"],"CREATE_USER","users",new_u["id"],
                                   details=f"Created user {u_name}")
                        st.success(f"✅ User **{u_name}** created.")
                    st.info(f"Login: `{u_email}` / `{u_pw}`")
                    st.rerun()
                else:
                    st.error("❌ Email already in use.")

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 3 — ASSIGN ROLES
    # ══════════════════════════════════════════════════════════════════════
    with tab3:
        section_header("Assign Event Roles", "🎭")
        st.caption("Assign or revoke roles for existing users on specific events.")

        events = get_events(user["id"])
        if not events:
            st.warning("Create an event first."); return

        ev_map2 = {e["name"]: e for e in events}
        sel_ev2 = st.selectbox("Select Event", list(ev_map2.keys()), key="role_ev_sel")
        ev2     = ev_map2[sel_ev2]

        assignments = get_event_role_assignments(ev2["id"])
        if assignments:
            st.markdown("**Current Assignments:**")
            rows = [{
                "User":       a["user_name"],
                "Email":      a["email"],
                "Role":       f"{ROLE_ICONS.get(a['role'],'')} {ROLES.get(a['role'],a['role'])}",
                "Department": a.get("dept_name") or "—",
            } for a in assignments]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No roles assigned yet for this event.")

        st.divider()
        st.markdown("**➕ Assign New Role:**")

        depts2    = get_departments(ev2["id"])
        all_users = get_all_users()

        # ── IMPORTANT: use session state so values survive form submission ──
        # Store selections outside form to avoid Streamlit re-render issue
        col_u, col_r = st.columns(2)
        user_opts  = [f"{u['name']} ({u['email']})" for u in all_users]
        sel_u_str  = col_u.selectbox("Select User", user_opts, key="ar_user")

        role_keys2  = ["event_admin","finance_head","dept_head","member"]
        role_labels2= [f"{ROLE_ICONS.get(r,'')} {ROLES.get(r,r)}" for r in role_keys2]
        sel_r_idx   = col_r.selectbox("Select Role",
            options=list(range(len(role_keys2))),
            format_func=lambda i: role_labels2[i],
            key="ar_role")
        sel_r = role_keys2[sel_r_idx]

        sel_d2 = None
        if sel_r == "dept_head":
            if depts2:
                dept_opts2  = {d["name"]: d["id"] for d in depts2}
                sel_d_name2 = st.selectbox("Select Department",
                    list(dept_opts2.keys()), key="ar_dept")
                sel_d2 = dept_opts2[sel_d_name2]
            else:
                st.warning("⚠️ No departments in this event. Create one in the Departments tab first.")

        if st.button("✅ Assign Role", key="do_assign_btn", use_container_width=True):
            idx2     = user_opts.index(sel_u_str)
            target_u = all_users[idx2]
            if sel_r == "dept_head" and not sel_d2:
                st.error("Select a department for Dept Head role.")
            else:
                ok = assign_role(target_u["id"], ev2["id"], sel_r, sel_d2, user["id"])
                if ok:
                    conn = get_connection()
                    conn.execute("UPDATE users SET role=? WHERE id=?",
                                 (sel_r, target_u["id"]))
                    conn.commit(); conn.close()
                    log_action(user["id"],"ASSIGN_ROLE","user_event_roles",target_u["id"],
                               ev2["id"], f"Assigned {sel_r} to {target_u['name']}")
                    st.success(
                        f"✅ **{target_u['name']}** → "
                        f"**{ROLES.get(sel_r,sel_r)}**"
                        + (f" ({depts2[[d['id'] for d in depts2].index(sel_d2)]['name']})"
                           if sel_d2 and depts2 else "")
                    )
                    st.rerun()
                else:
                    st.warning("Role already assigned or conflict.")

        st.divider()
        st.markdown("**🗑 Revoke a Role:**")
        if assignments:
            rev_opts = [
                f"{a['user_name']} — {ROLES.get(a['role'],a['role'])}"
                + (f" ({a['dept_name']})" if a.get("dept_name") else "")
                for a in assignments
            ]
            sel_rev = st.selectbox("Select assignment to revoke", rev_opts, key="rev_sel")
            if st.button("🗑 Revoke Role", key="do_revoke_btn", type="secondary"):
                idx_r = rev_opts.index(sel_rev)
                a_rev = assignments[idx_r]
                revoke_role(a_rev["user_id"], ev2["id"], a_rev["role"],
                            a_rev.get("dept_id"))
                st.success("Role revoked.")
                st.rerun()
        else:
            st.caption("Nothing to revoke.")

    # ══════════════════════════════════════════════════════════════════════
    #  TAB 4 — DEPARTMENTS (with inline user creation)
    # ══════════════════════════════════════════════════════════════════════
    with tab4:
        section_header("Manage Departments", "🏢")
        st.caption("Create departments and optionally assign a head user in one step.")

        events3 = get_events(user["id"])
        if not events3:
            st.warning("Create an event first."); return

        ev_map3  = {e["name"]: e for e in events3}
        sel_ev3  = st.selectbox("Select Event", list(ev_map3.keys()), key="dept_ev_sel")
        ev3      = ev_map3[sel_ev3]
        depts3   = get_departments(ev3["id"])

        # Current departments
        if depts3:
            st.markdown("**Existing Departments:**")
            df_d = pd.DataFrame([{
                "Department": d["name"],
                "Head":       d.get("head_name") or "—",
                "Manager":    d.get("manager") or "—",
            } for d in depts3])
            st.dataframe(df_d, use_container_width=True, hide_index=True)
        else:
            st.info("No departments yet for this event.")

        st.divider()
        st.markdown("**➕ Add Department:**")
        st.caption("You can also create the department head's user account right here.")

        with st.form("add_dept_full_form", clear_on_submit=True):
            st.markdown("**Department Info**")
            c1, c2, c3 = st.columns(3)
            d_name  = c1.text_input("Department Name *", placeholder="e.g. Logistics")
            d_head  = c2.text_input("Head Person Name",  placeholder="e.g. Ravi Kumar")
            d_mgr   = c3.text_input("Manager Name",      placeholder="e.g. Priya Shah")

            st.markdown("**Create Head User Account** *(optional — leave email blank to skip)*")
            st.caption("If you fill this in, a user account will be created and assigned as Dept Head automatically.")
            c4, c5, c6 = st.columns(3)
            hu_email = c4.text_input("Head's Email",    placeholder="ravi@org.com")
            hu_pw    = c5.text_input("Head's Password", placeholder="Min 6 chars", type="password")
            hu_org   = c6.text_input("Organization",    value=user.get("org_name",""))

            submitted3 = st.form_submit_button("🏢 Add Department", use_container_width=True)

        if submitted3:
            if not d_name.strip():
                st.error("Department name is required.")
            else:
                # 1. Create department
                add_department(ev3["id"], d_name.strip(), d_head.strip(), d_mgr.strip(), "#6366f1")

                # 2. Get the new dept id
                conn = get_connection()
                new_dept = conn.execute(
                    "SELECT id FROM departments WHERE event_id=? AND name=? ORDER BY id DESC LIMIT 1",
                    (ev3["id"], d_name.strip())
                ).fetchone()
                conn.close()
                new_dept_id = new_dept["id"] if new_dept else None

                # 3. Optionally create user and assign
                if hu_email.strip() and hu_pw and new_dept_id:
                    if len(hu_pw) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif "@" not in hu_email:
                        st.error("Enter a valid email for the head user.")
                    else:
                        head_name = d_head.strip() or "Department Head"
                        new_u     = create_user(head_name, hu_email.strip().lower(),
                                                hu_pw, hu_org.strip(), base_role="dept_head")
                        if new_u:
                            assign_role(new_u["id"], ev3["id"], "dept_head",
                                        new_dept_id, user["id"])
                            conn2 = get_connection()
                            conn2.execute("UPDATE users SET role='dept_head' WHERE id=?",
                                          (new_u["id"],))
                            conn2.commit(); conn2.close()
                            log_action(user["id"],"CREATE_USER","users",new_u["id"],
                                       ev3["id"],
                                       f"Created dept head {head_name} for {d_name}")
                            st.success(
                                f"✅ Department **{d_name}** created!\n\n"
                                f"👤 User **{head_name}** created and assigned as Dept Head.\n\n"
                                f"Login: `{hu_email}` / `{hu_pw}`"
                            )
                        else:
                            st.warning(f"⚠️ Department created but email **{hu_email}** is already in use. "
                                       "Assign the existing user from the Assign Roles tab.")
                else:
                    st.success(f"✅ Department **{d_name}** created!")

                log_action(user["id"],"CREATE_DEPT","departments",new_dept_id,
                           ev3["id"], f"Created department: {d_name}")
                st.rerun()

        # Delete dept
        if depts3:
            st.divider()
            with st.form("del_dept_form", clear_on_submit=True):
                st.markdown("**🗑 Delete Department:**")
                del_opts = [d["name"] for d in depts3]
                sel_del  = st.selectbox("Select", del_opts, key="del_dept_sel")
                if st.form_submit_button("Delete", type="secondary", use_container_width=False):
                    from utils.roles import get_connection as gc
                    conn = get_connection()
                    did = next(d["id"] for d in depts3 if d["name"]==sel_del)
                    conn.execute("DELETE FROM departments WHERE id=?", (did,))
                    conn.commit(); conn.close()
                    st.success(f"Deleted department: {sel_del}")
                    st.rerun()