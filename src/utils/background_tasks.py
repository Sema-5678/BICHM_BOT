import asyncio
from decimal import Decimal
import os
import random
from utils.json_engine import get_all_users, update_user_data, get_farm_data, update_farm_data
import random
from config import (
    INTEREST_CREDIT_RATE_day, 
    INTEREST_DEPOSIT_RATE_day, 
    CREDIT_INTEREST_RATE_TIME, 
    INTEREST_CREDIT_RATE, 
    CREDIT_RATING_DECREASE_PER_DAY,
    chats_bonuses
)
import logging
from aiogram import Bot
from datetime import date
from calendar import monthrange

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


async def process_interest():
    logger.info("Начисляет проценты всем пользователям")
    users = get_all_users()

    today = datetime.today().date()

    for user_id, user_data in users:
        try:
            if (user_data['max_loan'] + user_data['deposit']) > Decimal('0') and user_data["last_interest_date"] != "None":
                # if :
                last_date = datetime.strptime(user_data["last_interest_date"], "%Y-%m-%d").date()

                # Догоним пропущенные дни
                while last_date < today:

                    if user_data['debt'] > Decimal('0'):
                        user_data['debt'] += user_data['max_loan'] * (INTEREST_CREDIT_RATE_day)
                        user_data['credit_rating'] = max(0, user_data['credit_rating'] - CREDIT_RATING_DECREASE_PER_DAY)
                    user_data['max_loan'] = user_data['debt']
                    
                    # Начисляем проценты по вкладам на защищённую базу
                    # deposit = user_data['deposit']
                    if user_data['min_deposit'] > Decimal('0'):
                        # Умножаем Decimal на Decimal
                        user_data['deposit'] += user_data['min_deposit'] * (INTEREST_DEPOSIT_RATE_day)
                    user_data['min_deposit'] = user_data['deposit']

                    last_date += timedelta(days=1)
                    
            user_data["last_interest_date"] = today.strftime("%Y-%m-%d")
            update_user_data(user_id, user_data)

        except Exception as e:
                logger.exception(f"Ошибка при обработке пользователя {user_id}: {e}")
                continue




            


async def send_monthly_reset_notification(bot: Bot):
    """Отправляет уведомление о скором обнулении баланса в чаты из списка chats_bonuses"""
    try:
        today = date.today()
        _, last_day = monthrange(today.year, today.month)
        days_until_reset = last_day - today.day
        
        message = None
        
        if days_until_reset == 5:  # 5 дней до конца месяца
            message = (
                "⚠️ *ВНИМАНИЕ!* ⚠️\n\n"
                "До конца месяца осталось всего 5 дней!\n"
                "В полночь 1-го числа все балансы игроков будут обнулены, а данные сезона Minecraft сброшены.\n\n"
                "Успейте потратить свои средства до конца месяца!"
            )
        elif days_until_reset == 0:  # 1 день до конца месяца
            message = (
                "🔥 *ПОСЛЕДНИЙ ДЕНЬ МЕСЯЦА!* 🔥\n\n"
                "До обнуления балансов осталось меньше суток!\n"
                "В полночь все неиспользованные деньги сгорят, а данные сезона Minecraft будут сброшены.\n\n"
                "Срочно тратьте все свои сбережения! Покупайте предметы, улучшения - всё, что угодно!\n"
                "После полуночи эти деньги перестанут существовать! 💸"
            )
        
        if message:
            for chat_id in chats_bonuses.keys():
                try:
                    await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                    logger.info(f"Отправлено уведомление о скором обнулении в чат {chat_id}")
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление в чат {chat_id}: {e}")
        
    except Exception as e:
        logger.exception(f"Ошибка при отправке уведомлений о скором обнулении: {e}")


async def reset_minecraft_season():
    """
    Сбрасывает данные сезона Minecraft, баланс пользователей
    и обновляет поле мини-фермы
    """
    logger.info("Сбрасываю данные сезона Minecraft и баланс для всех пользователей")

    # Обновляем поле мини-фермы
    # try:
    #     farm_data = get_farm_data()
    #     if farm_data and 'fields' in farm_data and farm_data['fields'] and 'curr_field' in farm_data:
    #         # Выбираем случайное поле из доступных
    #         new_field = random.choice(farm_data['fields'])
    #         farm_data['curr_field'] = new_field
    #         update_farm_data(farm_data)
    #         logger.info("Mini-farm field updated successfully")
    # except Exception as e:
    #     logger.error(f"Error updating mini-farm field: {e}")
    
    # Сбрасываем баланс пользователей
    users = get_all_users()
    
    for index, (user_id, user_data) in enumerate(users):
        try:
            # Сбрасываем данные сезона
            if 'minecraft_goods_count_season' in user_data:
                user_data['minecraft_goods_count_season'] = {}
            
            # Обнуляем баланс
            user_data['balance'] = '0.00'
            # user_data['rub_balance'] = '0.00'
            
            # Сохраняем изменения
            update_user_data(user_id, user_data)

            if index % 10 == 0:
                await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.exception(f"Ошибка при сбросе данных сезона для пользователя {user_id}: {e}")
            continue

jobs = [
    {
        "func": process_interest,
        "trigger": "cron",
        "hour": CREDIT_INTEREST_RATE_TIME[0],
        "minute": CREDIT_INTEREST_RATE_TIME[1],
        "misfire_grace_time": 3600,
        "max_instances": 1,
        "coalesce": True,
    },
    {
        "func": reset_minecraft_season,
        "trigger": "cron",
        "day": "last",  # Последний день месяца
        "hour": 23,
        "minute": 59,
        "misfire_grace_time": 3600,
        "max_instances": 1,
        "coalesce": True,
    },
    {
        "func": send_monthly_reset_notification,
        "need_bot": True,
        "trigger": "cron",
        "hour": 12,  # В полдень
        "misfire_grace_time": 3600,
        "max_instances": 1,
        "coalesce": True,
    },
]



class InterestScheduler:
    def __init__(self, timezone = "Europe/Moscow", jobs: list = None):
        self.scheduler: AsyncIOScheduler | None = None
        self.timezone = timezone
        self.jobs = jobs

    async def add_bot(self, bot):
        self.bot = bot

    async def start(self):
        if self.scheduler and self.scheduler.running:
            return  # уже запущен

        self.scheduler = AsyncIOScheduler(timezone=self.timezone)
        if self.jobs:
            for job in self.jobs:
                need_bot = job.get("need_bot")
                if need_bot:
                    if not hasattr(self, "bot"):
                        raise AttributeError(
                            "бот не передан в Scheduler, но он нужен для работы"
                        )
                    else:
                        del job["need_bot"]
                        kwargs_list = job.get("kwargs", {})
                        kwargs_list["bot"] = self.bot
                        job["kwargs"] = kwargs_list

                self.scheduler.add_job(**job)
        else:
            logger.warning("Нет задач для запуска")
            return

        self.scheduler.start()
        logger.info("✅ InterestScheduler запущен")

    async def stop(self):
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("🛑 InterestScheduler остановлен")


interest_scheduler = InterestScheduler(jobs=jobs)