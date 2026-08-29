import json

import httpx

from edtech_verification.infrai_email import InfraiEmail


def test_send_decodes_envelope_and_returns_message_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/email/send"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert json.loads(request.content)["idempotency_key"] == "signup:42"
        return httpx.Response(
            200,
            json={
                "ok": True,
                "data": {"message_id": "msg_42"},
                "error": None,
                "metadata": {},
            },
        )

    email = InfraiEmail(api_key="test-key", transport=httpx.MockTransport(handler))
    message_id = email.send_verification(
        to="mina@example.com",
        subject="Verify email",
        html="<p>Verify</p>",
        idempotency_key="signup:42",
    )

    assert message_id == "msg_42"
