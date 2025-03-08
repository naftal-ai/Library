from typing import List, Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate


class CRUDReview(CRUDBase[Review, ReviewCreate, ReviewUpdate]):
    def get_reviews_by_book(
        self, db: Session, *, book_id: int, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        return db.query(Review)\
            .filter(Review.book_id == book_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_reviews_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        return db.query(Review)\
            .filter(Review.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_user_review_for_book(
        self, db: Session, *, user_id: int, book_id: int
    ) -> Optional[Review]:
        return db.query(Review)\
            .filter(Review.user_id == user_id, Review.book_id == book_id)\
            .first()

    def create_or_update_review(
        self, db: Session, *, obj_in: ReviewCreate, user_id: int
    ) -> Review:
        # Check if review already exists
        existing_review = self.get_user_review_for_book(
            db, user_id=user_id, book_id=obj_in.book_id
        )
        
        if existing_review:
            # Update existing review
            update_data = {
                "rating": obj_in.rating,
                "comment": obj_in.comment
            }
            updated_review = super().update(db, db_obj=existing_review, obj_in=update_data)
            
            # Update book's average rating
            from app.crud.book import book
            book.update_book_rating(db, book_id=obj_in.book_id)
            
            return updated_review
        else:
            # Create new review
            review_in_data = obj_in.dict()
            review_in_data["user_id"] = user_id
            db_obj = Review(**review_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            # Update book's average rating
            from app.crud.book import book
            book.update_book_rating(db, book_id=obj_in.book_id)
            
            return db_obj


review = CRUDReview(Review)