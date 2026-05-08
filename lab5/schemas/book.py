from marshmallow import Schema, ValidationError, fields, validate


class BookCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1))
    author = fields.String(required=True, validate=validate.Length(min=1))
    description = fields.String(allow_none=True, load_default=None)
    status = fields.String(required=True, validate=validate.Length(min=1))
    year = fields.Integer(required=True)


class BookSchema(BookCreateSchema):
    id = fields.UUID(required=True)


class BookQuerySchema(Schema):
    limit = fields.Integer(load_default=10, validate=validate.Range(min=1))
    offset = fields.Integer(load_default=0, validate=validate.Range(min=0))
    cursor = fields.UUID(load_default=None, allow_none=True)
    status = fields.String(load_default=None, allow_none=True)
    author = fields.String(load_default=None, allow_none=True)
    sort_by = fields.String(load_default=None, allow_none=True, validate=validate.OneOf(["title", "year", None]))


book_create_schema = BookCreateSchema()
book_schema = BookSchema()
books_schema = BookSchema(many=True)
book_query_schema = BookQuerySchema()


def format_validation_error(error: ValidationError):
    return {"message": error.messages}, 422
