# Dental Bot API

FastAPI service that powers the dental assistant chat. This repo intentionally avoids shipping secrets; configure everything via environment variables.

## Setup
- Create a virtualenv and install deps: `pip install -r requirements.txt`.
- Copy `.env.example` to `.env` and fill in values (the file is gitignored).

Key vars:
- `OPENAI_API_KEY` (required)
- `SUPABASE_URL` and `SUPABASE_SECRET_KEY` (required if using Supabase persistence)
- `IP_HASH_SALT` (required) — use a random string; do not reuse the old one.

Generate a new hash salt (example):
```bash
python - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
```

## Run
```bash
uvicorn app.main:app --reload
```

## Health
`GET /health` returns `{ "ok": true, "env": "<APP_ENV>" }`.
