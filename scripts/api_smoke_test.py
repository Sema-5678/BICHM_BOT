from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Api:
    base_url: str
    api_key: str

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None, auth: bool = False) -> Any:
        url = self.base_url.rstrip("/") + path
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if auth:
            headers["X-API-Key"] = self.api_key

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                payload = {"raw": raw.decode("utf-8", errors="ignore")}
            raise RuntimeError(f"{method} {path} -> {e.code}: {payload}") from None

    def get(self, path: str, *, auth: bool = False) -> Any:
        return self._request("GET", path, None, auth=auth)

    def post(self, path: str, body: dict[str, Any], *, auth: bool = False) -> Any:
        return self._request("POST", path, body, auth=auth)

    def put(self, path: str, body: dict[str, Any], *, auth: bool = False) -> Any:
        return self._request("PUT", path, body, auth=auth)

    def patch(self, path: str, body: dict[str, Any], *, auth: bool = False) -> Any:
        return self._request("PATCH", path, body, auth=auth)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for FastAPI endpoints (1-5).")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--telegram-id", required=True, type=int)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="Also test PUT/PATCH config endpoints (may affect bot behavior). Default: off.",
    )
    args = parser.parse_args()

    _setup_logging(args.verbose)
    log = logging.getLogger("api_smoke_test")

    api = Api(base_url=args.base_url, api_key=args.api_key)
    tg = args.telegram_id

    log.info("1) health/ready/version")
    _assert(api.get("/health")["status"] == "ok", "health failed")
    _assert(api.get("/ready")["db"] == "ok", "ready failed")
    _assert("api_version" in api.get("/version"), "version failed")

    log.info("2) ensure user exists (create via balance delta 0)")
    api.post(f"/v1/users/{tg}/balance/bc", {"amount": "0.00", "mode": "delta"}, auth=True)

    log.info("3) users read endpoints")
    card = api.get(f"/v1/users/{tg}", auth=True)
    _assert(card["id"] == tg, "get_user returned wrong id")
    balances = api.get(f"/v1/users/{tg}/balances", auth=True)
    _assert(balances["id"] == tg, "get_user_balances wrong id")
    inv = api.get(f"/v1/users/{tg}/inventory", auth=True)
    _assert(inv["id"] == tg and isinstance(inv["inventory"], dict), "inventory read failed")
    farm = api.get(f"/v1/users/{tg}/farm", auth=True)
    _assert(farm["id"] == tg and isinstance(farm["farm_minigame"], dict), "farm read failed")

    log.info("4) patch user (minecraft_username set/clear)")
    patched = api.patch(f"/v1/users/{tg}", {"minecraft_username": "Steve"}, auth=True)
    _assert(patched.get("minecraft_username") == "Steve", "minecraft_username not set")
    patched = api.patch(f"/v1/users/{tg}", {"minecraft_username": None}, auth=True)
    _assert(patched.get("minecraft_username") is None, "minecraft_username not cleared")

    log.info("5) balances BC/RUB delta")
    bc1 = api.post(f"/v1/users/{tg}/balance/bc", {"amount": "1.00", "mode": "delta"}, auth=True)
    _assert(bc1["currency"] == "BC", "BC endpoint wrong currency")
    rub1 = api.post(f"/v1/users/{tg}/balance/rub", {"amount": "2.00", "mode": "delta"}, auth=True)
    _assert(rub1["currency"] == "RUB", "RUB endpoint wrong currency")

    log.info("6) inventory add/remove/clear")
    api.post(f"/v1/users/{tg}/inventory/clear", {}, auth=True)
    api.post(f"/v1/users/{tg}/inventory/add", {"category_id": "1", "item_id": "10", "quantity": 3}, auth=True)
    inv = api.get(f"/v1/users/{tg}/inventory", auth=True)["inventory"]
    _assert(inv.get("1_10") == 3, "inventory add failed")
    api.post(f"/v1/users/{tg}/inventory/remove", {"category_id": "1", "item_id": "10", "quantity": 2}, auth=True)
    inv = api.get(f"/v1/users/{tg}/inventory", auth=True)["inventory"]
    _assert(inv.get("1_10") == 1, "inventory remove failed")
    api.post(f"/v1/users/{tg}/inventory/clear", {}, auth=True)
    inv = api.get(f"/v1/users/{tg}/inventory", auth=True)["inventory"]
    _assert(inv == {}, "inventory clear failed")

    log.info("7) farm reset + verify")
    api.post(f"/v1/users/{tg}/farm/reset", {"confirm": True}, auth=True)
    farm = api.get(f"/v1/users/{tg}/farm", auth=True)["farm_minigame"]
    _assert(isinstance(farm, dict) and farm.get("field_size") == 3, "farm reset failed")

    log.info("8) list/search endpoints")
    users = api.get("/v1/users?limit=5&offset=0&sort=date_update&order=desc", auth=True)
    _assert("items" in users and "total" in users, "list users failed")
    search = api.get(f"/v1/users/search?id={tg}&limit=5&offset=0", auth=True)
    _assert(any(u["id"] == tg for u in search.get("items", [])), "search by id failed")

    log.info("9) stats endpoints")
    _assert("users" in api.get("/v1/stats/users/count", auth=True), "stats users/count failed")
    _assert("items" in api.get("/v1/stats/balances/top?limit=5", auth=True), "stats top failed")
    summary = api.get("/v1/stats/balances/summary", auth=True)
    _assert("bc" in summary and "rub" in summary, "stats summary failed")
    active = api.get("/v1/stats/active?days=7", auth=True)
    _assert(active["days"] == 7, "stats active failed")
    _assert("items" in api.get("/v1/stats/inventory/top-items?limit=10", auth=True), "stats inventory top failed")

    log.info("10) config endpoints (read)")
    _assert("value" in api.get("/v1/config/minecraft_goods", auth=True), "config minecraft_goods read failed")
    _assert("value" in api.get("/v1/config/mini_game_farm", auth=True), "config mini_game_farm read failed")

    if args.write_config:
        log.warning("write-config enabled: will modify singletons")
        goods_before = api.get("/v1/config/minecraft_goods", auth=True)["value"]
        farm_before = api.get("/v1/config/mini_game_farm", auth=True)["value"]

        # Safe no-op-ish writes: put back same payloads, then patch delete non-existent item (should be ok)
        api.put("/v1/config/minecraft_goods", goods_before, auth=True)
        api.put("/v1/config/mini_game_farm", farm_before, auth=True)
        try:
            api.patch(
                "/v1/config/minecraft_goods",
                {"op": "delete_item", "category_id": "__no__", "item_id": "__no__"},
                auth=True,
            )
        except RuntimeError:
            # expected: category not found
            pass

    log.info("OK: all checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        logging.getLogger("api_smoke_test").exception("FAILED: %s", e)
        raise

