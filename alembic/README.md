# Alembic migrations

## 1) Install deps

```powershell
pip install -r requirements.txt
```

## 2) Configure DB URL

Use one of:

- `.env`: `DB_LITE=sqlite+aiosqlite:///./data/sqlite_database/bot.db`
- or environment: `ALEMBIC_DB_URL=sqlite+pysqlite:///./data/sqlite_database/bot.db`

Note: Alembic uses a **sync** driver. If your app uses `sqlite+aiosqlite`, Alembic will auto-convert it to `sqlite+pysqlite` internally.

## 3) Run migrations

Upgrade to latest:

```powershell
alembic upgrade head
```

Show current revision:

```powershell
alembic current
```

History:

```powershell
alembic history
```

Downgrade 1 step:

```powershell
alembic downgrade -1
```

## 4) Create new migration

Autogenerate from models in `src/database/models.py`:

```powershell
alembic revision --autogenerate -m "your message"
```

Then apply:

```powershell
alembic upgrade head
```

