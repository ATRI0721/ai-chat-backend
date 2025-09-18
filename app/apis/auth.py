from fastapi import APIRouter, BackgroundTasks, Body, HTTPException
from app.apis.user import generate_user_response
from app.core.deps import CurrentUser
from app.emails.utils import  verify_email
from app.emails.sender import send_verification_email
from app.models.interfaces import AuthEmailVerification, UserResponse

router = APIRouter(tags=["auth"], prefix="/auth")

@router.post("/send-verification/{type}")
def send_verification(type: str, background_tasks: BackgroundTasks, email: str = Body(embed=True)):
    send_message = send_verification_email(email, type)
    background_tasks.add_task(send_message)
    return {"message": "Verification code sent"}

@router.post("/verify-verification")
def verify_verification(email_verification: AuthEmailVerification):
    if not verify_email(email_verification.email, email_verification.verification_code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    return {"message": "Email verified", "valid": True}

@router.get("/verify", response_model=UserResponse)
def verify(user: CurrentUser):
    return generate_user_response(user)

@router.get("/refresh-token", response_model=UserResponse)
def refresh_token(user: CurrentUser):
    return generate_user_response(user)