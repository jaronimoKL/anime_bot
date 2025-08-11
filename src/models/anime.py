from sqlalchemy import Column, Integer, String

from ..database import Base


class Anime(Base):
    __tablename__ = 'anime'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    status = Column(String)
    url = Column(String)