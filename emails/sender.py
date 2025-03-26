from logging import log
from aiosmtplib import SMTPResponseException
from fastapi import HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import jinja2
from core.config import settings
from emails.utils import is_valid_email, generate_verification_code, set_email_verification_code

conf = ConnectionConfig(
    MAIL_USERNAME=settings.EMAIL_USERNAME,
    MAIL_PASSWORD=settings.EMAIL_PASSWORD,
    MAIL_FROM=settings.EMAIL_USERNAME,
    MAIL_PORT=settings.EMAIL_PORT,
    MAIL_SERVER=settings.EMAIL_SMTP_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

env = jinja2.Environment(loader=jinja2.PackageLoader(package_name="emails", package_path="templates"))

templates = {
    'register' : ['register_email.html','Register Email Verification'],
    'login' : ['login_email.html','Login Email Verification'],
    'reset' : ['reset_email.html','Reset Password Verification']
}

def send_verification_email(to_email: str, type: str):
    if not is_valid_email(to_email):
        raise HTTPException(status_code=400, detail="Invalid email address")
    if type not in templates:
        raise HTTPException(status_code=400, detail="Invalid verification type")
    code = generate_verification_code()
    template = env.get_template(templates[type][0])
    message = MessageSchema(
        subject=templates[type][1],
        recipients=[to_email],
        body=template.render(verification_code=code),
        subtype=MessageType.html
    )
    fm = FastMail(config=conf)
    async def _send_email():
        try:
            set_email_verification_code(to_email, code)
            await fm.send_message(message)
        except SMTPResponseException as e:
            pass
        except Exception as e:
            log("error", e)
    return _send_email

# if __name__ == '__main__':
#    import asyncio
#    asyncio.run(send_verification_email(to_email=settings.EMAIL_USERNAME, code=generate_verification_code(), type='register')())

