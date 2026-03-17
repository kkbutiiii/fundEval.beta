"""
Watchlist database model.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class WatchlistDB(Base):
    """Watchlist database model."""
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    fund_code = Column(String(20), nullable=False)
    fund_name = Column(String(255), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: watchlist item belongs to a user
    user = relationship("UserDB", back_populates="watchlists")

    def __repr__(self):
        return f"<WatchlistDB(user_id={self.user_id}, fund_code={self.fund_code})>"
