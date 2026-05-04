# Project ops (Bot + FastAPI)

Ниже — минимальный “ops” README: как поднять **бота** и **FastAPI** как отдельные сервисы через **PM2**, и как проксировать API через **Nginx** на домен.

> Примеры ниже ориентированы на Linux/VPS (как в твоём примере с `./venv/bin/python`).

## 0) Один раз на сервере

```bash
cd /path/to/your/repo
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Миграции (SQLite):

```bash
./venv/bin/alembic upgrade head
```

## 1) Запуск через PM2 (команды)

### 1.1 Бот (отдельный процесс)

```bash
cd /path/to/your/repo
pm2 start src/app.py --interpreter ./venv/bin/python --name bot
```

### 1.2 FastAPI (отдельный процесс, порт 8010)

Рекомендованный запуск — через `python -m uvicorn` (чтобы точно использовалось `venv` окружение):

```bash
cd /path/to/your/repo
pm2 start "./venv/bin/python -m uvicorn api.main:app --app-dir src --host 127.0.0.1 --port 8010" --name bot_api
```

Проверка:

```bash
pm2 status
pm2 logs bot
pm2 logs bot_api
```

Автозапуск после ребута:

```bash
pm2 save
pm2 startup
```

## 2) Nginx (главный конфиг для домена)

Пример server block для проксирования **всего**, что приходит на домен, в FastAPI на `127.0.0.1:8010`.

Файл (пример): `/etc/nginx/sites-available/bot_api.conf`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # (опционально) ограничить размер тела запросов
    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # таймауты
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Активировать:

```bash
sudo ln -s /etc/nginx/sites-available/bot_api.conf /etc/nginx/sites-enabled/bot_api.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 3) Важно про .env

- И бот, и API читают `.env`.
- SQLite файл по умолчанию: `./data/sqlite_database/bot.db`
- Для API нужен `API_KEY` в `.env` (заголовок `X-API-Key`).

