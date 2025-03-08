from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base
import enum


class BookStatus(enum.Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    MAINTENANCE = "maintenance"
    LOST = "lost"


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    author = Column(String(255), index=True, nullable=False)
    isbn = Column(String(20), unique=True, index=True, nullable=False)
    publication_year = Column(Integer)
    publisher = Column(String(255))
    genre = Column(String(100), index=True)
    description = Column(Text)
    cover_image_url = Column(String(255))
    status = Column(Enum(BookStatus), default=BookStatus.AVAILABLE)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    loans = relationship("Loan", back_populates="book")
    reviews = relationship("Review", back_populates="book")
