import pytest


@pytest.fixture
def sample_book_payload():
    return {
        "title": "Clean Architecture",
        "author": "Robert C. Martin",
        "description": "A practical guide to software design.",
        "status": "available",
        "year": 2017,
    }
