# DB smoke tests

Запуск из корня проекта:

```powershell
pip install -r requirements.txt
python tests/db_smoke_test.py
```

Скрипт читает `.env` (через `python-dotenv`) и использует `DB_LITE` или `DB_URL` (если заданы), иначе — дефолтный SQLite путь из `src/database/engine.py`.
