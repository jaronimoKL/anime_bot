# src/models/subscription.py
from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey, UniqueConstraint
# from sqlalchemy.orm import relationship # Опционально, если не используем связь
from datetime import datetime
from src.database.base import Base

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    anime_id = Column(Integer, ForeignKey('anime.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Уникальное ограничение: один пользователь не может подписаться на одно аниме дважды
    __table_args__ = (UniqueConstraint('user_id', 'anime_id', name='_user_anime_uc'),)

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, anime_id={self.anime_id})>"

print(f"Модель Subscription зарегистрирована в metadata. Таблица: {Subscription.__tablename__}")