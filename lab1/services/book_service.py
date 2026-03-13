from repository.book_repository import BookRepository
from schemas.book import BookStatus
from typing import Optional


class BookService:
    def __init__(self):
        self.repository = BookRepository()

    async def get_books(self, status: Optional[BookStatus] = None, author: Optional[str] = None,
                        sort_by: Optional[str] = None):
        books = await self.repository.get_all()

        if status:
            books = [b for b in books if b["status"] == status]
        if author:
            books = [b for b in books if author.lower() in b["author"].lower()]

        if sort_by == "title":
            books = sorted(books, key=lambda x: x["title"])
        elif sort_by == "year":
            books = sorted(books, key=lambda x: x["year"])

        return books

    async def get_book_by_id(self, book_id):
        return await self.repository.get_by_id(book_id)

    async def add_book(self, book_data):
        return await self.repository.create(book_data)

    async def remove_book(self, book_id):
        return await self.repository.delete(book_id)