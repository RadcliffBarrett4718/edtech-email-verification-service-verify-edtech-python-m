from datetime import date, timedelta
from html import escape
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from .infrai_email import InfraiEmail


class CourseDelivery(BaseModel):
    course_id: str = Field(min_length=1)
    course_title: str = Field(min_length=1)
    starts_on: date
    completion_window_days: int = Field(ge=1, le=365)


class SignupRequest(BaseModel):
    signup_id: UUID
    learner_email: EmailStr
    learner_name: str = Field(min_length=1, max_length=100)
    verification_url: HttpUrl
    course: CourseDelivery


class EducatorReportRow(BaseModel):
    course_id: str
    learner_email: EmailStr
    verification_status: str
    deadline: date


class SignupResult(BaseModel):
    message_id: str
    deadline: date
    report: EducatorReportRow


def enrollment_deadline(course: CourseDelivery) -> date:
    return course.starts_on + timedelta(days=course.completion_window_days)


def enroll_learner(request: SignupRequest, email: InfraiEmail) -> SignupResult:
    deadline = enrollment_deadline(request.course)
    safe_name = escape(request.learner_name)
    safe_course = escape(request.course.course_title)
    link = escape(str(request.verification_url), quote=True)
    message_id = email.send_verification(
        to=str(request.learner_email),
        subject=f"Verify your email for {request.course.course_title}",
        html=(
            f"<p>Hi {safe_name},</p>"
            f"<p>Confirm your email to join <strong>{safe_course}</strong>.</p>"
            f'<p><a href="{link}">Verify email</a></p>'
            f"<p>Your course deadline is {deadline.isoformat()}.</p>"
        ),
        idempotency_key=f"signup-verification:{request.signup_id}",
    )
    report = EducatorReportRow(
        course_id=request.course.course_id,
        learner_email=request.learner_email,
        verification_status="pending_email_verification",
        deadline=deadline,
    )
    return SignupResult(message_id=message_id, deadline=deadline, report=report)

