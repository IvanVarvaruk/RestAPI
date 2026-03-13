from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from enum import Enum
from typing import Optional

class BookStatus(str, Enum):
    AVAILABLE = "Available in library"
    ISSUED = "Issued to someone"

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    author: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: BookStatus = BookStatus.AVAILABLE
    year: int = Field(..., gt=0, lt=2100)

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: UUID