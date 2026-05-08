from repository.book_repository import BookRepository


class BookService:
    def __init__(self, db):
        self.repo = BookRepository(db)

    def list_books(self, limit, offset, status=None, author=None, sort_by=None, cursor=None):
        return self.repo.get_all(limit, offset, status, author, sort_by, cursor)

    def create_book(self, book_data):
        return self.repo.create(book_data)

    def get_book(self, book_id):
        return self.repo.get_by_id(book_id)

    def delete_book(self, book_id):
        return self.repo.delete(book_id)
