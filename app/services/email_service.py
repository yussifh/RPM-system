"""
email_service.py
-----------------
SMTP email notification service for alerts, appointments, and emergency contacts.
Configured via .env variables. Falls back to logging when SMTP is not configured.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Lightweight email service using Python's smtplib."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("SMTP_FROM_NAME", "RPM System")
        self.enabled = bool(self.smtp_host and self.smtp_user)

    def _send_email(self, to_email: str, subject: str, html_body: str,
                    text_body: str = None) -> bool:
        """
        Sends an email via SMTP. Returns True on success, False on failure.
        Logs instead of sending when SMTP is not configured.
        """
        if not self.enabled:
            logger.info(f"[EMAIL STUB] To: {to_email} | Subject: {subject}")
            logger.info(f"[EMAIL STUB] Body preview: {(text_body or html_body)[:200]}")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.ehlo()
                if self.smtp_port != 25:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_alert_notification(self, to_email: str, patient_name: str,
                                 severity: str, message: str,
                                 doctor_name: str = "") -> bool:
        """Sends a clinical alert notification email."""
        color = {"critical": "#C73E3A", "high": "#B8761D", "medium": "#2A6A9B", "low": "#0E7A5C"}.get(severity, "#5F717A")
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:{color};color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
                <h2 style="margin:0;font-size:18px;">RPM Alert: {severity.upper()}</h2>
            </div>
            <div style="background:white;border:1px solid #DCE5E1;padding:20px;border-radius:0 0 8px 8px;">
                <p style="font-size:14px;color:#16242B;">Dear {doctor_name or 'Doctor'},</p>
                <p style="font-size:14px;color:#5F717A;">
                    A <strong style="color:{color};">{severity.upper()}</strong> alert has been triggered for patient
                    <strong>{patient_name}</strong>.
                </p>
                <div style="background:#F1F5F3;padding:12px;border-radius:6px;margin:12px 0;">
                    <p style="font-size:13px;color:#16242B;margin:0;">{message}</p>
                </div>
                <p style="font-size:12px;color:#5F717A;margin-top:16px;">
                    Please log in to the RPM System to review and take action.
                </p>
                <hr style="border:none;border-top:1px solid #DCE5E1;margin:16px 0;">
                <p style="font-size:11px;color:#999;">
                    RPM System - AI-Integrated Remote Patient Monitoring | Academic Demo Only
                </p>
            </div>
        </div>
        """
        text = f"RPM Alert: {severity.upper()}\nPatient: {patient_name}\n\n{message}\n\nPlease log in to review."
        return self._send_email(to_email, f"[RPM] {severity.upper()} Alert — {patient_name}", html, text)

    def send_appointment_notification(self, to_email: str, patient_name: str,
                                       doctor_name: str, appointment_date: str,
                                       appointment_time: str, location: str,
                                       notification_type: str = "reminder") -> bool:
        """Sends an appointment notification email."""
        action = "Reminder" if notification_type == "reminder" else "Scheduled"
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#0E7A5C;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
                <h2 style="margin:0;font-size:18px;">Appointment {action}</h2>
            </div>
            <div style="background:white;border:1px solid #DCE5E1;padding:20px;border-radius:0 0 8px 8px;">
                <p style="font-size:14px;color:#16242B;">Dear {patient_name},</p>
                <p style="font-size:14px;color:#5F717A;">
                    You have an appointment {notification_type}:
                </p>
                <div style="background:#F1F5F3;padding:16px;border-radius:6px;margin:12px 0;">
                    <table style="width:100%;font-size:13px;">
                        <tr><td style="padding:4px 0;font-weight:bold;color:#555;">Doctor:</td><td>Dr. {doctor_name}</td></tr>
                        <tr><td style="padding:4px 0;font-weight:bold;color:#555;">Date:</td><td>{appointment_date}</td></tr>
                        <tr><td style="padding:4px 0;font-weight:bold;color:#555;">Time:</td><td>{appointment_time}</td></tr>
                        <tr><td style="padding:4px 0;font-weight:bold;color:#555;">Location:</td><td>{location}</td></tr>
                    </table>
                </div>
                <hr style="border:none;border-top:1px solid #DCE5E1;margin:16px 0;">
                <p style="font-size:11px;color:#999;">
                    RPM System - AI-Integrated Remote Patient Monitoring | Academic Demo Only
                </p>
            </div>
        </div>
        """
        text = f"Appointment {action}\nDoctor: Dr. {doctor_name}\nDate: {appointment_date}\nTime: {appointment_time}\nLocation: {location}"
        return self._send_email(to_email, f"[RPM] Appointment {action} — {appointment_date}", html, text)

    def send_emergency_notification(self, to_email: str, patient_name: str,
                                     severity: str, message: str,
                                     vital_snapshot: str = "") -> bool:
        """Sends an emergency contact notification email."""
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#C73E3A;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
                <h2 style="margin:0;font-size:18px;">EMERGENCY: {patient_name}</h2>
            </div>
            <div style="background:white;border:1px solid #DCE5E1;padding:20px;border-radius:0 0 8px 8px;">
                <p style="font-size:14px;color:#16242B;">Emergency Contact Notification</p>
                <p style="font-size:14px;color:#5F717A;">
                    Patient <strong>{patient_name}</strong> has a
                    <strong style="color:#C73E3A;">{severity.upper()}</strong> health alert.
                </p>
                <div style="background:#FBE9E7;padding:12px;border-radius:6px;margin:12px 0;border-left:4px solid #C73E3A;">
                    <p style="font-size:13px;color:#16242B;margin:0;">{message}</p>
                </div>
                {"<p style='font-size:13px;color:#5F717A;'><strong>Vitals:</strong> " + vital_snapshot + "</p>" if vital_snapshot else ""}
                <p style="font-size:12px;color:#C73E3A;font-weight:bold;margin-top:16px;">
                    Please contact the patient immediately or call emergency services if needed.
                </p>
                <hr style="border:none;border-top:1px solid #DCE5E1;margin:16px 0;">
                <p style="font-size:11px;color:#999;">
                    RPM System - AI-Integrated Remote Patient Monitoring | Academic Demo Only
                </p>
            </div>
        </div>
        """
        text = f"EMERGENCY: {patient_name}\nSeverity: {severity}\n\n{message}\n\nVitals: {vital_snapshot}\n\nPlease contact the patient immediately."
        return self._send_email(to_email, f"[RPM EMERGENCY] {severity.upper()} — {patient_name}", html, text)

    def send_otp_email(self, to_email: str, otp: str) -> bool:
        """Sends a 6-digit OTP password reset PIN via email."""
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#0A5E46;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
                <h2 style="margin:0;font-size:18px;">Password Reset Request</h2>
            </div>
            <div style="background:white;border:1px solid #DCE5E1;padding:20px;border-radius:0 0 8px 8px;">
                <p style="font-size:14px;color:#16242B;">Hello,</p>
                <p style="font-size:14px;color:#5F717A;">
                    You requested a password reset. Use the One Time PIN below
                    to reset your password. It expires in <strong>10 minutes</strong>.
                </p>
                <div style="text-align:center;margin:24px 0;">
                    <div style="display:inline-flex;gap:8px;background:#F1F5F3;
                         padding:16px 24px;border-radius:12px;">
                        {''.join([
                            f'<div style="width:44px;height:56px;background:#0A5E46;'
                            f'color:white;border-radius:8px;display:inline-flex;'
                            f'align-items:center;justify-content:center;'
                            f'font-size:26px;font-weight:800;font-family:monospace;">'
                            f'{d}</div>'
                            for d in otp
                        ])}
                    </div>
                </div>
                <div style="background:#FBF3E4;border-left:4px solid #B8761D;padding:12px;
                     border-radius:4px;margin:16px 0;">
                    <p style="font-size:12px;color:#5F717A;margin:0;">
                        <strong>Security tip:</strong> If you did not request this reset,
                        please ignore this email and consider changing your password.
                    </p>
                </div>
                <hr style="border:none;border-top:1px solid #DCE5E1;margin:16px 0;">
                <p style="font-size:11px;color:#999;">
                    RPM System - AI-Integrated Remote Patient Monitoring | Academic Demo Only
                </p>
            </div>
        </div>
        """
        text = (
            f"Password Reset Request\n\n"
            f"Your One Time PIN is: {otp}\n\n"
            f"It expires in 10 minutes.\n"
            f"If you did not request this, please ignore this email."
        )
        return self._send_email(
            to_email,
            "[RPM] Your Password Reset PIN",
            html,
            text,
        )
