from datetime import date
from uuid import UUID

from edtech_verification.signup_service import CourseDelivery, SignupRequest, enroll_learner


class RecordingEmail:
    def __init__(self) -> None:
        self.call: dict[str, str] = {}

    def send_verification(self, **values: str) -> str:
        self.call = values
        return "msg_course_42"


def test_signup_sets_course_deadline_and_pending_report() -> None:
    email = RecordingEmail()
    request = SignupRequest(
        signup_id=UUID("3d594650-b2e1-4bc6-b0d7-257286a8b112"),
        learner_email="mina@example.com",
        learner_name="Mina",
        verification_url="https://school.example/verify-email?token=signed-token",
        course=CourseDelivery(
            course_id="python-101",
            course_title="Python 101",
            starts_on=date(2026, 9, 1),
            completion_window_days=21,
        ),
    )

    result = enroll_learner(request, email)  # type: ignore[arg-type]

    assert result.deadline == date(2026, 9, 22)
    assert result.report.verification_status == "pending_email_verification"
    assert result.report.course_id == "python-101"
    assert email.call["to"] == "mina@example.com"
    assert email.call["idempotency_key"] == (
        "signup-verification:3d594650-b2e1-4bc6-b0d7-257286a8b112"
    )
    assert "2026-09-22" in email.call["html"]

