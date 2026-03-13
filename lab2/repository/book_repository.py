from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, func
from models.book import BookModel
from uuid import UUID


class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, limit: int, offset: int, status: str = None, author: str = None, sort_by: str = None):
        query = select(BookModel)

        if status:
            query = query.where(BookModel.status == status)
        if author:
            query = query.where(BookModel.author.ilike(f"%{author}%"))

        if sort_by == "title":
            query = query.order_by(BookModel.title)
        elif sort_by == "year":
            query = query.order_by(BookModel.year)

        total_query = select(func.count()).select_from(query.subquery())
        total = await self.session.execute(total_query)

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)

        return total.scalar(), result.scalars().all()

    async def get_by_id(self, book_id: UUID):
        result = await self.session.execute(select(BookModel).where(BookModel.id == book_id))
        return result.scalar_one_or_none()

    async def create(self, book_data):
        new_book = BookModel(**book_data.model_dump())
        self.session.add(new_book)
        await self.session.commit()
        await self.session.refresh(new_book)
        return new_book

    async def delete(self, book_id: UUID):
        query = delete(BookModel).where(BookModel.id == book_id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0