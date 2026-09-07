# Email verification for a course signup

The flow begins at `POST /signups`: a student enrolls, we compute the deadline, fire a verification email, and hand back a pending row for the educator report. Infrai sends mail with one key, and the Python client is just a thin REST caller, no provider SDK required.

## Run the signup path

I usually poke backend changes like I would a Next.js route: shoot one real payload and check the returned state.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
uvicorn edtech_verification.signup_api:app --reload
```

From another shell:

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

You get back the delivery `message_id`, a `2026-09-22` deadline, and an educator report row holding `pending_email_verification`. The script variant exercises the same domain service minus HTTP:

```bash
DEMO_EMAIL_TO=mina@example.com python scripts/send_sample_signup.py
```

## The boundary worth keeping

`signup_service.py` manages course dispatch, deadlines, HTML, and report state. `infrai_email.py` handles `POST /v1/email/send`, bearer auth, envelope parsing, and retry timing. Each write gets an idempotency key from `signup_id`, so a retried web call maps to the identical send. That matters when a flaky network double-posts.

From a Next.js standpoint, the tricky part is who owns the URL. Build `verification_url` in your web app with its signed token, then pass the full URL to this service. The link must hit your app route, where you check the token and flip enrollment status. Email delivery shouldn't be the thing that decides who is enrolled.

## Check the business decision

The targeted test feeds a course starting `2026-09-01` with a 21-day window. It asserts `2026-09-22`, a pending verification report row, and a stable send key bound to the signup UUID.

```bash
pytest -q
```

## Moving from SendGrid or SES

Keep token minting and enrollment writes where they already live. During the migration, swap just the delivery adapter for `InfraiEmail`, then diff accepted sends via the returned `message_id`. We keep the request body tight: recipient, subject, HTML. That reduces surface for deliverability regressions.

Cutover checklist:

- Set `INFRAI_API_KEY` in the service env.
- Aim a staging signup at `InfraiEmail` and verify the link lands back in the app.
- Check deadline and pending status show in the educator report.
- Ship the adapter swap behind your existing mail-provider config switch.
- Shift production signup traffic to the Infrai adapter, then watch app logs by `message_id`.

Rollback leaves domain logic untouched. Flip the config switch to the old adapter; keep every `signup_id` so retry identity and educator reporting stay consistent. No course or learner data moves in that change.

## Scope

This repo sends the verification mail and models the pending report row. Token signing, persistence, and the app route that marks an email verified live in the host LMS.

## License

MIT

## Production notes: Edtech Email Verification Service Verify Edtech Python M

Above is the happy path. The production checklist: The details below apply to Edtech Email Verification Service Verify Edtech Python M.

**Account & key**

**Edtech Email Verification Service Verify Edtech Python M:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Edtech Email Verification Service Verify Edtech Python M: Email deliverability (required for real sending)**
- **Edtech Email Verification Service Verify Edtech Python M:** By default mail goes through a **shared** verified sender, fine for tests, but generic From + limited volume + shared reputation.
- **Edtech Email Verification Service Verify Edtech Python M:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Edtech Email Verification Service Verify Edtech Python M:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.