from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _ensure_import_path() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    sys.path.insert(0, str(src_path))
    return repo_root


def _load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_admins_data(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"admins_ids": []}
    ids = data.get("admins_ids", [])
    if not isinstance(ids, list):
        ids = []
    out_ids: list[int] = []
    for x in ids:
        try:
            out_ids.append(int(x))
        except Exception:
            continue
    return {"admins_ids": out_ids}


async def _migrate(repo_root: Path, json_dir: Path) -> int:
    from database.engine import create_db, session_maker
    from database.orm import orm_set_singleton

    log = logging.getLogger("migrate_singletons_from_json")

    await create_db()

    mapping: list[tuple[str, Path, str]] = [
        ("admins_data", json_dir / "admins_data.json", "admins_data"),
        ("minecraft_goods", json_dir / "minecraft_goods.json", "minecraft_goods"),
        ("mini_game_farm", json_dir / "mini_game_farm.json", "mini_game_farm"),
    ]

    async with session_maker() as session:
        for key, file_path, label in mapping:
            if not file_path.exists():
                log.warning("SKIP: %s not found at %s", label, file_path)
                continue

            try:
                data = _load_json_file(file_path)
            except Exception as e:
                log.exception("FAIL: cannot read %s (%s): %s", label, file_path, e)
                continue

            if key == "admins_data":
                data = _normalize_admins_data(data)
            elif not isinstance(data, dict):
                log.error("SKIP: %s must be a JSON object at top-level, got %s", label, type(data).__name__)
                continue

            await orm_set_singleton(session, key, data)
            log.info("OK: migrated %s -> singletons[%s] (%s bytes)", label, key, file_path.stat().st_size)

    log.info("DONE")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate selected JSON singletons into SQLite (table singletons).")
    parser.add_argument(
        "--json-dir",
        default=None,
        help="Path to JSON database dir (default: ./data/json_database)",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    _setup_logging(args.verbose)
    repo_root = _ensure_import_path()

    try:
        from dotenv import find_dotenv, load_dotenv  # type: ignore
    except Exception:
        logging.getLogger("migrate_singletons_from_json").warning(
            "python-dotenv not installed; .env will not be loaded (using current process env)."
        )
    else:
        load_dotenv(find_dotenv())

    json_dir = Path(args.json_dir) if args.json_dir else (repo_root / "data" / "json_database")
    json_dir = json_dir.resolve()

    raise SystemExit(asyncio.run(_migrate(repo_root, json_dir)))


if __name__ == "__main__":
    main()

