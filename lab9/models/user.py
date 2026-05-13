import uuid6
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid6.uuid7)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)