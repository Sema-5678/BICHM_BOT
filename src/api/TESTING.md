# API testing

## 0) Start the API

From repo root:

```powershell
uvicorn api.main:app --app-dir src --host 127.0.0.1 --port 8000
```

## 1) Quick manual checks (curl)

Set env vars (PowerShell):

```powershell
$env:API_BASE_URL="http://127.0.0.1:8000"
$env:API_KEY="<your-api-key>"
$env:TG_ID="5273608148"
```

Health:

```powershell
curl "$env:API_BASE_URL/health"
curl "$env:API_BASE_URL/ready"
curl "$env:API_BASE_URL/version"
```

Get user card:

```powershell
curl "$env:API_BASE_URL/v1/users/$env:TG_ID" -H "X-API-Key: $env:API_KEY"
```

Add BC +10.50:

```powershell
curl -X POST "$env:API_BASE_URL/v1/users/$env:TG_ID/balance/bc" -H "X-API-Key: $env:API_KEY" -H "Content-Type: application/json" -d "{\"amount\":\"10.50\",\"mode\":\"delta\"}"
```

Remove RUB -55.10:

```powershell
curl -X POST "$env:API_BASE_URL/v1/users/$env:TG_ID/balance/rub" -H "X-API-Key: $env:API_KEY" -H "Content-Type: application/json" -d "{\"amount\":\"-55.10\",\"mode\":\"delta\"}"
```

Reset farm (confirm required):

```powershell
curl -X POST "$env:API_BASE_URL/v1/users/$env:TG_ID/farm/reset" -H "X-API-Key: $env:API_KEY" -H "Content-Type: application/json" -d "{\"confirm\":true}"
curl "$env:API_BASE_URL/v1/users/$env:TG_ID/farm" -H "X-API-Key: $env:API_KEY"
```

Inventory add/remove/clear:

```powershell
curl -X POST "$env:API_BASE_URL/v1/users/$env:TG_ID/inventory/add" -H "X-API-Key: $env:API_KEY" -H "Content-Type: application/json" -d "{\"category_id\":\"1\",\"item_id\":\"10\",\"quantity\":3}"
curl "$env:API_BASE_URL/v1/users/$env:TG_ID/inventory" -H "X-API-Key: $env:API_KEY"
curl -X POST "$env:API_BASE_URL/v1/users/$env:TG_ID/inventory/remove" -H "X-API-Key: $env:API_KEY" -H "Content-Type: application/json" -d "{\"category_id\":\"1\",\"item_id\":\"10\",\"quantity\":2}"
curl -X POST "$env:API_BASE_URL/v1/users/$env:TG_ID/inventory/clear" -H "X-API-Key: $env:API_KEY"
```

## 2) Full smoke test script

From repo root:

```powershell
python scripts/api_smoke_test.py --base-url http://127.0.0.1:8000 --api-key "<your-api-key>" --telegram-id 5273608148
```

The script prints logs and fails fast on unexpected responses.

