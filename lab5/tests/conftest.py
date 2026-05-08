import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "postgresql+psycopg2://test_user:test_pass@localhost:5434/library5_test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from database import Base
from main import create_app
from models.book import BookModel


@pytest.fixture(scope="session")
def test_engine():
    maintenance_engine = create_engine(
        "postgresql+psycopg2://test_user:test_pass@localhost:5434/postgres",
        echo=False,
        future=True,
        isolation_level="AUTOCOMMIT",
    )
    with maintenance_engine.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'library5_test'")).scalar()
        if not exists:
            conn.execute(text("CREATE DATABASE library5_test"))
    maintenance_engine.dispose()

    engine = create_engine(TEST_DATABASE_URL, echo=False, future=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def setup_test_db(test_engine):
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def clear_database(test_engine):
    with test_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE books CASCADE;"))
    yield


@pytest.fixture
def db_session(test_engine, setup_test_db, clear_database):
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    def service_provider():
        from services.book_service import BookService

        return BookService(db_session)

    app = create_app({"TESTING": True, "INIT_DB": False, "BOOK_SERVICE_PROVIDER": service_provider})
    with app.test_client() as test_client:
        yield test_client
