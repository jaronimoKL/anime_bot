# src/services/subscription_service.py
from sqlalchemy import select, and_
from src.models.subscription import Subscription
from src.models.anime import Anime
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SubscriptionsService:
    def __init__(self, db_session):
        self.db = db_session # Сессия передается извне

    async def subscribe_user_to_anime(self, user_id: int, anime_id: int) -> bool:
        """Подписка пользователя на аниме"""
        try:
            # Проверяем, существует ли аниме
            result = await self.db.execute(select(Anime).filter(Anime.id == anime_id))
            anime = result.scalar()
            if not anime:
                return False

            # Проверяем, есть ли уже подписка
            result = await self.db.execute(
                select(Subscription).filter(
                    and_(Subscription.user_id == user_id, Subscription.anime_id == anime_id)
                )
            )
            existing_subscription = result.scalar()

            if existing_subscription:
                return False  # Уже подписан

            # Создаем новую подписку
            subscription = Subscription(user_id=user_id, anime_id=anime_id)
            self.db.add(subscription)
            await self.db.commit()
            logger.info(f"Пользователь {user_id} подписался на аниме {anime_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подписки пользователя {user_id} на аниме {anime_id}: {e}")
            await self.db.rollback()
            return False

    async def unsubscribe_user_from_anime(self, user_id: int, anime_id: int) -> bool:
        """Отписка пользователя от аниме"""
        try:
            result = await self.db.execute(
                select(Subscription).filter(
                    and_(Subscription.user_id == user_id, Subscription.anime_id == anime_id)
                )
            )
            subscription = result.scalar()

            if not subscription:
                return False  # Не был подписан

            await self.db.delete(subscription)
            await self.db.commit()
            logger.info(f"Пользователь {user_id} отписался от аниме {anime_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отписки пользователя {user_id} от аниме {anime_id}: {e}")
            await self.db.rollback()
            return False

    async def get_user_subscriptions(self, user_id: int) -> list:
        """Получение списка подписок пользователя"""
        try:
            result = await self.db.execute(
                select(Anime).join(Subscription).filter(Subscription.user_id == user_id)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка получения подписок пользователя {user_id}: {e}")
            return []

    async def is_user_subscribed(self, user_id: int, anime_id: int) -> bool:
        """Проверка, подписан ли пользователь на аниме"""
        try:
            result = await self.db.execute(
                select(Subscription).filter(
                    and_(Subscription.user_id == user_id, Subscription.anime_id == anime_id)
                )
            )
            return result.scalar() is not None
        except Exception as e:
            logger.error(f"Ошибка проверки подписки пользователя {user_id} на аниме {anime_id}: {e}")
            return False

    async def get_anime_subscribers(self, anime_id: int) -> list:
        """Получение списка подписчиков на аниме (для уведомлений)"""
        try:
            result = await self.db.execute(
                select(Subscription.user_id).filter(Subscription.anime_id == anime_id)
            )
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения подписчиков аниме {anime_id}: {e}")
            return []