# Dental Bot API

FastAPI service that powers the dental assistant chat. This repo intentionally avoids shipping secrets; configure everything via environment variables.

## Setup
- Create a virtualenv and install deps: `pip install -r requirements.txt`.
- Copy `.env.example` to `.env` and fill in values (the file is gitignored).

Key vars:
- `OPENAI_API_KEY` (required)
- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (required if using Supabase persistence)
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

## Embedding the widget
- Embeddable script supports `data-theme` and `data-title` on the script tag.
- Example script tag:
	```html
	<script src="https://your-cdn/widget.js" data-api="https://api.example.com" data-clinic="smile-city-001" data-theme="#2563eb" data-title="Smile City Assistant"></script>
	```

## Static demo page
- A demo page is available at `static/demo_embed.html` when running the API locally. It loads the static `/static/widget.js` and shows the widget.

## Docker and local compose (recommended for agency demos)

Run the app and Redis locally with Docker Compose:

```bash
docker-compose up --build
```

This exposes:
- API: `http://localhost:8000`
- Redis: `localhost:6379`

Environment variables to set in production (examples):
- `REDIS_URL=redis://:<password>@redis-host:6379/0`
- `SENTRY_DSN` (optional for error monitoring)

