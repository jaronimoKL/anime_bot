from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import foreign

from ..database import Base


class Subscription(Base):
    __tablename__ = 'subscription'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    anime_id = Column(Integer, ForeignKey('anime.id'))