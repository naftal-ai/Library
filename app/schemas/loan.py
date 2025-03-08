from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.loan import LoanStatus


class LoanBase(BaseModel):
    book_id: int
    user_id: Optional[int] = None
    due_date: datetime
    notes: Optional[str] = None


class LoanCreate(LoanBase):
    pass


class LoanUpdate(BaseModel):
    due_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    status: Optional[LoanStatus] = None
    notes: Optional[str] = None


class LoanInDBBase(LoanBase):
    id: int
    loan_date: datetime
    return_date: Optional[datetime] = None
    status: LoanStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Loan(LoanInDBBase):
    pass


class LoanWithDetails(Loan):
    from app.schemas.book import Book
    from app.schemas.user import User
    
    book: Book
    user: User