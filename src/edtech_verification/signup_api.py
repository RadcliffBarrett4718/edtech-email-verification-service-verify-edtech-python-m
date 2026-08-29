from fastapi import Depends, FastAPI, HTTPException

from .infrai_email import InfraiEmail, InfraiError
from .signup_service import SignupRequest, SignupResult, enroll_learner

app = FastAPI(title="Edtech signup verification")


def email_client() -> InfraiEmail:
    return InfraiEmail()


@app.post("/signups", response_model=SignupResult, status_code=201)
def create_signup(
    request: SignupRequest, email: InfraiEmail = Depends(email_client)
) -> SignupResult:
    try:
        return enroll_learner(request, email)
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc

