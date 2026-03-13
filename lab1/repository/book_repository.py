from uuid import UUID, uuid4
from models.storage import books_db
from schemas.book import BookCreate

class BookRepository:
    async def get_all(self):
        return books_db

    async def get_by_id(self, book_id: UUID):
        for book in books_db:
            if book["id"] == book_id:
                return book
        return None

    async def create(self, book_data: BookCreate):
        new_book = book_data.model_dump()
        new_book["id"] = uuid4()
        books_db.append(new_book)
        return new_book

    async def delete(self, book_id: UUID):
        for i, book in enumerate(books_db):
            if book["id"] == book_id:
                del books_db[i]
                return True
        return False