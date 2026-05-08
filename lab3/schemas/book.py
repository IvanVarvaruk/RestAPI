from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List

class BookBase(BaseModel):
    title: str
    author: str
    description: Optional[str] = None
    status: str
    year: int

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class PaginatedBooks(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[Book]
    next_cursor: Optional[UUID] = None