import logging
import sys
from aiogram import Bot
from aiogram.enums import ParseMode
import os

import requests

from config import (
    ADD_CASTOM_TASK_THREAD_ID,
    ADD_CASTOM_TECHNOLOGY_THREAD_ID,
    DUPLICATES_THREAD_ID,
    LOGS_THEME_ID,
    SUPERGROUP_CHAT_ID,
)
from kbds.inline import get_callback_btns

logger = logging.getLogger(__name__)


class NotificationManager:
    chat_id = SUPERGROUP_CHAT_ID

    logs_chat_id = LOGS_THEME_ID
    task_chat_id = ADD_CASTOM_TASK_THREAD_ID
    techn_chat_id = ADD_CASTOM_TECHNOLOGY_THREAD_ID
    duplicates_chat_id = DUPLICATES_THREAD_ID

    def set_data(self, bot, base_level=None):
        if base_level is None:
            base_level = "info"

        self.bot = bot
        self.base_level = base_level

    async def send_message_admins(self, text, message_thread_id, btns=None, sizes=(1,)):
        "отправляет ответы в тг"
        try:

            formatted_message = f"{text}"

            if btns is None:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=formatted_message,
                    message_thread_id=message_thread_id,
                    parse_mode=ParseMode.HTML,
                )
            else:
                kbds = get_callback_btns(btns=btns, sizes=sizes)

                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=formatted_message,
                    message_thread_id=message_thread_id,
                    parse_mode=ParseMode.HTML,
                    reply_markup=kbds,
                )
        except Exception as e:
            logger.exception(f"Ошибка отправки сообщения в тг в Telegram: {e}")

    def add_log_level(self, text, level=None):
        if level is None:
            level = self.base_level

        return f"<b>{level.upper()}</b>\n{text}"

    async def send_log(self, text, level=None):
        "отправляет логи в тг"
        await self.send_message_admins(
            self.add_log_level(text, level), self.logs_chat_id
        )

    async def send_texn(self, text, btns=None, sizes=None):
        "отправляет технологии в тг"
        await self.send_message_admins(text, self.techn_chat_id, btns=btns, sizes=sizes)

    async def send_task(self, text, btns=None, sizes=None):
        "отправляет задачи в тг"
        await self.send_message_admins(text, self.task_chat_id, btns=btns, sizes=sizes)

    async def send_duplicates(self, text, btns=None, sizes=None):
        "отправляет дубликаты в тг"
        await self.send_message_admins(text, self.duplicates_chat_id, btns=btns, sizes=sizes)

    def send_sync_log(self, text: str, level=None):
        """
        Отправляет синхронное сообщение в тему супергруппы
        """

        url = f"https://api.telegram.org/bot{os.getenv("TOKEN")}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "message_thread_id": self.logs_chat_id,
            "text": self.add_log_level(text, level),
            "parse_mode": "HTML",
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code != 200:
                logger.error(f"Ошибка отправки лога: {response.text}")
        except Exception as e:
            logger.exception(f"Не удалось отправить лог: {e}")


tg_manager = NotificationManager()
