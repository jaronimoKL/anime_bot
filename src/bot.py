"""
Файл: bot.py
Назначение: точка входа для запуска Telegram-бота.
Как использовать: положи рядом с config.py и папкой handlers/
Запуск: python bot.py
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

# если у тебя есть config.py, который читает .env:
from config import BOT_TOKEN  # <- убедись, что в config.py переменная BOT_TOKEN

# импортируем роутеры/хэндлеры (примеры имен)
# если у тебя структура src/handlers/... — укажи правильный путь, например: from src.handlers import start, anime_list
# здесь пример для handlers в корне проекта: package handlers с router-объектами
try:
    from handlers.start import router as start_router
    from handlers.anime_list import router as anime_router
except Exception:
    # альтернативный путь, если у тебя пакет src.handlers
    from src.handlers.start import router as start_router
    from src.handlers.anime_list import router as anime_router

# Логирование в консоль
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN пуст. Проверь .env / config.py")
        return

    logger.info("Инициализация бота...")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # включаем роутеры
    dp.include_router(start_router)
    dp.include_router(anime_router)

    # если есть инициализация БД, вызывай её здесь; пример:
    try:
        # from database import init_db
        # init_db()
        pass
    except Exception as e:
        logger.exception("Ошибка инициализации БД: %s", e)

    logger.info("Бот запущен. Ожидание команд...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
