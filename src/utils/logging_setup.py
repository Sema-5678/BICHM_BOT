# logging_setup.py
import os
import logging
import asyncio
from logging.handlers import RotatingFileHandler
from aiogram import Bot
from aiogram.enums import ParseMode

from config import log_dir

class ErrorHandler(logging.Handler):
    """Обработчик для отправки ошибок в Telegram"""
    
    def __init__(self, bot: Bot = None, enable_telegram: bool = True, SUPERGROUP_CHAT_ID=None, LOGS_THEME_ID=None):
        super().__init__()
        self.bot = bot
        self.enable_telegram = enable_telegram
        self.SUPERGROUP_CHAT_ID = SUPERGROUP_CHAT_ID
        self.LOGS_THEME_ID = LOGS_THEME_ID


    def set_bot(self, bot: Bot):
        """Установить бота для отправки сообщений"""
        self.bot = bot
        
    def set_telegram_enabled(self, enabled: bool):
        """Включить/отключить отправку в Telegram"""
        self.enable_telegram = enabled

    async def send_error_to_admin(self, error_message: str):
        """Функция для отправки ошибок админу"""
        if not self.bot or not self.enable_telegram:
            return
            
        try:
            text = f"🚨 ERROR:\n```python\n{error_message.replace('```', '3 кавычки')}```"
            await self.bot.send_message(
                chat_id=self.SUPERGROUP_CHAT_ID,
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2,
                message_thread_id=self.LOGS_THEME_ID,
            )
        except Exception:
            logging.warning("Не удалось отправить ошибку админу")

    def emit(self, record):
        if self.bot and self.enable_telegram:
            log_entry = self.format(record)
            if len(log_entry) > 4000:
                log_entry = log_entry[:4000] + "..."
            asyncio.create_task(self.send_error_to_admin(log_entry))

def setup_logging(bot: Bot = None, enable_telegram_logging: bool = False, SUPERGROUP_CHAT_ID=None, LOGS_THEME_ID=None, maxBytes= 1 * 1024 * 1024, backupCount=3):
    """Настройка логирования
    
    Args:
        bot: Экземпляр бота для отправки ошибок в Telegram
        enable_telegram_logging: Включить отправку логов в Telegram
    """
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Создаем логер
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Форматтер для сообщений
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Обработчик для записи в файл
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "bot.log"),
        maxBytes=maxBytes,
        backupCount=backupCount,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Обработчик для вывода в терминал
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    


    # Очищаем существующие обработчики и добавляем новые
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    if enable_telegram_logging:
        # Обработчик ошибок для Telegram
        error_handler = ErrorHandler(bot, enable_telegram_logging, SUPERGROUP_CHAT_ID, LOGS_THEME_ID)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    return logger



# Глобальные переменные для управления логированием
_logger_instance = None
_error_handler_instance = None

def get_logger():
    """Получить экземпляр логгера"""
    return _logger_instance

def set_telegram_logging_enabled(enabled: bool):
    """Включить/отключить отправку логов в Telegram"""
    global _error_handler_instance
    if _error_handler_instance:
        _error_handler_instance.set_telegram_enabled(enabled)

def set_bot_for_logging(bot: Bot):
    """Установить бота для логирования (полезно, если бот инициализируется позже)"""
    global _error_handler_instance
    if _error_handler_instance:
        _error_handler_instance.set_bot(bot)