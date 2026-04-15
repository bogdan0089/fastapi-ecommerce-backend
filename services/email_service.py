import aiosmtplib
from email.mime.text import MIMEText
from core.config import settings


class EmailService:


    @staticmethod
    async def send_verification_email(to_email: str, token: str):
        message = MIMEText(f"code: {token}")
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
    