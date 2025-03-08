from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ReviewBase(BaseModel):
    book_id: int
    user_id: Optional[int] = None
    rating: float = Field(..., ge=0.0, le=5.0)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    comment: Optional[str] = None


class ReviewInDBBase(ReviewBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Review(ReviewInDBBase):
    pass


class ReviewWithDetails(Review):
    from app.schemas.book import Book
    from app.schemas.user import User
    
    book: Book
    user: User