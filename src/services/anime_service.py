from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
import json
import logging
from src.database.db import SessionLocal
from src.models.anime import Anime
import asyncio

logger = logging.getLogger(__name__)

class AnimeService:
    def __init__(self):
        # Создаем сессию БД при инициализации
        self.db = SessionLocal()

    async def get_or_create_anime(self, anime_data: dict) -> Anime:
        """Получить аниме из БД или создать новую запись с полной информацией"""
        try:
            source = anime_data.get('source', 'unknown')
            source_id = anime_data.get('id')
            title = anime_data.get('title')

            # Ищем по source + source_id или по title
            anime = None
            if source and source_id:
                result = await self.db.execute(
                    select(Anime).filter(
                        and_(Anime.source == source, Anime.source_id == str(source_id))
                    )
                )
                anime = result.scalar()

            if not anime and title:
                result = await self.db.execute(
                    select(Anime).filter(Anime.title == title)
                )
                anime = result.scalar()

            if not anime:
                # Создаем новое аниме
                anime = Anime(
                    title=title,
                    english_title=anime_data.get('english_title'),
                    japanese_title=anime_data.get('japanese_title'),
                    synonyms=anime_data.get('synonyms'), # Хранится как строка
                    source=source,
                    source_id=str(source_id) if source_id else None,
                    url=anime_data.get('url'),
                    animego_url=anime_data.get('animego_url'),
                    type=anime_data.get('type'),
                    status=anime_data.get('status', 'ongoing'),
                    episodes=anime_data.get('episodes'),
                    episodes_aired=anime_data.get('episodes_aired'),
                    score=float(anime_data.get('score')) if anime_data.get('score') else None,
                    aired_on=anime_data.get('aired_on'),
                    released_on=anime_data.get('released_on'),
                    image_url=anime_data.get('image_url'),
                    genres=anime_data.get('genres'), # Хранится как строка
                    duration=anime_data.get('duration'),
                    description=anime_data.get('description'),
                    created_at=anime_data.get('created_at', datetime.utcnow()),
                    updated_at=anime_data.get('updated_at', datetime.utcnow())
                )
                self.db.add(anime)
                await self.db.commit()
                await self.db.refresh(anime)
                logger.info(f"Создано новое аниме в БД: {title}")
            else:
                # Обновляем ТОЛЬКО количество эпизодов и статус для существующего аниме
                updated = False
                if 'episodes_aired' in anime_data and anime_data['episodes_aired'] is not None:
                    if anime_data['episodes_aired'] != anime.episodes_aired:
                        anime.episodes_aired = anime_data['episodes_aired']
                        updated = True
                        logger.info(f"Обновлены эпизоды для аниме: {title} ({anime.episodes_aired})")

                if 'status' in anime_data and anime_data['status'] is not None:
                    if anime_data['status'] != anime.status:
                        anime.status = anime_data['status']
                        updated = True
                        logger.info(f"Обновлен статус для аниме: {title} ({anime.status})")

                # Также можно обновить общее количество эпизодов
                if 'episodes' in anime_data and anime_data['episodes'] is not None:
                    if anime_data['episodes'] != anime.episodes:
                        anime.episodes = anime_data['episodes']
                        updated = True

                if updated:
                    anime.updated_at = datetime.utcnow()
                    await self.db.commit()
                    await self.db.refresh(anime)

            return anime
        except Exception as e:
            logger.error(f"Ошибка при работе с аниме в БД: {e}")
            await self.db.rollback()
            raise

    async def update_all_ongoing_from_source(self, source: str, force_update: bool = False) -> int:
        """Обновить все онгоинги из указанного источника"""
        try:
            logger.info(f"Начинаем обновление онгоингов из {source}")

            added_count = 0
            updated_count = 0

            if source == "shikimori":
                # Для Shikimori используем асинхронный подход
                from src.parsers.shikimori import get_ongoing_anime_count_async, get_ongoing_anime_async

                total_anime_count = await get_ongoing_anime_count_async()
                total_pages = min((total_anime_count // 50) + 1, 20)

                logger.info(f"Будет загружено {total_pages} страниц из Shikimori")

                # Создаем список задач для параллельной загрузки всех страниц
                tasks = []
                for page in range(1, total_pages + 1):
                    tasks.append(get_ongoing_anime_async(limit=50, page=page))

                # Выполняем все запросы параллельно
                all_pages_data = await asyncio.gather(*tasks)

                # Обрабатываем все полученные данные
                for page_data in all_pages_data:
                    if page_data:
                        for anime_data in page_data:
                            try:
                                # Добавляем animego_url к полным данным
                                anime_data['animego_url'] = self._get_animego_url(anime_data.get('title', ''))
                                # Используем готовый метод для создания/обновления
                                await self.get_or_create_anime(anime_data)
                                added_count += 1 # Упрощенный подсчет, т.к. get_or_create_anime сам решает создать или обновить
                            except Exception as e:
                                logger.error(f"Ошибка обработки аниме {anime_data.get('title')}: {e}")

            elif source == "mal":
                # Для MAL используем асинхронный подход
                from src.parsers.mal import fetch_all_ongoing_anime_mal # Убедитесь, что путь правильный

                try:
                    all_anime_data, last_visible_page, total_items = await fetch_all_ongoing_anime_mal()

                    logger.info(f"Загружено {len(all_anime_data)} аниме из MyAnimeList")

                    for anime_data_tuple in all_anime_data:
                        # fetch_all_ongoing_anime_mal возвращает (data, last_page, total), где data - список
                        # anime_data_tuple - это (anime_dict, _, _)
                        anime_data = anime_data_tuple[0] if isinstance(anime_data_tuple, tuple) else anime_data_tuple

                        try:
                            # Добавляем информацию для полного сохранения
                            full_anime_data = {
                                'source': 'mal',
                                'id': anime_data["id"],
                                'title': anime_data["title"],
                                'url': anime_data["url"],
                                'animego_url': self._get_animego_url(anime_data["title"])
                            }

                            # Используем готовый метод для создания/обновления
                            await self.get_or_create_anime(full_anime_data)
                            added_count += 1 # Упрощенный подсчет

                        except Exception as e:
                            logger.error(f"Ошибка обработки аниме {anime_data.get('title')}: {e}")

                except Exception as e:
                    logger.error(f"Ошибка загрузки из MyAnimeList: {e}")

            logger.info(f"Обновление из {source} завершено: добавлено/обновлено {added_count}")
            return added_count

        except Exception as e:
            logger.error(f"Ошибка при обновлении из {source}: {e}")
            return 0

    async def get_anime_by_title(self, title: str) -> Anime:
        """Получить аниме по названию"""
        try:
            result = await self.db.execute(select(Anime).filter(Anime.title == title))
            return result.scalar()
        except Exception as e:
            logger.error(f"Ошибка получения аниме по названию: {e}")
            return None

    async def get_anime_by_source_and_id(self, source: str, source_id: str) -> Anime:
        """Получить аниме по источнику и ID"""
        try:
            result = await self.db.execute(
                select(Anime).filter(
                    and_(Anime.source == source, Anime.source_id == str(source_id))
                )
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Ошибка получения аниме из БД: {e}")
            return None

    async def get_ongoing_anime(self, limit: int = 10, offset: int = 0):
        """Получить список онгоингов"""
        try:
            result = await self.db.execute(
                select(Anime).filter(Anime.status == 'ongoing').offset(offset).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка получения онгоингов: {e}")
            return []

    async def get_ongoing_count_from_database(self, source: str) -> int:
        """Получить количество онгоингов из базы данных"""
        try:
            result = await self.db.execute(
                select(func.count(Anime.id)).filter(
                    and_(Anime.source == source, Anime.status == 'ongoing')
                )
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Ошибка подсчета онгоингов в БД: {e}")
            return 0

    async def get_ongoing_from_database(self, source: str, limit: int = 10, offset: int = 0):
        """Получить онгоинги из базы данных"""
        try:
            result = await self.db.execute(
                select(Anime).filter(
                    and_(Anime.source == source, Anime.status == 'ongoing')
                ).offset(offset).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Ошибка получения онгоингов из БД: {e}")
            return []

    def _get_animego_url(self, title: str) -> str:
        """Получить ссылку на AnimeGO (вынесено в отдельный метод)"""
        try:
            from src.utils.animego_link import get_anime_link_from_title
            return get_anime_link_from_title(title)
        except:
            return None

    async def close(self):
        """Закрыть сессию БД"""
        await self.db.close()

# Глобальный экземпляр сервиса (если используется так)
anime_service = AnimeService()