from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid6

from database import Base


class BookModel(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
