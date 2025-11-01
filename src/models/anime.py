# src/models/anime.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, BigInteger
from sqlalchemy.orm import relationship  # Опционально, если не используем связь
from src.database.base import Base


class Anime(Base):
    __tablename__ = 'anime'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    english_title = Column(String)
    japanese_title = Column(String)
    synonyms = Column(Text)

    source = Column(String, nullable=False)  # 'shikimori', 'mal', etc.
    source_id = Column(String)  # ID аниме в источнике (например, Shikimori ID)

    url = Column(String)  # URL на страницу аниме в источнике
    animego_url = Column(String)  # URL на страницу аниме на AnimeGO (если есть)

    type = Column(String)  # 'TV', 'Movie', 'OVA', etc.
    status = Column(String)  # 'ongoing', 'released', 'announced', etc.

    episodes = Column(Integer)  # Общее количество эпизодов
    episodes_aired = Column(Integer)  # Количество вышедших эпизодов

    score = Column(Float)  # Рейтинг
    aired_on = Column(DateTime)  # Дата начала выхода
    released_on = Column(DateTime)  # Дата окончания выхода

    image_url = Column(String)  # URL изображения
    genres = Column(Text)  # Жанры (хранятся как строка, например, JSON или через запятую)
    duration = Column(String)  # Длительность одного эпизода
    description = Column(Text)  # Описание

    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<Anime(id={self.id}, title='{self.title}', source='{self.source}')>"

print(f"Модель Anime зарегистрирована в metadata. Таблица: {Anime.__tablename__}")