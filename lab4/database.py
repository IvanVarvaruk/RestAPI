import os

from motor.motor_asyncio import AsyncIOMotorClient


DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/library4")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = AsyncIOMotorClient(DATABASE_URL)
database = client[DATABASE_NAME] if DATABASE_NAME else client.get_default_database()


async def init_db():
    await database.books.create_index("id", unique=True)
    await database.books.create_index([("status", 1), ("author", 1)])
    await database.books.create_index([("title", 1), ("id", 1)])
    await database.books.create_index([("year", 1), ("id", 1)])


async def close_db():
    client.close()


async def get_db():
    yield database
