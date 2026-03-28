from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class BookModel(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    year = Column(Integer, nullable=False)