"""
EventLedger AI – Email Notification Engine
Sends transactional emails via Gmail SMTP for key events:
budget submitted, approved, rejected, password reset, event created.

Fails silently (logs to console) if email sending breaks, so a
flaky SMTP connection never blocks the actual in-app action.
"""

import os
import smtplib
import ssl
import threading
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465


def _fire_and_forget(target, *args, **kwargs):
    """
    Runs an email-sending function in a background thread so the
    calling page action (approve/reject/submit/reset) returns
    immediately instead of waiting on Gmail's SMTP round-trip.
    """
    t = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    t.start()


def _get_credentials():
    """Reads Gmail sender credentials from env vars or Streamlit secrets."""
    sender = os.environ.get("GMAIL_SENDER", "")
    app_pw = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not sender or not app_pw:
        try:
            sender = st.secrets.get("GMAIL_SENDER", "")
            app_pw = st.secrets.get("GMAIL_APP_PASSWORD", "")
        except Exception:
            pass
    return sender, app_pw


def _smtp_send(sender: str, app_pw: str, to_email: str, subject: str, html_body: str):
    """The actual blocking SMTP call — meant to run inside a background thread."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"EventLedger AI <{sender}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, context=context) as server:
            server.login(sender, app_pw)
            server.sendmail(sender, to_email, msg.as_string())
    except Exception as e:
        print(f"[email_engine] Failed to send email to {to_email}: {e}")


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Reads credentials on the calling (main) thread, then dispatches
    the actual SMTP send to a background thread so the caller doesn't
    block waiting on Gmail's response.
    Returns True if a send was dispatched, False if credentials were missing.
    """
    sender, app_pw = _get_credentials()
    if not sender or not app_pw or not to_email:
        return False

    _fire_and_forget(_smtp_send, sender, app_pw, to_email, subject, html_body)
    return True


def _base_template(title: str, color: str, body_html: str) -> str:
    """Shared HTML wrapper so every email looks consistent."""
    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif; max-width:520px; margin:0 auto;
                background:#0a1422; border:1px solid #1a4060; border-radius:12px; overflow:hidden;">
      <div style="background:linear-gradient(135deg,#0d1f33,#091525); padding:24px; text-align:center;
                  border-bottom:1px solid #1a4060;">
        <div style="font-size:24px; font-weight:700; color:#00d4ff;">⚡ EventLedger AI</div>
      </div>
      <div style="padding:28px 24px;">
        <div style="display:inline-block; padding:6px 14px; border-radius:20px; font-size:12px;
                    font-weight:600; color:#fff; background:{color}; margin-bottom:16px;">
          {title}
        </div>
        {body_html}
      </div>
      <div style="padding:16px 24px; border-top:1px solid #1a4060; text-align:center;">
        <span style="font-size:11px; color:#4a7fa8;">
          This is an automated notification from EventLedger AI. Please do not reply to this email.
        </span>
      </div>
    </div>
    """


# ── Public email-sending functions ──────────────────────────────────────────

def send_budget_submitted_email(to_email: str, recipient_name: str, dept_name: str,
                                  amount: float, sym: str = "₹"):
    body = f"""
    <p style="color:#e2f0ff; font-size:15px;">Hi {recipient_name},</p>
    <p style="color:#a8c8e0; font-size:14px; line-height:1.6;">
      <strong style="color:#e2f0ff;">{dept_name}</strong> has submitted a new budget proposal
      of <strong style="color:#00d4ff;">{sym}{amount:,.0f}</strong> for your review.
    </p>
    <p style="color:#a8c8e0; font-size:14px;">Please log in to EventLedger AI to approve or reject it.</p>
    """
    html = _base_template("📤 BUDGET SUBMITTED", "#3378dd", body)
    return _send_email(to_email, f"New budget submitted by {dept_name}", html)


def send_budget_approved_email(to_email: str, recipient_name: str, dept_name: str,
                                 amount: float, sym: str = "₹"):
    body = f"""
    <p style="color:#e2f0ff; font-size:15px;">Hi {recipient_name},</p>
    <p style="color:#a8c8e0; font-size:14px; line-height:1.6;">
      Great news — your budget for <strong style="color:#e2f0ff;">{dept_name}</strong> totaling
      <strong style="color:#00e5a0;">{sym}{amount:,.0f}</strong> has been
      <strong style="color:#00e5a0;">approved</strong>. Funds are now released and ready to use.
    </p>
    """
    html = _base_template("✅ BUDGET APPROVED", "#00b87f", body)
    return _send_email(to_email, f"Your {dept_name} budget was approved 🎉", html)


def send_budget_rejected_email(to_email: str, recipient_name: str, dept_name: str,
                                 amount: float, reason: str, sym: str = "₹"):
    body = f"""
    <p style="color:#e2f0ff; font-size:15px;">Hi {recipient_name},</p>
    <p style="color:#a8c8e0; font-size:14px; line-height:1.6;">
      Your budget for <strong style="color:#e2f0ff;">{dept_name}</strong>
      ({sym}{amount:,.0f}) was <strong style="color:#ff7a7a;">not approved</strong> this time.
    </p>
    <div style="background:#1a0808; border:1px solid #ff5a5a44; border-radius:8px; padding:12px; margin-top:10px;">
      <span style="color:#ff9a9a; font-size:13px;"><strong>Reason:</strong> {reason}</span>
    </div>
    <p style="color:#a8c8e0; font-size:14px; margin-top:14px;">
      You can revise and resubmit it from EventLedger AI.
    </p>
    """
    html = _base_template("❌ BUDGET REJECTED", "#cc3a3a", body)
    return _send_email(to_email, f"Your {dept_name} budget needs revision", html)


def send_password_reset_email(to_email: str, recipient_name: str, new_password: str):
    body = f"""
    <p style="color:#e2f0ff; font-size:15px;">Hi {recipient_name},</p>
    <p style="color:#a8c8e0; font-size:14px; line-height:1.6;">
      Your EventLedger AI password has been reset by an administrator.
    </p>
    <div style="background:#0d1f33; border:1px solid #1a4060; border-radius:8px; padding:14px; margin:14px 0; text-align:center;">
      <span style="color:#7aa8cc; font-size:12px;">Your new temporary password:</span><br/>
      <span style="color:#00d4ff; font-size:18px; font-weight:700; letter-spacing:1px;">{new_password}</span>
    </div>
    <p style="color:#a8c8e0; font-size:13px;">
      Please log in and change this password as soon as possible from Settings.
    </p>
    """
    html = _base_template("🔒 PASSWORD RESET", "#7eb8ff", body)
    return _send_email(to_email, "Your EventLedger AI password was reset", html)


def send_event_created_email(to_email: str, recipient_name: str, event_name: str,
                               venue: str = "", start_date: str = ""):
    body = f"""
    <p style="color:#e2f0ff; font-size:15px;">Hi {recipient_name},</p>
    <p style="color:#a8c8e0; font-size:14px; line-height:1.6;">
      A new event <strong style="color:#00d4ff;">'{event_name}'</strong> has been created
      and you've been added to it.
    </p>
    <table style="width:100%; margin-top:12px; font-size:13px; color:#a8c8e0;">
      <tr><td style="padding:4px 0;">📍 Venue</td><td style="text-align:right; color:#e2f0ff;">{venue or '—'}</td></tr>
      <tr><td style="padding:4px 0;">📆 Start Date</td><td style="text-align:right; color:#e2f0ff;">{start_date or '—'}</td></tr>
    </table>
    <p style="color:#a8c8e0; font-size:14px; margin-top:14px;">Log in to EventLedger AI to start planning.</p>
    """
    html = _base_template("🚀 EVENT CREATED", "#00d4ff", body)
    return _send_email(to_email, f"You've been added to '{event_name}'", html)