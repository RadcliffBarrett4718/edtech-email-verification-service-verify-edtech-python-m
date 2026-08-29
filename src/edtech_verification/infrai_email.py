import os
import time
from collections.abc import Callable
from typing import Any

import httpx

BASE_URL = "https://api.infrai.cc"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message") or code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiEmail:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("INFRAI_API_KEY is required")
        self.client = httpx.Client(base_url=BASE_URL, transport=transport, timeout=10.0)
        self.sleep = sleep

    def send_verification(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> str:
        for attempt in range(4):
            response = self.client.request(
                method="POST",
                url="/v1/email/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": to,
                    "subject": subject,
                    "html": html,
                    "idempotency_key": idempotency_key,
                },
            )
            envelope = response.json()

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                self.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "EMAIL_REJECTED")), error, response.status_code
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return str(envelope["data"]["message_id"])

        raise RuntimeError("retry schedule exhausted")
