from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.book import Book, BookCreate, PaginatedBooks
from services.book_service import BookService
from uuid import UUID
from typing import Optional

router = APIRouter()


@router.get("/books/", response_model=PaginatedBooks)
async def get_books(
        limit: int = Query(10, ge=1),
        offset: int = Query(0, ge=0),
        cursor: Optional[UUID] = Query(None, description="ID останньої книги з попередньої сторінки"),
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    service = BookService(db)
    total, items = await service.list_books(limit, offset, status, author, sort_by, cursor)

    next_cursor = items[-1].id if items else None

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
        "next_cursor": next_cursor
    }


@router.post("/books/", response_model=Book, status_code=201)
async def add_book(book_in: BookCreate, db: AsyncSession = Depends(get_db)):
    service = BookService(db)
    return await service.create_book(book_in)


@router.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: UUID, db: AsyncSession = Depends(get_db)):
    service = BookService(db)
    book = await service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.delete("/books/{book_id}", status_code=204)
async def delete_book(book_id: UUID, db: AsyncSession = Depends(get_db)):
    service = BookService(db)
    is_deleted = await service.delete_book(book_id)
    if not is_deleted:
        raise HTTPException(status_code=404, detail="Book not found")
    return None