from sqlalchemy import String, cast, delete, func, select

from models.book import BookModel


class BookRepository:
    def __init__(self, session):
        self.session = session

    def get_all(self, limit, offset, status=None, author=None, sort_by=None, cursor=None):
        query = select(BookModel)

        if status:
            query = query.where(BookModel.status == status)
        if author:
            query = query.where(BookModel.author.ilike(f"%{author}%"))
        if cursor:
            query = query.where(cast(BookModel.id, String) > str(cursor))

        if sort_by == "title":
            query = query.order_by(BookModel.title, BookModel.id)
        elif sort_by == "year":
            query = query.order_by(BookModel.year, BookModel.id)
        else:
            query = query.order_by(BookModel.id)

        total = self.session.execute(select(func.count()).select_from(query.subquery())).scalar_one()
        items = self.session.execute(query.limit(limit).offset(offset)).scalars().all()
        return total, items

    def get_by_id(self, book_id):
        return self.session.execute(select(BookModel).where(BookModel.id == book_id)).scalar_one_or_none()

    def create(self, book_data):
        new_book = BookModel(**book_data)
        self.session.add(new_book)
        self.session.commit()
        self.session.refresh(new_book)
        return new_book

    def delete(self, book_id):
        result = self.session.execute(delete(BookModel).where(BookModel.id == book_id))
        self.session.commit()
        return result.rowcount > 0
