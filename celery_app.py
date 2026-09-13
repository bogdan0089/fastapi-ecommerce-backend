import smtplib
from email.mime.text import MIMEText

from celery import Celery

from core.config import settings

celery = Celery("tasks", broker=settings.RABBITMQ_URL)

SMTP_TIMEOUT_SECONDS = 30

RETRY = {
    "autoretry_for": (smtplib.SMTPException, OSError),
    "retry_backoff": True,
    "retry_jitter": True,
    "max_retries": 3,
}


def _send(to_email: str, subject: str, body: str) -> None:
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.EMAIL_USER
    message["To"] = to_email
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=SMTP_TIMEOUT_SECONDS) as server:
        server.starttls()
        server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        server.sendmail(settings.EMAIL_USER, to_email, message.as_string())


@celery.task(**RETRY)
def send_verification_email(to_email: str, token: str) -> None:
    _send(
        to_email,
        "Verification email",
        f"Click to verify your email:\n{settings.FRONTEND_URL}/auth/verify/{token}",
    )


@celery.task(**RETRY)
def send_reset_password_email(to_email: str, token: str) -> None:
    _send(
        to_email,
        "Password reset",
        f"Click to reset your password:\n{settings.FRONTEND_URL}/reset-password?token={token}",
    )


@celery.task(**RETRY)
def send_order_status_email(to_email: str, order_id: int, status: str) -> None:
    _send(
        to_email,
        "Order update",
        f"Your order {order_id} status changed to {status}",
    )


@celery.task(**RETRY)
def send_new_order_notification(
    admin_email: str, order_id: int, client_email: str, amount: float
) -> None:
    _send(
        admin_email,
        "New order",
        f"New order {order_id} was placed by {client_email} for ${amount}",
    )