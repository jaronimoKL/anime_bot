import asyncio
import logging
from aiogram import Bot, Dispatcher

from src.scheduler import AnimeUpdateScheduler
from src.config import BOT_TOKEN
from src.handlers.start import router as start_router
from src.handlers.anime_list import router as anime_router
from src.handlers.subscriptions import router as subscriptions_router
from src.services.anime_service import anime_service

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN пуст. Проверь .env / config.py")
        return

    logger.info("Инициализация бота...")

    try:
        from src.database import init_db
        logger.info("Начинаем инициализацию базы данных...")
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.exception("Ошибка инициализации БД: %s", e)
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(anime_router)
    dp.include_router(subscriptions_router)

    scheduler = AnimeUpdateScheduler(anime_service, bot)
    scheduler.start()

    logger.info("Бот запущен. Ожидание команд...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.stop()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())

