from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_superuser, get_current_active_user
from app.core.exceptions import BadRequestError, NotFoundError
from app.crud.book import book
from app.db.session import get_db
from app.models.book import BookStatus
from app.models.user import User
from app.schemas.book import Book, BookCreate, BookUpdate

router = APIRouter()


@router.get("/", response_model=List[Book])
def read_books(
    db: Session = Depends(get_db),
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve books with optional filtering.
    """
    if title or author or genre:
        books = book.search_books(
            db, title=title, author=author, genre=genre, skip=skip, limit=limit
        )
    else:
        books = book.get_multi(db, skip=skip, limit=limit)
    return books


@router.post("/", response_model=Book)
def create_book(
    *,
    db: Session = Depends(get_db),
    book_in: BookCreate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new book.
    """
    # Check if ISBN already exists
    book_exists = book.get_by_isbn(db, isbn=book_in.isbn)
    if book_exists:
        raise BadRequestError(
            detail="A book with this ISBN already exists in the system"
        )
    
    book_obj = book.create(db, obj_in=book_in)
    return book_obj


@router.get("/{book_id}", response_model=Book)
def read_book(
    *,
    db: Session = Depends(get_db),
    book_id: int,
) -> Any:
    """
    Get book by ID.
    """
    book_obj = book.get(db, id=book_id)
    if not book_obj:
        raise NotFoundError(detail="Book not found")
    return book_obj


@router.put("/{book_id}", response_model=Book)
def update_book(
    *,
    db: Session = Depends(get_db),
    book_id: int,
    book_in: BookUpdate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update a book.
    """
    book_obj = book.get(db, id=book_id)
    if not book_obj:
        raise NotFoundError(detail="Book not found")
    
    # Check if ISBN already exists (if updating ISBN)
    if book_in.isbn and book_in.isbn != book_obj.isbn:
        book_exists = book.get_by_isbn(db, isbn=book_in.isbn)
        if book_exists:
            raise BadRequestError(
                detail="A book with this ISBN already exists in the system"
            )
    
    book_obj = book.update(db, db_obj=book_obj, obj_in=book_in)
    return book_obj


@router.delete("/{book_id}", response_model=Book)
def delete_book(
    *,
    db: Session = Depends(get_db),
    book_id: int,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Delete a book.
    """
    book_obj = book.get(db, id=book_id)
    if not book_obj:
        raise NotFoundError(detail="Book not found")
    
    book_obj = book.remove(db, id=book_id)
    return book_obj