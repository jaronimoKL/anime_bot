import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import logging

from src.config import DATABASE_URL
from src.database.base import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Асинхронная инициализация базы данных"""
    logger.info("Начинаем инициализацию базы данных...")
    try:
        # Явно импортируем модели ДО создания таблиц
        logger.info("Импортируем модели...")
        from src.models.anime import Anime
        from src.models.subscription import Subscription
        logger.info("Модели импортированы успешно")
        logger.info(f"Таблицы для создания: {list(Base.metadata.tables.keys())}")

        # Создаем все таблицы асинхронно
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы созданы успешно")

        # Проверяем, какие таблицы теперь есть
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            logger.info("Таблицы в базе данных: %s", tables)

    except Exception as e:
        logger.error(f"Ошибка при инициализации БД: {e}")
        import traceback
        traceback.print_exc()

async def get_db():
    """Асинхронное получение сессии БД"""
    async with SessionLocal() as session:
        yield session

# Для прямого запуска файла
if __name__ == "__main__":
    asyncio.run(init_db())