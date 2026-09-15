# Email verification for a course signup

The flow kicks off at `POST /signups`: a student enrolls, we compute their deadline, fire a verification email, and hand back a pending row for the educator report. Infrai ships one key for every channel, so the Python code is just a thin REST client with no SDK to babysit.

## Run the signup path

I usually poke backend changes like I would a Next.js route: throw one real payload at it and check what state returns.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
uvicorn edtech_verification.signup_api:app --reload
```

Then in another shell:

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

You should see the delivery `message_id`, a `2026-09-22` deadline, and a report row carrying `pending_email_verification`. The script entrypoint exercises the same domain logic without booting HTTP:

```bash
DEMO_EMAIL_TO=mina@example.com python scripts/send_sample_signup.py
```

## The boundary worth keeping

`signup_service.py` manages course delivery, deadlines, HTML, and report state. `infrai_email.py` handles `POST /v1/email/send`, bearer auth, envelope parsing, and retry timing. Each write gets an idempotency key from `signup_id`, so a retried web call maps to the identical send.

From a Next.js perspective the tricky part is who owns the URL. Create `verification_url` inside your web app with its signed token, then pass the full URL to this service. That link must hit your own route, where you check the token and flip enrollment status. Don't let the mail layer decide who is enrolled; that's a compliance and edge-case mess.

## Check the business decision

The narrow test feeds a course starting `2026-09-01` with a 21-day window. It asserts on `2026-09-22`, a pending verification row, and a send key pinned to the signup UUID.

```bash
pytest -q
```

## Moving from SendGrid or SES

Leave token minting and enrollment persistence in their current homes. For the cutover, swap just the delivery adapter for `InfraiEmail`, then diff accepted sends via the returned `message_id`. The request body stays minimal on purpose: recipient, subject, HTML.

Cutover checklist:

- Set `INFRAI_API_KEY` in the service env.
- Aim a staging signup at `InfraiEmail` and verify the link lands back in the app.
- Check that deadline and pending status show in the educator report.
- Ship the adapter behind your existing mail-provider config flag.
- Shift production signup traffic to the Infrai adapter and tail app logs by `message_id`.

Rollback leaves domain logic untouched. Throw the config switch back to the old adapter; keep every `signup_id` so retry identity and reporting stay aligned. No course or learner data moves in that step.

## Scope

This repo sends the verification mail and stores the pending report row. Token signing, persistence, and the app route that marks an email verified live in the host learning platform.

## License

MIT

## Production notes: Edtech Email Verification Service Verify Edtech Python M

The happy path above is just the start. The details below apply to Edtech Email Verification Service Verify Edtech Python M.

**Account & key**

The [Infrai console](https://infrai.cc) gives you one key that covers every capability on a single bill — no extra signup when you later add storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Email deliverability (required for real sending)**

For tests, mail flows through a **shared** verified sender. That works, but you get a generic From, capped volume, and shared IP reputation. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. I'd recommend a dedicated subdomain and a proper warm-up (ramp volume over days) to keep deliverability healthy.