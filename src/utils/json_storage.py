import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from filelock import FileLock
import asyncio


class JsonTable:
    """
    Универсальный класс для работы с JSON-таблицей.
    - Поддерживает дефолтные значения
    - Защищён от крашей атомарной записью (tmp → os.replace)
    - FileLock защищает от одновременной записи из разных процессов
    - asyncio.Lock защищает от гонок внутри одного процесса
    """

    def __init__(
        self,
        path: str | Path,
        defaults: Optional[Dict[str, Any]] = None,
        indent: int = 2,
    ):
        self.path = Path(path)
        self.defaults = defaults or {}
        self.indent = indent

        self._cache: Dict[str, Any] = {}
        self._file_lock_path = str(self.path) + ".lockfile"
        self._lock = asyncio.Lock()

        # Инициализация файла
        if not self.path.exists():
            self._cache = dict(self.defaults)
            self._atomic_write(self._cache)
        else:
            self._cache = self._load_from_disk()

    # ------------------------
    # Внутренние методы
    # ------------------------

    def _load_from_disk(self) -> Dict[str, Any]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return dict(self.defaults)

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        """Записывает JSON атомарно (через tmp-файл)."""
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=self.indent)
        os.replace(tmp_path, self.path)

    # ------------------------
    # API
    # ------------------------

    async def get(self, key: str) -> Any:
        async with self._lock:
            return self._cache.get(key, self.defaults.get(key))

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            with FileLock(self._file_lock_path):
                # читаем с диска свежую версию
                disk = self._load_from_disk()
                disk[key] = value
                self._cache = dict(disk)
                self._atomic_write(disk)

    async def delete(self, key: str) -> None:
        async with self._lock:
            with FileLock(self._file_lock_path):
                disk = self._load_from_disk()
                if key in disk:
                    del disk[key]
                self._cache = dict(disk)
                self._atomic_write(disk)

    async def replace_all(self, new_data: Dict[str, Any]) -> None:
        async with self._lock:
            with FileLock(self._file_lock_path):
                self._cache = dict(new_data)
                self._atomic_write(new_data)

    async def all(self) -> Dict[str, Any]:
        async with self._lock:
            return dict(self._cache)

    async def clear(self) -> None:
        """Очистить таблицу, записав только дефолты."""
        await self.replace_all(dict(self.defaults))
