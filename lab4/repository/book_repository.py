import re
from uuid import UUID, uuid4

from pymongo import ASCENDING


class BookRepository:
    def __init__(self, database):
        self.collection = database.books

    async def get_all(
        self,
        limit: int,
        offset: int,
        status: str = None,
        author: str = None,
        sort_by: str = None,
        cursor: UUID = None,
    ):
        filters = {}

        if status:
            filters["status"] = status
        if author:
            filters["author"] = {"$regex": re.escape(author), "$options": "i"}
        if cursor:
            filters["id"] = {"$gt": str(cursor)}

        sort_field = "id"
        if sort_by == "title":
            sort_field = "title"
        elif sort_by == "year":
            sort_field = "year"

        total = await self.collection.count_documents(filters)
        cursor_result = (
            self.collection.find(filters, {"_id": 0})
            .sort([(sort_field, ASCENDING), ("id", ASCENDING)])
            .skip(offset)
            .limit(limit)
        )
        items = await cursor_result.to_list(length=limit)

        return total, items

    async def get_by_id(self, book_id: UUID):
        return await self.collection.find_one({"id": str(book_id)}, {"_id": 0})

    async def create(self, book_data):
        new_book = {
            "id": str(uuid4()),
            **book_data.model_dump(),
        }
        await self.collection.insert_one(new_book)
        return {key: value for key, value in new_book.items() if key != "_id"}

    async def delete(self, book_id: UUID):
        deleted_book = await self.collection.find_one_and_delete({"id": str(book_id)})
        return deleted_book is not None
