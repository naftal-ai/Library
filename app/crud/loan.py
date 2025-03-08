from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.loan import Loan, LoanStatus
from app.schemas.loan import LoanCreate, LoanUpdate


class CRUDLoan(CRUDBase[Loan, LoanCreate, LoanUpdate]):
    def get_active_loans_by_user(self, db: Session, *, user_id: int) -> List[Loan]:
        return db.query(Loan)\
            .filter(Loan.user_id == user_id)\
            .filter(Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.OVERDUE]))\
            .all()

    def get_active_loans_by_book(self, db: Session, *, book_id: int) -> List[Loan]:
        return db.query(Loan)\
            .filter(Loan.book_id == book_id)\
            .filter(Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.OVERDUE]))\
            .all()

    def get_overdue_loans(self, db: Session) -> List[Loan]:
        return db.query(Loan)\
            .filter(Loan.status == LoanStatus.ACTIVE)\
            .filter(Loan.due_date < func.now())\
            .all()

    def update_loan_status(self, db: Session) -> None:
        """Update loan status for overdue loans"""
        overdue_loans = db.query(Loan)\
            .filter(Loan.status == LoanStatus.ACTIVE)\
            .filter(Loan.due_date < func.now())\
            .all()
        
        for loan in overdue_loans:
            loan.status = LoanStatus.OVERDUE
            db.add(loan)
        
        db.commit()

    def return_book(self, db: Session, *, loan_id: int) -> Optional[Loan]:
        loan = self.get(db, id=loan_id)
        if not loan:
            return None
        
        # Update loan information
        loan.return_date = datetime.now()
        loan.status = LoanStatus.RETURNED
        db.add(loan)
        
        # Update book status
        from app.models.book import BookStatus
        book = loan.book
        book.status = BookStatus.AVAILABLE
        db.add(book)
        
        db.commit()
        db.refresh(loan)
        return loan


loan = CRUDLoan(Loan)