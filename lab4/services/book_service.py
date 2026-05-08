from repository.book_repository import BookRepository
from schemas.book import BookCreate
from uuid import UUID

class BookService:
    def __init__(self, db):
        self.repo = BookRepository(db)

    async def list_books(self, limit: int, offset: int, status: str, author: str, sort_by: str, cursor: UUID = None):
        return await self.repo.get_all(limit, offset, status, author, sort_by, cursor)

    async def create_book(self, book_data: BookCreate):
        return await self.repo.create(book_data)

    async def get_book(self, book_id: UUID):
        return await self.repo.get_by_id(book_id)

    async def delete_book(self, book_id: UUID):
        return await self.repo.delete(book_id)
