# FastAPI service

## Install

```powershell
pip install -r requirements.txt
```

## Env

Add to `.env`:

- `DB_LITE=sqlite+aiosqlite:///./data/sqlite_database/bot.db`
- `API_KEY=change-me`

Optional limits:

- `MAX_BALANCE=1000000`
- `MAX_RUB_BALANCE=100000000`

## Run (separate service)

```powershell
uvicorn api.main:app --app-dir src --host 127.0.0.1 --port 8000
```

The service loads `.env` automatically on startup (via `python-dotenv`).

## Endpoints

Header: `X-API-Key: <API_KEY>`

- `POST /v1/users/{telegram_id}/balance/bc`
- `POST /v1/users/{telegram_id}/balance/rub`

Body:

```json
{ "amount": "10.50", "mode": "delta" }
```

`mode`:
- `delta` — add/subtract
- `set` — set absolute value
