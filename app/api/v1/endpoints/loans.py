from typing import Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_superuser, get_current_active_user
from app.core.exceptions import BadRequestError, NotFoundError, ForbiddenError
from app.crud.loan import loan
from app.crud.book import book
from app.db.session import get_db
from app.models.book import Book, BookStatus
from app.models.loan import Loan, LoanStatus
from app.models.user import User
from app.schemas.loan import Loan as LoanSchema, LoanCreate, LoanUpdate, LoanWithDetails

router = APIRouter()


@router.get("/", response_model=List[LoanWithDetails])
def read_loans(
    db: Session = Depends(get_db),
    status: Optional[LoanStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve loans.
    """
    # Update loan statuses for overdue loans
    loan.update_loan_status(db)
    
    # For non-admin users, only show their own loans
    if not current_user.is_superuser:
        if status:
            loans = db.query(Loan)\
                .filter(Loan.user_id == current_user.id)\
                .filter(Loan.status == status)\
                .offset(skip)\
                .limit(limit)\
                .all()
        else:
            loans = db.query(Loan)\
                .filter(Loan.user_id == current_user.id)\
                .offset(skip)\
                .limit(limit)\
                .all()
    else:
        # Admin users can see all loans
        if status:
            loans = db.query(Loan)\
                .filter(Loan.status == status)\
                .offset(skip)\
                .limit(limit)\
                .all()
        else:
            loans = loan.get_multi(db, skip=skip, limit=limit)
    
    return loans


@router.post("/", response_model=LoanSchema)
def create_loan(
    *,
    db: Session = Depends(get_db),
    loan_in: LoanCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new loan. Regular users can only create loans for themselves.
    """
    # Check if book exists
    book_obj = book.get(db, id=loan_in.book_id)
    if not book_obj:
        raise NotFoundError(detail="Book not found")
    
    # Check if book is available
    if book_obj.status != BookStatus.AVAILABLE:
        raise BadRequestError(detail="Book is not available for loan")
    
    # For regular users, ensure they can only create loans for themselves
    if not current_user.is_superuser:
        loan_in.user_id = current_user.id
    elif not loan_in.user_id:
        # If admin doesn't specify user_id, use their own
        loan_in.user_id = current_user.id
    
    # Create the loan
    loan_obj = loan.create(db, obj_in=loan_in)
    
    # Update book status
    book_obj.status = BookStatus.BORROWED
    db.add(book_obj)
    db.commit()
    
    return loan_obj


@router.get("/{loan_id}", response_model=LoanWithDetails)
def read_loan(
    *,
    db: Session = Depends(get_db),
    loan_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get loan by ID.
    """
    loan_obj = loan.get(db, id=loan_id)
    if not loan_obj:
        raise NotFoundError(detail="Loan not found")
    
    # Check permissions - users can only view their own loans unless they're admin
    if not current_user.is_superuser and loan_obj.user_id != current_user.id:
        raise ForbiddenError(detail="Not enough permissions")
    
    return loan_obj


@router.put("/{loan_id}", response_model=LoanSchema)
def update_loan(
    *,
    db: Session = Depends(get_db),
    loan_id: int,
    loan_in: LoanUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a loan. Regular users can only extend due date for their own loans.
    """
    loan_obj = loan.get(db, id=loan_id)
    if not loan_obj:
        raise NotFoundError(detail="Loan not found")
    
    # Check permissions - users can only update their own loans unless they're admin
    if not current_user.is_superuser and loan_obj.user_id != current_user.id:
        raise ForbiddenError(detail="Not enough permissions")
    
    # Regular users can only extend due date
    if not current_user.is_superuser:
        # Only allow updating due_date
        if loan_in.status or loan_in.return_date:
            raise ForbiddenError(detail="You can only extend the due date")
        
        # Ensure loan is active
        if loan_obj.status != LoanStatus.ACTIVE and loan_obj.status != LoanStatus.PENDING:
            raise BadRequestError(detail="Cannot extend due date for non-active loan")
        
        # Ensure new due date is after current due date
        if loan_in.due_date and loan_in.due_date <= loan_obj.due_date:
            raise BadRequestError(detail="New due date must be after current due date")
    
    # Update the loan
    loan_obj = loan.update(db, db_obj=loan_obj, obj_in=loan_in)
    return loan_obj


@router.post("/{loan_id}/return", response_model=LoanSchema)
def return_book(
    *,
    db: Session = Depends(get_db),
    loan_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Return a book.
    """
    loan_obj = loan.get(db, id=loan_id)
    if not loan_obj:
        raise NotFoundError(detail="Loan not found")
    
    # Check permissions - users can only return their own loans unless they're admin
    if not current_user.is_superuser and loan_obj.user_id != current_user.id:
        raise ForbiddenError(detail="Not enough permissions")
    
    # Ensure loan is active or overdue
    if loan_obj.status not in [LoanStatus.ACTIVE, LoanStatus.OVERDUE]:
        raise BadRequestError(detail="Loan is not active or overdue")
    
    # Return the book
    loan_obj = loan.return_book(db, loan_id=loan_id)
    if not loan_obj:
        raise BadRequestError(detail="Failed to return book")
    
    return loan_obj


@router.delete("/{loan_id}", response_model=LoanSchema)
def delete_loan(
    *,
    db: Session = Depends(get_db),
    loan_id: int,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Delete a loan. Only for superusers.
    """
    loan_obj = loan.get(db, id=loan_id)
    if not loan_obj:
        raise NotFoundError(detail="Loan not found")
    
    # Update book status if loan is active
    if loan_obj.status in [LoanStatus.ACTIVE, LoanStatus.OVERDUE]:
        book_obj = book.get(db, id=loan_obj.book_id)
        if book_obj:
            book_obj.status = BookStatus.AVAILABLE
            db.add(book_obj)
    
    loan_obj = loan.remove(db, id=loan_id)
    db.commit()
    
    return loan_obj