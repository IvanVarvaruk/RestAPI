from flasgger import Swagger
from flask import Flask
from flask_restful import Api

from api.resources import BookListResource, BookResource
from database import Base, get_engine
from models.book import BookModel


def init_database():
    Base.metadata.create_all(bind=get_engine())


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        {
            "SWAGGER": {
                "title": "Library API",
                "uiversion": 3,
                "openapi": "3.0.2",
            },
            "INIT_DB": False,
        }
    )
    if config:
        app.config.update(config)

    Swagger(app)
    api = Api(app)
    api.add_resource(BookListResource, "/books/")
    api.add_resource(BookResource, "/books/<string:book_id>")

    if app.config["INIT_DB"]:
        with app.app_context():
            init_database()

    return app


app = create_app()


if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=5000)
