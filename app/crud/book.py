from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate


class CRUDBook(CRUDBase[Book, BookCreate, BookUpdate]):
    def get_by_isbn(self, db: Session, *, isbn: str) -> Optional[Book]:
        return db.query(Book).filter(Book.isbn == isbn).first()

    def search_books(
        self,
        db: Session,
        *,
        title: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Book]:
        query = db.query(Book)
        if title:
            query = query.filter(Book.title.ilike(f"%{title}%"))
        if author:
            query = query.filter(Book.author.ilike(f"%{author}%"))
        if genre:
            query = query.filter(Book.genre.ilike(f"%{genre}%"))
        return query.offset(skip).limit(limit).all()

    def update_book_rating(self, db: Session, *, book_id: int) -> None:
        """Update book's average rating based on its reviews"""
        from app.models.review import Review
        
        avg_rating = db.query(func.avg(Review.rating))\
            .filter(Review.book_id == book_id)\
            .scalar()
        
        book = self.get(db, id=book_id)
        if book and avg_rating is not None:
            book.rating = avg_rating
            db.add(book)
            db.commit()
            db.refresh(book)


book = CRUDBook(Book)