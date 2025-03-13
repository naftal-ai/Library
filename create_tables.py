from app.db.base import Base
from app.db.session import engine
from app.models.book import Book
from app.models.user import User
from app.models.loan import Loan
from app.models.review import Review

Base.metadata.create_all(bind=engine)
print("Tables created")