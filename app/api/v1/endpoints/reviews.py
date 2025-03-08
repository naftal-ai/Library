from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_superuser, get_current_active_user
from app.core.exceptions import BadRequestError, NotFoundError, ForbiddenError
from app.crud.review import review
from app.crud.book import book
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import Review as ReviewSchema, ReviewCreate, ReviewUpdate, ReviewWithDetails

router = APIRouter()


@router.get("/", response_model=List[ReviewWithDetails])
def read_reviews(
    db: Session = Depends(get_db),
    book_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve reviews with optional filtering.
    """
    if book_id:
        # Get reviews for a specific book
        reviews = review.get_reviews_by_book(db, book_id=book_id, skip=skip, limit=limit)
    elif user_id:
        # Get reviews by a specific user
        reviews = review.get_reviews_by_user(db, user_id=user_id, skip=skip, limit=limit)
    else:
        # Get all reviews
        reviews = review.get_multi(db, skip=skip, limit=limit)
    
    return reviews


@router.post("/", response_model=ReviewSchema)
def create_review(
    *,
    db: Session = Depends(get_db),
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create or update a review. Users can only create reviews for books they've borrowed.
    """
    # Check if book exists
    book_obj = book.get(db, id=review_in.book_id)
    if not book_obj:
        raise NotFoundError(detail="Book not found")
    
    # Set the user_id to the current user
    user_id = current_user.id
    
    # Create or update the review
    review_obj = review.create_or_update_review(db, obj_in=review_in, user_id=user_id)
    return review_obj


@router.get("/{review_id}", response_model=ReviewWithDetails)
def read_review(
    *,
    db: Session = Depends(get_db),
    review_id: int,
) -> Any:
    """
    Get review by ID.
    """
    review_obj = review.get(db, id=review_id)
    if not review_obj:
        raise NotFoundError(detail="Review not found")
    
    return review_obj


@router.put("/{review_id}", response_model=ReviewSchema)
def update_review(
    *,
    db: Session = Depends(get_db),
    review_id: int,
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a review. Users can only update their own reviews.
    """
    review_obj = review.get(db, id=review_id)
    if not review_obj:
        raise NotFoundError(detail="Review not found")
    
    # Check permissions - users can only update their own reviews unless they're admin
    if not current_user.is_superuser and review_obj.user_id != current_user.id:
        raise ForbiddenError(detail="Not enough permissions")
    
    # Update the review
    review_obj = review.update(db, db_obj=review_obj, obj_in=review_in)
    
    # Update book's average rating
    book.update_book_rating(db, book_id=review_obj.book_id)
    
    return review_obj


@router.delete("/{review_id}", response_model=ReviewSchema)
def delete_review(
    *,
    db: Session = Depends(get_db),
    review_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a review. Users can only delete their own reviews.
    """
    review_obj = review.get(db, id=review_id)
    if not review_obj:
        raise NotFoundError(detail="Review not found")
    
    # Check permissions - users can only delete their own reviews unless they're admin
    if not current_user.is_superuser and review_obj.user_id != current_user.id:
        raise ForbiddenError(detail="Not enough permissions")
    
    # Save book_id before deletion for updating rating
    book_id = review_obj.book_id
    
    # Delete the review
    review_obj = review.remove(db, id=review_id)
    
    # Update book's average rating
    book.update_book_rating(db, book_id=book_id)
    
    return review_obj