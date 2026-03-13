from fastapi import APIRouter, HTTPException, status, Query
from schemas.book import Book, BookCreate, BookStatus
from services.book_service import BookService
from uuid import UUID
from typing import List, Optional

router = APIRouter(prefix="/books", tags=["Books"])
service = BookService()

@router.get("/", response_model=List[Book], status_code=status.HTTP_200_OK)
async def read_books(
    status: Optional[BookStatus] = None,
    author: Optional[str] = None,
    sort_by: Optional[str] = Query(None, regex="^(title|year)$")
):
    return await service.get_books(status, author, sort_by)

@router.get("/{book_id}", response_model=Book)
async def read_book(book_id: UUID):
    book = await service.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.post("/", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate):
    return await service.add_book(book)

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: UUID):
    await service.remove_book(book_id)
    return None