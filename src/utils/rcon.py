import asyncio
import aiomcrcon
import json
# from app import logger
import logging

from config import Config
logger = logging.getLogger(__name__)

class RconManager:
    """
    Асинхронный менеджер для работы с RCON, где каждое подключение создаётся заново.
    """

    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password

    async def _send(self, command: str) -> str:
        """
        Подключается, выполняет команду и закрывает соединение.
        """
        try:
            print(f"Подключаюсь к {self.host}:{self.port}")
            async with aiomcrcon.Client(
                host=self.host,
                port=self.port,
                password=self.password
            ) as client:
                response = await client.send_cmd(command)
                # print(response)
                logger.info(f"команда в майн: {response}")
                return response[0]
                # return response[0] or "✅ Команда выполнена успешно."

        except Exception as e:
            # print(response)
            logger.exception("Ошибка при выполнении команды на серве майна")
            # return f"❌ Ошибка при выполнении команды: {e}"
            raise e

    # ------------------------
    # Методы для разных команд
    # ------------------------

    async def do_command(self, command: str) -> str:
        """
        Выполняет команду на сервере.
        """
        res = await self._send(command)
        return res

    async def give_item(self, player: str, item: str, amount: int) -> str:
        """
        Выдаёт предмет игроку.
        """
        # command = f"give {player} {item} {amount}"
        # print(88)
        data = json.dumps({"Item": {"id": f"minecraft:{item}", "Count": amount}})
        # print(data)
        command = f"execute at {player} run summon item ~ ~1 ~ {data}"

        return await self._send(command)

    async def broadcast(self, message: str) -> str:
        """
        Отправляет сообщение всем игрокам.
        """
        command = f"say {message}"
        return await self._send(command)

    async def kick(self, player: str, reason: str = "Вы были кикнуты") -> str:
        """
        Кикает игрока с сервера.
        """
        command = f"kick {player} {reason}"
        return await self._send(command)





rcon_manager = RconManager(
        host=(Config.RCON_HOST or "").strip(),
        port=(int(Config.RCON_PORT) if str(Config.RCON_PORT).isdigit() else 25575),
        password=(Config.RCON_PASSWORD or "")
    )


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def apply_rcon_settings(host: str | None = None, port: int | str | None = None, password: str | None = None) -> None:
    """
    Обновляет настройки глобального rcon_manager в оперативке (без сохранения на диск).
    """
    if host is not None:
        rcon_manager.host = str(host).strip()
    if port is not None:
        rcon_manager.port = _safe_int(port, rcon_manager.port)
    if password is not None:
        rcon_manager.password = str(password)

