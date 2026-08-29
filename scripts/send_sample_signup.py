from datetime import date
import os
from uuid import uuid4

from edtech_verification.infrai_email import InfraiEmail
from edtech_verification.signup_service import CourseDelivery, SignupRequest, enroll_learner


def main() -> None:
    recipient = os.environ.get("DEMO_EMAIL_TO")
    if not recipient:
        raise RuntimeError("DEMO_EMAIL_TO is required")
    request = SignupRequest(
        signup_id=uuid4(),
        learner_email=recipient,
        learner_name="Mina",
        verification_url="http://localhost:3000/verify-email?token=demo-token",
        course=CourseDelivery(
            course_id="python-101",
            course_title="Python 101",
            starts_on=date(2026, 9, 1),
            completion_window_days=21,
        ),
    )
    result = enroll_learner(request, InfraiEmail())
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
