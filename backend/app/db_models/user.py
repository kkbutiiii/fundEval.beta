"""
User database model.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime

from app.database import Base


# Forward reference for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.db_models.portfolio import PortfolioDB
    from app.db_models.watchlist import WatchlistDB


class UserDB(Base):
    """User database model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<UserDB(id={self.id}, username={self.username})>"


# Import and set up relationships after class definition to avoid circular imports
def _setup_relationships():
    from sqlalchemy.orm import relationship
    from app.db_models.portfolio import PortfolioDB
    from app.db_models.watchlist import WatchlistDB
    UserDB.portfolios = relationship("PortfolioDB", back_populates="user", cascade="all, delete-orphan")
    UserDB.watchlists = relationship("WatchlistDB", back_populates="user", cascade="all, delete-orphan")

_setup_relationships()
