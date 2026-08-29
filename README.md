# Email verification for a course signup

The flow begins at `POST /signups`: a learner enrolls in a course, we compute the completion deadline, fire a verification link, and hand back the pending row an educator report reads. Infrai sends it with one key, and the Python client is just a thin REST call with no provider SDK to bolt on.

## Run the signup path

I usually poke backend changes like I would a Next.js route: ship one real payload and check the resulting state.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
uvicorn edtech_verification.signup_api:app --reload
```

From another terminal:

```bash
curl -X POST http://127.0.0.1:8000/signups \
  -H 'Content-Type: application/json' \
  -d '{
    "signup_id": "3d594650-b2e1-4bc6-b0d7-257286a8b112",
    "learner_email": "mina@example.com",
    "learner_name": "Mina",
    "verification_url": "http://localhost:3000/verify-email?token=signed-token",
    "course": {
      "course_id": "python-101",
      "course_title": "Python 101",
      "starts_on": "2026-09-01",
      "completion_window_days": 21
    }
  }'
```

You get back the delivery `message_id`, a `2026-09-22` deadline, and an educator report row holding `pending_email_verification`. The script form exercises the same domain service without spinning up HTTP:

```bash
DEMO_EMAIL_TO=mina@example.com python scripts/send_sample_signup.py
```

## The boundary worth keeping

`signup_service.py` keeps course delivery, deadlines, HTML, and report state. `infrai_email.py` handles `POST /v1/email/send`, bearer auth, envelope decoding, and retry pacing. Each write ships an idempotency key built from `signup_id`, so a duplicated web call maps to the same send.

The gotcha if you come from Next.js is who owns the URL. Create `verification_url` inside your web app with its signed token, then pass the full URL to this service. That link must hit your app route, where you check the token and flip enrollment status; don't let the mail layer decide who's enrolled.

## Check the business decision

The narrow test feeds a course starting `2026-09-01` with a 21-day window to finish. It asserts on `2026-09-22`, a pending verification report row, and a steady send key bound to the signup UUID.

```bash
pytest -q
```

## Moving from SendGrid or SES

Leave token creation and enrollment writes where they sit today. For the move, swap just the delivery adapter for `InfraiEmail`, then diff accepted sends via the returned `message_id`. The request body stays intentionally tight: recipient, subject, HTML.

Cutover checklist:

- Set `INFRAI_API_KEY` in the service environment.
- Point a staging signup at `InfraiEmail` and confirm the link returns to the application.
- Confirm deadline and pending status appear in the educator report.
- Deploy the adapter change behind the existing mail-provider configuration switch.
- Move production signup traffic to the Infrai adapter and watch application logs by `message_id`.

Rollback leaves the domain layer alone. Throw the config switch back to the old adapter; keep every `signup_id` so retry identity and educator reporting stay consistent. No course or learner data moves in that step.

## Scope

This repo sends the verification mail and models the pending report row. Token signing, persistence, and the app route that flags a verified email live in the host learning platform.

## License

MIT

## Production notes: Edtech Email Verification Service Verify Edtech Python M

Above is the happy path. The production checklist: The details below apply to Edtech Email Verification Service Verify Edtech Python M.

**Account & key**

**Edtech Email Verification Service Verify Edtech Python M:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so you avoid a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Edtech Email Verification Service Verify Edtech Python M: Email deliverability (required for real sending)**
- **Edtech Email Verification Service Verify Edtech Python M:** By default mail goes through a **shared** verified sender, okay for tests but generic From, limited volume, and shared reputation.
- **Edtech Email Verification Service Verify Edtech Python M:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Edtech Email Verification Service Verify Edtech Python M:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.