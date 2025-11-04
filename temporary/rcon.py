# import asyncio
# import struct
# import logging

# import logging

# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



# class RconError(Exception):
#     """Общее исключение для ошибок RCON."""


# class AuthenticationError(RconError):
#     """Ошибка аутентификации."""


# class RconClient:
#     """Асинхронный клиент для RCON протокола Minecraft."""

#     def __init__(self, host: str, port: int, password: str, timeout: float = 5.0):
#         self.host = host
#         self.port = port
#         self.password = password
#         self.timeout = timeout
#         self._reader: asyncio.StreamReader | None = None
#         self._writer: asyncio.StreamWriter | None = None
#         self._req_id = 0
#         self._log = logging.getLogger(__name__)

#     async def __aenter__(self):
#         await self.connect()
#         return self

#     async def __aexit__(self, exc_type, exc, tb):
#         await self.close()

#     async def connect(self):
#         """Подключается к серверу RCON и выполняет аутентификацию."""
#         try:
#             self._reader, self._writer = await asyncio.wait_for(
#                 asyncio.open_connection(self.host, self.port), timeout=self.timeout
#             )
#         except (OSError, asyncio.TimeoutError) as e:
#             raise RconError(f"Не удалось подключиться к {self.host}:{self.port}: {e}") from e

#         if not await self._authenticate():
#             raise AuthenticationError("Неверный пароль RCON")

#     async def close(self):
#         """Закрывает соединение."""
#         if self._writer:
#             self._writer.close()
#             await self._writer.wait_closed()
#             self._writer = None
#             self._reader = None

#     async def _authenticate(self) -> bool:
#         """Аутентификация на сервере."""
#         resp = await self._send_packet(self.password, out_type=3)  # 3 = SERVERDATA_AUTH
#         return resp.get("request_id") == self._req_id

#     async def command(self, cmd: str) -> str:
#         """Отправляет команду на сервер и возвращает результат."""
#         resp = await self._send_packet(cmd, out_type=2)  # 2 = SERVERDATA_EXECCOMMAND
#         return resp.get("body", "")

#     async def _send_packet(self, payload: str, out_type: int) -> dict:
#         """Формирует и отправляет пакет."""
#         if not self._writer or not self._reader:
#             raise RconError("Нет активного соединения")

#         self._req_id += 1
#         data = payload.encode("utf8")
#         packet = struct.pack("<iii", len(data) + 10, self._req_id, out_type) + data + b"\x00\x00"

#         self._writer.write(packet)
#         await self._writer.drain()

#         return await self._read_response()

#     async def _read_response(self) -> dict:
#         """Читает ответ от сервера."""
#         raw_len = await self._reader.readexactly(4)
#         (length,) = struct.unpack("<i", raw_len)
#         data = await self._reader.readexactly(length)
#         req_id, resp_type = struct.unpack("<ii", data[:8])
#         body = data[8:-2].decode("utf8", errors="replace")
#         return {"request_id": req_id, "type": resp_type, "body": body}







# # import asyncio
# # from rcon import RconClient


# async def main():
#     async with RconClient("185.9.145.7", 25575, 'asr-d5211') as rcon:
#         resp = await rcon.command("list")  # Покажет список игроков
#         print("Ответ:", resp)


# if __name__ == "__main__":
#     asyncio.run(main())




















from mcrcon import MCRcon

# Настройки RCON
RCON_HOST = "185.9.145.7"   # IP твоего сервера
RCON_PORT = 25575          # порт RCON (из server.properties)

RCON_PORT = 42385
RCON_PASSWORD = "asr-d5211"

# Имя игрока и предмет
PLAYER_NAME = "Raven79rus"      # имя игрока на сервере
ITEM = "minecraft:carrot"   # ID предмета
AMOUNT = 3                 # количество

# Подключаемся и выполняем команду
with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
    command = f"give {PLAYER_NAME} {ITEM} {AMOUNT}"
    response = mcr.command(command)
    print(response)