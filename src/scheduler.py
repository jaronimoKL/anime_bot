# src/scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnimeUpdateScheduler:
    def __init__(self, anime_service, bot):
        self.anime_service = anime_service
        self.bot = bot
        self.is_running = False


    async def update_anime_episodes_task(self):
        """Фоновая задача для обновления количества эпизодов"""
        while self.is_running:
            try:
                logger.info("Начинаем автоматическое обновление количества эпизодов...")

                # Обновляем только количество эпизодов для онгоингов
                shikimori_updated = await self._update_episodes_for_source("shikimori")
                mal_updated = await self._update_episodes_for_source("mal")

                logger.info(f"Автоматическое обновление завершено. "
                            f"Shikimori: {shikimori_updated}, MAL: {mal_updated}")

                # Ждем 12 часов до следующего обновления
                await asyncio.sleep(12 * 60 * 60)  # 12 часов в секундах

            except Exception as e:
                logger.error(f"Ошибка в фоновой задаче обновления: {e}")
                # Ждем 1 час перед повторной попыткой
                await asyncio.sleep(60 * 60)


    async def _update_episodes_for_source(self, source: str) -> int:
        """Обновление количества эпизодов и статусов для конкретного источника"""
        try:
            updated_count = 0
            finished_anime_list = []

            if source == "shikimori":
                from src.parsers.shikimori import get_ongoing_anime_async

                animes_data = await get_ongoing_anime_async(limit=100, page=1)

                for anime_data in animes_data:
                    try:
                        existing_anime = await self.anime_service.get_anime_by_source_and_id(source, anime_data["id"])

                        if existing_anime:
                            was_ongoing = existing_anime.status == "ongoing"
                            updated = False

                            new_episodes_aired = anime_data.get("episodes_aired")
                            if (new_episodes_aired is not None and
                                    new_episodes_aired != existing_anime.episodes_aired):
                                existing_anime.episodes_aired = new_episodes_aired
                                updated = True

                            new_status = anime_data.get("status")
                            if new_status and new_status != existing_anime.status:
                                if was_ongoing and new_status in ["released", "completed"]:
                                    finished_anime_list.append(existing_anime)
                                    logger.info(f"Аниме завершено: {existing_anime.title}")
                                    # Здесь будет функцию для уведомления подписчиков
                                    # await self._notify_subscribers_about_finish(existing_anime)
                                # === КОНЕЦ ДОБАВЛЕНИЯ ===
                                existing_anime.status = new_status
                                updated = True

                            new_episodes_total = anime_data.get("episodes")
                            if (new_episodes_total is not None and
                                    new_episodes_total != existing_anime.episodes):
                                existing_anime.episodes = new_episodes_total
                                updated = True

                            if updated:
                                existing_anime.updated_at = datetime.utcnow()
                                await self.anime_service.db.commit()  # Предполагается, что у anime_service есть атрибут db
                                updated_count += 1

                    except Exception as e:
                        logger.error(f"Ошибка обновления эпизодов для аниме из {source}: {e}")

            logger.info(f"Обновление для {source} завершено. Обновлено записей: {updated_count}")

            return updated_count
        except Exception as e:
            logger.error(f"Ошибка в _update_episodes_for_source для {source}: {e}")
            return 0


    async def notify_subscribers_about_new_episodes(self, anime, old_episodes_aired, new_episodes_aired):
        """Уведомление подписчиков о новых сериях"""
        try:
            # Получаем список подписчиков
            subscribers = await self.anime_service.get_anime_subscribers(anime.id)

            if not subscribers:
                return

            # Формируем сообщение
            message_text = f"🔔 *Новые серии!*\n\n"
            message_text += f"🎬 *{anime.title}*\n"
            message_text += f"📺 Вышло серий: {old_episodes_aired} → {new_episodes_aired}\n\n"
            message_text += "Проверьте, может уже можно смотреть! 🍿"

            # Отправляем уведомления всем подписчикам
            for user_id in subscribers:
                try:
                    await self.bot.send_message(
                        user_id,
                        message_text,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

            logger.info(f"Отправлено уведомлений о новых сериях для {anime.title}: {len(subscribers)} пользователей")

        except Exception as e:
            logger.error(f"Ошибка при уведомлении подписчиков об аниме {anime.id}: {e}")


    def start(self):
        """Запуск планировщика"""
        self.is_running = True
        # Запускаем задачу в фоне
        asyncio.create_task(self.update_anime_episodes_task())


    def stop(self):
        """Остановка планировщика"""
        self.is_running = False