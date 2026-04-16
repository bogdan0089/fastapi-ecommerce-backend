import aiosmtplib
from email.mime.text import MIMEText
from core.config import settings


class EmailService:


    @staticmethod
    async def send_verification_email(to_email: str, token: str):
        message = MIMEText(f"Click to verify your email:\nhttp://localhost:8000/auth/verify/{token}")
        message["Subject"] = "Verification email"
        message["From"] = settings.EMAIL_USER
        message["To"] = to_email
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            username=settings.EMAIL_USER,
            password=settings.EMAIL_PASSWORD,
            start_tls=True
        )
    

    @staticmethod
    async def send_reset_password_email(to_email: str, token: str):
        message = MIMEText(f"Click to reset your password:\nhttp://localhost:8000/auth/reset_password/{token}")
        message["Subject"] = "Password reset"
        message["From"] = settings.EMAIL_USER
        message["To"] = to_email
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            username=settings.EMAIL_USER,
            password=settings.EMAIL_PASSWORD,
            start_tls=True
        )