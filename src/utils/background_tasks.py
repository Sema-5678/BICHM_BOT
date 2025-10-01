import asyncio
from decimal import Decimal
from utils.json_engine import get_all_users, update_user_data
from config import  INTEREST_CREDIT_RATE_day, INTEREST_DEPOSIT_RATE_day, CREDIT_INTEREST_RATE_TIME, INTEREST_CREDIT_RATE, CREDIT_RATING_DECREASE_PER_DAY
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

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

                    if user_data['max_loan'] > Decimal('0'):
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




            
class InterestScheduler:
    def __init__(self, timezone: str = "Europe/Moscow", jobs: list = None):
        self.scheduler: AsyncIOScheduler | None = None
        self.timezone = timezone
        self.jobs = jobs

    async def start(self):
        if self.scheduler and self.scheduler.running:
            return  # уже запущен

        self.scheduler = AsyncIOScheduler(timezone=self.timezone)
        if self.jobs:
            for job in self.jobs:
                self.scheduler.add_job(**job)
        else:
            logger.warning("Нет задач для запуска")
            return
        # self.scheduler.add_job(
        #     process_interest,
        #     "cron",
        #     hour=10,
        #     minute=0,
        # )
        self.scheduler.start()
        logger.info("✅ InterestScheduler запущен")

    async def stop(self):
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("🛑 InterestScheduler остановлен")


jobs = [
    {
        "func": process_interest,
        "trigger": "cron",
        "hour": CREDIT_INTEREST_RATE_TIME[0],
        "minute": CREDIT_INTEREST_RATE_TIME[1],
    }
]

interest_scheduler = InterestScheduler(jobs=jobs)