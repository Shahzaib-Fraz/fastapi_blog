from email.message import EmailMessage
import aiosmtplib
from config import settings

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

async def send_email(
        to_email: str,
        subject: str,
        plain_text: str,
        html_content: str|None = None):
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(plain_text)
    if html_content:
        message.add_alternative(html_content, subtype="html")
    
    await aiosmtplib.send(
        message,
        hostname=settings.mail_server,
        port=settings.mail_port,
        username=settings.mail_username if settings.mail_username else None,
        password=settings.mail_password.get_secret_value() or None,
        start_tls=settings.mail_use_tls
    )

async def send_password_reset_email(to_email: str,username: str,  token: str):
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    template = templates.env.get_template("email/password_reset.html")

    html_content = templates.render(username=username, reset_url=reset_url)
    plain_text = f"Hi {username},\n\nYou have requested to reset your password. Please click the link below to reset your password:\n\n{reset_url}\n\nIf you did not request this, please ignore this email."
    
    await send_email(
        to_email=to_email,
        subject="Password Reset Request",
        plain_text=plain_text,
        html_content=html_content
    )


