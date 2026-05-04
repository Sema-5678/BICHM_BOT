# FastAPI API Reference

База URL (prod):

```powershell
$BASE_URL = "https://bichmbot.mooo.com"
```

Авторизация:
- Все защищённые эндпоинты требуют заголовок `X-API-Key`.
- Ключ берётся из `.env` на сервере (`API_KEY`).

Важно: **не храни и не коммить реальный API‑ключ в документации/репозитории**. Ниже в примерах используется переменная `$API_KEY`.

```powershell
$API_KEY = "<PUT_YOUR_API_KEY_HERE>"
```

Демо пользователь:

```powershell
$TG_ID = 5273608148
```

PowerShell команды используют `irm` (`Invoke-RestMethod`).

## Python examples (recommended)

Ниже — примеры на Python без сторонних библиотек (только стандартная библиотека `urllib`).

В начале можно определить базовые переменные и helper:

```python
import json
import urllib.request
import urllib.error

BASE_URL = "https://bichmbot.mooo.com"
API_KEY = "<PUT_YOUR_API_KEY_HERE>"
TG_ID = 5273608148


def api_request(method: str, path: str, body: dict | None = None, *, auth: bool = True):
    url = BASE_URL.rstrip("/") + path
    headers = {"Accept": "application/json"}
    if auth:
        headers["X-API-Key"] = API_KEY

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            payload = {"raw": raw.decode("utf-8", errors="ignore")}
        raise RuntimeError(f"{method} {path} -> {e.code}: {payload}") from None
```

## Форматы данных

### Money / Decimal

Баланс/суммы передаются строкой с десятичной точкой, например `"10.50"` или `"-7.25"`.

### Общие ошибки

- `401 Invalid API key` — неверный/отсутствующий `X-API-Key`.
- `422` — ошибка валидации входных данных.
- `404 User not found` — пользователя нет (на read эндпоинтах).
- `500` — ошибка сервера.

## 1) Health / Meta

### `GET /health`
Назначение: проверка “жив ли сервис”.

Запрос:
```powershell
irm "$BASE_URL/health"
```

Python:
```python
print(api_request("GET", "/health", auth=False))
```

Ответ (пример):
```json
{"status":"ok"}
```

### `GET /ready`
Назначение: проверка готовности (доступна ли БД).

Запрос:
```powershell
irm "$BASE_URL/ready"
```

Python:
```python
print(api_request("GET", "/ready", auth=False))
```

Ответ (пример):
```json
{"db":"ok","migrations":"unknown"}
```

### `GET /version`
Назначение: версия API.

Запрос:
```powershell
irm "$BASE_URL/version"
```

Python:
```python
print(api_request("GET", "/version", auth=False))
```

Ответ (пример):
```json
{"api_version":"0.1.0","alembic_head":"0001_create_core_tables"}
```

## 2) Балансы (BC / RUB)

Эти эндпоинты:
- требуют `X-API-Key`,
- **создают пользователя**, если его ещё нет (через `orm_get_or_create_user`),
- поддерживают режимы:
  - `mode="delta"` — прибавить/убавить
  - `mode="set"` — установить абсолютное значение
- ограничивают баланс снизу `0.00` и сверху лимитом (`MAX_BALANCE` / `MAX_RUB_BALANCE`).

### `POST /v1/users/{telegram_id}/balance/bc`
Назначение: изменить BC.

Запрос (пример, +10.50):
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/balance/bc" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"amount":"10.50","mode":"delta"}'
```

Ответ (пример):
```json
{"user_id":5273608148,"currency":"BC","mode":"delta","amount":"10.50","new_balance":"123.45"}
```

Python:
```python
resp = api_request(
    "POST",
    f"/v1/users/{TG_ID}/balance/bc",
    {"amount": "10.50", "mode": "delta"},
)
print(resp)
```

### `POST /v1/users/{telegram_id}/balance/rub`
Назначение: изменить RUB.

Запрос (пример, -55.10):
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/balance/rub" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"amount":"-55.10","mode":"delta"}'
```

Ответ (пример):
```json
{"user_id":5273608148,"currency":"RUB","mode":"delta","amount":"-55.10","new_balance":"0.00"}
```

Python:
```python
resp = api_request(
    "POST",
    f"/v1/users/{TG_ID}/balance/rub",
    {"amount": "-55.10", "mode": "delta"},
)
print(resp)
```

## 3) Users (read)

Все эндпоинты этого раздела требуют `X-API-Key` и **не создают** пользователей автоматически.

### `GET /v1/users/{telegram_id}`
Назначение: карточка пользователя.

Запрос:
```powershell
irm "$BASE_URL/v1/users/$TG_ID" -Headers @{ "X-API-Key" = $API_KEY }
```

Python:
```python
print(api_request("GET", f"/v1/users/{TG_ID}"))
```

Ответ (пример):
```json
{
  "id": 5273608148,
  "username": "",
  "minecraft_username": null,
  "balance": "10.50",
  "rub_balance": "0.00",
  "deposit": "0.00",
  "debt": "0.00",
  "credit_rating": 100,
  "date_create": 1710000000,
  "date_update": 1710000001,
  "created_at": "2026-05-04T07:00:00",
  "updated_at": "2026-05-04T07:00:00"
}
```

### `GET /v1/users/{telegram_id}/balances`
Назначение: только финансовые поля.

Запрос:
```powershell
irm "$BASE_URL/v1/users/$TG_ID/balances" -Headers @{ "X-API-Key" = $API_KEY }
```

Python:
```python
print(api_request("GET", f"/v1/users/{TG_ID}/balances"))
```

Ответ (пример):
```json
{"id":5273608148,"balance":"10.50","rub_balance":"0.00","deposit":"0.00","debt":"0.00","credit_rating":100}
```

### `GET /v1/users`
Назначение: список пользователей с пагинацией/сортировкой.

Запрос (пример):
```powershell
irm "$BASE_URL/v1/users?limit=50&offset=0&sort=date_update&order=desc" -Headers @{ "X-API-Key" = $API_KEY }
```

Python:
```python
print(api_request("GET", "/v1/users?limit=50&offset=0&sort=date_update&order=desc"))
```

Ответ (пример):
```json
{"items":[{...user_card...}],"limit":50,"offset":0,"total":1234}
```

### `GET /v1/users/search`
Назначение: поиск (по `id`, `username`, `minecraft_username`).

Запрос (пример, по id):
```powershell
irm "$BASE_URL/v1/users/search?id=$TG_ID&limit=5&offset=0" -Headers @{ "X-API-Key" = $API_KEY }
```

Python:
```python
print(api_request("GET", f"/v1/users/search?id={TG_ID}&limit=5&offset=0"))
```

Ответ (пример):
```json
{"items":[{...user_card...}],"limit":5,"offset":0,"total":1}
```

### `GET /v1/users/{telegram_id}/inventory`
Назначение: получить инвентарь пользователя.

Запрос:
```powershell
irm "$BASE_URL/v1/users/$TG_ID/inventory" -Headers @{ "X-API-Key" = $API_KEY }
```

Python:
```python
print(api_request("GET", f"/v1/users/{TG_ID}/inventory"))
```

Ответ (пример):
```json
{"id":5273608148,"inventory":{"1_10":1}}
```

### `GET /v1/users/{telegram_id}/farm` (временно отключено)
Сейчас эндпоинт отключён и возвращает `403`.

Запрос:
```powershell
irm "$BASE_URL/v1/users/$TG_ID/farm" -Headers @{ "X-API-Key" = $API_KEY }
```

Python:
```python
try:
    print(api_request("GET", f"/v1/users/{TG_ID}/farm"))
except RuntimeError as e:
    print("Expected error:", e)
```

Ответ:
```json
{"detail":"Farm API is temporarily disabled"}
```

## 4) Users (write)

### `PATCH /v1/users/{telegram_id}`
Назначение: обновить `username` / `minecraft_username`.

Запрос (пример, установить ник Minecraft):
```powershell
irm -Method Patch "$BASE_URL/v1/users/$TG_ID" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"minecraft_username":"Steve"}'
```

Запрос (пример, очистить ник Minecraft):
```powershell
irm -Method Patch "$BASE_URL/v1/users/$TG_ID" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"minecraft_username":null}'
```

Ответ: `UserCardOut` как в `GET /v1/users/{telegram_id}`.

Python (set):
```python
print(api_request("PATCH", f"/v1/users/{TG_ID}", {"minecraft_username": "Steve"}))
```

Python (clear):
```python
print(api_request("PATCH", f"/v1/users/{TG_ID}", {"minecraft_username": None}))
```

### `POST /v1/users/{telegram_id}/inventory/add`
Назначение: добавить предмет в инвентарь.

Запрос:
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/inventory/add" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"category_id":"1","item_id":"10","quantity":3}'
```

Ответ:
```json
{"id":5273608148,"inventory":{"1_10":3}}
```

Python:
```python
print(
    api_request(
        "POST",
        f"/v1/users/{TG_ID}/inventory/add",
        {"category_id": "1", "item_id": "10", "quantity": 3},
    )
)
```

### `POST /v1/users/{telegram_id}/inventory/remove`
Назначение: убрать предмет из инвентаря.

Правила:
- уменьшает количество,
- если стало `<= 0` — ключ удаляется.

Запрос:
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/inventory/remove" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"category_id":"1","item_id":"10","quantity":2}'
```

Ответ:
```json
{"id":5273608148,"inventory":{"1_10":1}}
```

Python:
```python
print(
    api_request(
        "POST",
        f"/v1/users/{TG_ID}/inventory/remove",
        {"category_id": "1", "item_id": "10", "quantity": 2},
    )
)
```

### `POST /v1/users/{telegram_id}/inventory/clear` (временно отключено)
Сейчас эндпоинт отключён и возвращает `403`.

Запрос:
```powershell
irm -Method Post "$BASE_URL/v1/users/$TG_ID/inventory/clear" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{}'
```

Ответ:
```json
{"detail":"Inventory clear endpoint is temporarily disabled"}
```

Python:
```python
try:
    api_request("POST", f"/v1/users/{TG_ID}/inventory/clear", {})
except RuntimeError as e:
    print("Expected error:", e)
```

### `POST /v1/users/{telegram_id}/farm/reset` (временно отключено)
Сейчас эндпоинт отключён и возвращает `403`.

## 5) Stats / Analytics

### `GET /v1/stats/users/count`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/users/count" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"users":1234}
```

Python:
```python
print(api_request("GET", "/v1/stats/users/count"))
```

### `GET /v1/stats/balances/top`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/balances/top?limit=10" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"items":[{"id":1,"total":"123.45","balance":"100.00","deposit":"23.45"}]}
```

Python:
```python
print(api_request("GET", "/v1/stats/balances/top?limit=10"))
```

### `GET /v1/stats/balances/summary`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/balances/summary" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"bc":{"sum":"...","avg":"..."},"rub":{"sum":"...","avg":"..."},"deposit":{"sum":"...","avg":"..."},"debt":{"sum":"...","avg":"..."}}
```

Python:
```python
print(api_request("GET", "/v1/stats/balances/summary"))
```

### `GET /v1/stats/active`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/active?days=7" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"days":7,"active_users":123}
```

Python:
```python
print(api_request("GET", "/v1/stats/active?days=7"))
```

### `GET /v1/stats/inventory/top-items`
Запрос:
```powershell
irm "$BASE_URL/v1/stats/inventory/top-items?limit=50" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"items":[{"item_key":"1_10","total_qty":999}]}
```

Python:
```python
print(api_request("GET", "/v1/stats/inventory/top-items?limit=50"))
```

## 6) Config (Singletons)

Сюда входят только `minecraft_goods` и `mini_game_farm` (админы не доступны через API).

### `GET /v1/config/minecraft_goods`
Запрос:
```powershell
irm "$BASE_URL/v1/config/minecraft_goods" -Headers @{ "X-API-Key" = $API_KEY }
```
Ответ:
```json
{"key":"minecraft_goods","value":{...}}
```

Python:
```python
print(api_request("GET", "/v1/config/minecraft_goods"))
```

### `PUT /v1/config/minecraft_goods`
Полная замена конфига.

Запрос (пример — загрузить JSON из файла):
```powershell
$body = Get-Content -Raw ".\\data\\json_database\\minecraft_goods.json"
irm -Method Put "$BASE_URL/v1/config/minecraft_goods" -Headers @{ "X-API-Key" = $API_KEY } -ContentType "application/json" -Body $body
```

Python:
```python
import json
from pathlib import Path

goods = json.loads(Path("data/json_database/minecraft_goods.json").read_text(encoding="utf-8"))
print(api_request("PUT", "/v1/config/minecraft_goods", goods))
```

### `PATCH /v1/config/minecraft_goods`
Точечная модификация (операции):

`set_item_field` (пример):
```powershell
irm -Method Patch "$BASE_URL/v1/config/minecraft_goods" `
  -Headers @{ "X-API-Key" = $API_KEY } `
  -ContentType "application/json" `
  -Body '{"op":"set_item_field","category_id":"1","item_id":"10","field":"base_price","value":"100.00"}'
```

Python:
```python
print(
    api_request(
        "PATCH",
        "/v1/config/minecraft_goods",
        {"op": "set_item_field", "category_id": "1", "item_id": "10", "field": "base_price", "value": "100.00"},
    )
)
```

### `GET /v1/config/mini_game_farm`
Запрос:
```powershell
irm "$BASE_URL/v1/config/mini_game_farm" -Headers @{ "X-API-Key" = $API_KEY }
```

Python:
```python
print(api_request("GET", "/v1/config/mini_game_farm"))
```

### `PUT /v1/config/mini_game_farm`
Запрос (пример — загрузить JSON из файла):
```powershell
$body = Get-Content -Raw ".\\data\\json_database\\mini_game_farm.json"
irm -Method Put "$BASE_URL/v1/config/mini_game_farm" -Headers @{ "X-API-Key" = $API_KEY } -ContentType "application/json" -Body $body
```

Python:
```python
farm = json.loads(Path("data/json_database/mini_game_farm.json").read_text(encoding="utf-8"))
print(api_request("PUT", "/v1/config/mini_game_farm", farm))
```
