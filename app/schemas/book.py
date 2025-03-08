from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.models.book import BookStatus


class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    status: BookStatus = BookStatus.AVAILABLE


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    status: Optional[BookStatus] = None


class BookInDBBase(BookBase):
    id: int
    rating: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Book(BookInDBBase):
    pass
