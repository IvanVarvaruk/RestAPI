from contextlib import contextmanager
from uuid import UUID

from flask import current_app, request
from flask_restful import Resource
from marshmallow import ValidationError

from database import session_scope
from schemas.book import (
    book_create_schema,
    book_query_schema,
    book_schema,
    books_schema,
    format_validation_error,
)
from services.book_service import BookService


@contextmanager
def service_scope():
    provider = current_app.config.get("BOOK_SERVICE_PROVIDER")
    if provider:
        yield provider()
        return

    with session_scope() as session:
        yield BookService(session)


class BookListResource(Resource):
    def get(self):
        """
        List books.
        ---
        tags:
          - books
        parameters:
          - in: query
            name: limit
            schema:
              type: integer
              minimum: 1
              default: 10
          - in: query
            name: offset
            schema:
              type: integer
              minimum: 0
              default: 0
          - in: query
            name: cursor
            schema:
              type: string
              format: uuid
          - in: query
            name: status
            schema:
              type: string
          - in: query
            name: author
            schema:
              type: string
          - in: query
            name: sort_by
            schema:
              type: string
              enum: [title, year]
        responses:
          200:
            description: Paginated list of books.
        """
        try:
            args = book_query_schema.load(request.args)
        except ValidationError as error:
            return format_validation_error(error)

        with service_scope() as service:
            total, items = service.list_books(
                args["limit"],
                args["offset"],
                args.get("status"),
                args.get("author"),
                args.get("sort_by"),
                args.get("cursor"),
            )

        serialized = books_schema.dump(items)
        return {
            "total": total,
            "limit": args["limit"],
            "offset": args["offset"],
            "items": serialized,
            "next_cursor": serialized[-1]["id"] if serialized else None,
        }, 200

    def post(self):
        """
        Create a book.
        ---
        tags:
          - books
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required: [title, author, status, year]
                properties:
                  title:
                    type: string
                  author:
                    type: string
                  description:
                    type: string
                    nullable: true
                  status:
                    type: string
                  year:
                    type: integer
        responses:
          201:
            description: Created book.
          422:
            description: Validation error.
        """
        try:
            payload = book_create_schema.load(request.get_json(silent=True) or {})
        except ValidationError as error:
            return format_validation_error(error)

        with service_scope() as service:
            book = service.create_book(payload)
        return book_schema.dump(book), 201


class BookResource(Resource):
    def get(self, book_id):
        """
        Get a book by id.
        ---
        tags:
          - books
        parameters:
          - in: path
            name: book_id
            required: true
            schema:
              type: string
              format: uuid
        responses:
          200:
            description: Book.
          404:
            description: Book not found.
          422:
            description: Invalid UUID.
        """
        parsed_id, error = parse_uuid(book_id)
        if error:
            return error

        with service_scope() as service:
            book = service.get_book(parsed_id)
        if not book:
            return {"detail": "Book not found"}, 404
        return book_schema.dump(book), 200

    def delete(self, book_id):
        """
        Delete a book by id.
        ---
        tags:
          - books
        parameters:
          - in: path
            name: book_id
            required: true
            schema:
              type: string
              format: uuid
        responses:
          204:
            description: Deleted.
          404:
            description: Book not found.
          422:
            description: Invalid UUID.
        """
        parsed_id, error = parse_uuid(book_id)
        if error:
            return error

        with service_scope() as service:
            deleted = service.delete_book(parsed_id)
        if not deleted:
            return {"detail": "Book not found"}, 404
        return "", 204


def parse_uuid(raw_value):
    try:
        return UUID(str(raw_value)), None
    except ValueError:
        return None, ({"message": {"book_id": ["Not a valid UUID."]}}, 422)
