"""EventLedger AI – UI Components (mode-aware sidebar)"""

import streamlit as st
from utils.app_mode import is_single_user
from utils.roles import (
    get_primary_role, unread_count,
    ROLE_ICONS, ROLE_COLORS, ROLES
)


def render_sidebar(user):
    if is_single_user():
        _sidebar_single(user)
    else:
        _sidebar_multi(user)


def _sidebar_single(user):
    """Simple sidebar for single-user mode — full access, no role restrictions."""
    with st.sidebar:
        st.markdown("## 📊 EventLedger AI")
        st.caption(f"👤 {user['name']}")
        st.caption("🟢 **Single User Mode**")
        st.divider()

        nav = [
            ("dashboard",   "🏠", "Dashboard"),
            ("events",      "📅", "Events"),
            ("finance",     "💰", "Finance"),
            ("sponsors",    "🤝", "Sponsors"),
            ("vendors",     "🚚", "Vendors"),
            ("analytics",   "📈", "Analytics"),
            ("ai_insights", "🤖", "AI Insights"),
            ("reports",     "📄", "Reports"),
            ("archive",     "📦", "Archive"),
            ("settings",    "⚙️", "Settings"),
        ]
        for page, icon, label in nav:
            if st.button(f"{icon}  {label}", key=f"nav_{page}",
                         use_container_width=True):
                st.session_state.page = page
                st.session_state.active_event = None
                st.rerun()

        st.divider()
        if st.button("🚪  Sign Out", key="logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


@st.fragment(run_every=8)
def _live_notification_badge(uid):
    """
    Polls every 8 seconds for new unread notifications.
    Only this small fragment re-runs (not the whole page/app),
    so it feels like a live WhatsApp/Instagram-style badge
    without disrupting whatever the user is doing.
    """
    notifs = unread_count(uid)

    prev_key = f"_prev_notif_count_{uid}"
    prev = st.session_state.get(prev_key, notifs)

    if notifs > prev:
        # New notification(s) arrived since last poll
        new_count = notifs - prev
        st.toast(f"🔔 You have {new_count} new notification{'s' if new_count>1 else ''}!", icon="🔔")

    st.session_state[prev_key] = notifs

    if notifs > 0:
        st.warning(f"🔔 {notifs} unread notification{'s' if notifs>1 else ''}")
    else:
        st.caption("🔕 No new notifications")


def _sidebar_multi(user):
    """Full role-based sidebar for multi-user mode."""
    uid    = user["id"]
    role   = get_primary_role(uid)
    icon   = ROLE_ICONS.get(role, "👤")

    with st.sidebar:
        st.markdown("## 📊 EventLedger AI")
        st.caption(f"{icon} **{user['name']}**")
        st.caption(f"🔵 **Multi User Mode** · {ROLES.get(role, role)}")
        _live_notification_badge(uid)
        st.divider()

        is_sa  = bool(user.get("is_super_admin"))
        is_ea  = role in ("super_admin", "event_admin")
        is_fin = role in ("super_admin", "finance_head")

        st.markdown("**Main**")
        for page, icon_s, label in [
            ("dashboard", "🏠", "Dashboard"),
            ("events",    "📅", "Events"),
        ]:
            if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                st.session_state.page = page
                st.session_state.active_event = None; st.rerun()

        if is_fin:
            st.markdown("**Finance**")
            for page, icon_s, label in [
                ("finance",   "💰", "Finance"),
                ("approvals", "📋", "Pending Approvals"),
            ]:
                if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.session_state.active_event = None; st.rerun()

        if is_ea:
            for page, icon_s, label in [
                ("sponsors", "🤝", "Sponsors"),
                ("vendors",  "🚚", "Vendors"),
            ]:
                if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.session_state.active_event = None; st.rerun()

        st.markdown("**Insights**")
        for page, icon_s, label in [
            ("analytics",   "📈", "Analytics"),
            ("ai_insights", "🤖", "AI Insights"),
            ("reports",     "📄", "Reports"),
        ]:
            if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                st.session_state.page = page
                st.session_state.active_event = None; st.rerun()

        if is_sa:
            st.markdown("**Admin**")
            for page, icon_s, label in [
                ("user_management", "👥", "User Management"),
                ("archive",         "📦", "Archive"),
                ("audit_log",       "🔍", "Audit Log"),
            ]:
                if st.button(f"{icon_s}  {label}", key=f"nav_{page}", use_container_width=True):
                    st.session_state.page = page
                    st.session_state.active_event = None; st.rerun()

        if st.button("🔔  Notifications", key="nav_notifs", use_container_width=True):
            st.session_state.page = "notifications"
            st.session_state.active_event = None; st.rerun()

        st.markdown("**System**")
        if st.button("⚙️  Settings", key="nav_settings", use_container_width=True):
            st.session_state.page = "settings"
            st.session_state.active_event = None; st.rerun()

        st.divider()
        if st.button("🚪  Sign Out", key="logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ── Shared helpers ──────────────────────────────────────────────────────────

def section_header(title, icon=""):
    st.markdown(f"### {icon} {title}" if icon else f"### {title}")


def empty_state(icon, message, hint=""):
    st.info(f"{icon} **{message}**" + (f"\n\n{hint}" if hint else ""))


def celebrate_success(title: str, subtitle: str = "", height: int = 230):
    """
    Confetti-burst celebration banner — used for big wins like
    budget approvals, milestones, or event completions.
    """
    _animated_banner(title, subtitle, height, kind="confetti")


def celebrate_launch(title: str, subtitle: str = "", height: int = 230):
    """Rocket launch animation — used when a new event is created."""
    _animated_banner(title, subtitle, height, kind="launch")


def celebrate_sent(title: str, subtitle: str = "", height: int = 210):
    """Paper-plane send animation — used when a budget is submitted for review."""
    _animated_banner(title, subtitle, height, kind="sent")


def shake_warning(title: str, subtitle: str = "", height: int = 210):
    """Gentle shake + soft red glow — used when a budget is rejected."""
    _animated_banner(title, subtitle, height, kind="shake")


def _animated_banner(title: str, subtitle: str, height: int, kind: str):
    import streamlit.components.v1 as components
    safe_title = title.replace('"', '&quot;')
    safe_sub   = subtitle.replace('"', '&quot;')

    if kind == "confetti":
        icon_html = '<span style="font-size:28px; color:#060a12; font-weight:700;">✓</span>'
        circle_bg = "linear-gradient(135deg,#00e5a0,#00b87f)"
        circle_glow = "#00e5a055"
        extra_anim = ""
        body_anim = ""
    elif kind == "launch":
        icon_html = '<span style="font-size:26px;">🚀</span>'
        circle_bg = "linear-gradient(135deg,#00d4ff,#0088cc)"
        circle_glow = "#00d4ff55"
        extra_anim = "animation: launch-up 1.1s cubic-bezier(.34,1.2,.4,1) 0.15s both;"
        body_anim = ""
    elif kind == "sent":
        icon_html = '<span style="font-size:24px;">📤</span>'
        circle_bg = "linear-gradient(135deg,#7eb8ff,#3378dd)"
        circle_glow = "#3378dd55"
        extra_anim = "animation: sent-fly 0.9s cubic-bezier(.34,1.2,.4,1) 0.1s both;"
        body_anim = ""
    else:  # shake
        icon_html = '<span style="font-size:26px;">⚠️</span>'
        circle_bg = "linear-gradient(135deg,#ff7a7a,#cc3a3a)"
        circle_glow = "#ff5a5a55"
        extra_anim = ""
        body_anim = "animation: gentle-shake 0.5s ease 0.1s both;"

    confetti_canvas = '<canvas id="confetti-canvas" style="position:absolute; inset:0; width:100%; height:100%; pointer-events:none;"></canvas>' if kind == "confetti" else ""
    confetti_script = _confetti_js() if kind == "confetti" else ""

    components.html(f"""
<style>
@keyframes launch-up {{
  0%   {{ transform: translateY(40px) scale(0.5) rotate(0deg); opacity:0; }}
  60%  {{ transform: translateY(-6px) scale(1.1) rotate(-8deg); opacity:1; }}
  100% {{ transform: translateY(0) scale(1) rotate(0deg); opacity:1; }}
}}
@keyframes sent-fly {{
  0%   {{ transform: translateX(-30px) translateY(10px) rotate(-20deg) scale(0.6); opacity:0; }}
  60%  {{ transform: translateX(4px) translateY(-4px) rotate(5deg) scale(1.08); opacity:1; }}
  100% {{ transform: translateX(0) translateY(0) rotate(0deg) scale(1); opacity:1; }}
}}
@keyframes gentle-shake {{
  0%, 100% {{ transform: translateX(0); }}
  20% {{ transform: translateX(-6px); }}
  40% {{ transform: translateX(5px); }}
  60% {{ transform: translateX(-3px); }}
  80% {{ transform: translateX(2px); }}
}}
</style>
<div style="position:relative; background:linear-gradient(135deg, #0d1f33, #091525);
    border:0.5px solid #1a4060; border-radius:12px; padding:1.75rem 1rem; text-align:center;
    overflow:hidden; min-height:{height-20}px; display:flex; flex-direction:column;
    align-items:center; justify-content:center; font-family:'Inter',sans-serif; {body_anim}">
  {confetti_canvas}
  <div id="icon-circle" style="width:56px; height:56px; border-radius:50%;
      background:{circle_bg}; display:flex; align-items:center;
      justify-content:center; margin-bottom:0.9rem; box-shadow:0 0 20px {circle_glow}; {extra_anim}">
    {icon_html}
  </div>
  <p style="font-size:17px; font-weight:600; margin:0 0 4px; color:#e2f0ff;
      opacity:0; transform:translateY(8px); transition:all 0.4s ease 0.3s;" id="title-text">{safe_title}</p>
  <p style="font-size:13px; color:#7aa8cc; margin:0; opacity:0; transform:translateY(8px);
      transition:all 0.4s ease 0.45s;" id="sub-text">{safe_sub}</p>
</div>
<script>
{confetti_script}
setTimeout(()=>{{
  document.getElementById('title-text').style.opacity = '1';
  document.getElementById('title-text').style.transform = 'translateY(0)';
}}, 280);
setTimeout(()=>{{
  document.getElementById('sub-text').style.opacity = '1';
  document.getElementById('sub-text').style.transform = 'translateY(0)';
}}, 420);
</script>
""", height=height)


def _confetti_js():
    return """
(function(){
  const canvas = document.getElementById('confetti-canvas');
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const colors = ['#00d4ff','#00e5a0','#7eb8ff','#ffaa00','#ff7eb8'];
  let particles = [];
  for(let i=0;i<70;i++){
    particles.push({
      x: rect.width/2, y: rect.height/2,
      vx: (Math.random()-0.5)*9, vy: (Math.random()-1.3)*9,
      size: Math.random()*5+3, color: colors[Math.floor(Math.random()*colors.length)],
      rot: Math.random()*360, vr: (Math.random()-0.5)*14, life: 1
    });
  }
  function frame(){
    ctx.clearRect(0,0,rect.width,rect.height);
    let alive = false;
    particles.forEach(p=>{
      p.vy += 0.22; p.x += p.vx; p.y += p.vy; p.rot += p.vr; p.life -= 0.012;
      if(p.life > 0){
        alive = true;
        ctx.save();
        ctx.globalAlpha = Math.max(p.life,0);
        ctx.translate(p.x,p.y);
        ctx.rotate(p.rot * Math.PI/180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size/2,-p.size/2,p.size,p.size*0.6);
        ctx.restore();
      }
    });
    if(alive) requestAnimationFrame(frame);
  }
  frame();
})();
"""


def fmt_currency(amount, symbol="₹"):
    if abs(amount) >= 10_000_000:
        return f"{symbol}{amount/10_000_000:.2f} Cr"
    if abs(amount) >= 100_000:
        return f"{symbol}{amount/100_000:.2f} L"
    if abs(amount) >= 1_000:
        return f"{symbol}{amount/1_000:.1f}K"
    return f"{symbol}{amount:,.0f}"


def role_badge(role: str) -> str:
    from utils.roles import ROLE_ICONS, ROLES
    return f"{ROLE_ICONS.get(role,'👤')} {ROLES.get(role, role)}"