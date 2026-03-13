"""
Portfolio Return Cache Model
Caches calculated portfolio return data to improve performance.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, UniqueConstraint
from app.db.database import Base


class PortfolioReturnCacheDB(Base):
    """Database model for portfolio return cache."""
    __tablename__ = 'portfolio_return_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Portfolio metrics
    total_value = Column(Numeric(15, 2), nullable=True)  # Total market value
    total_cost = Column(Numeric(15, 2), nullable=True)   # Total cost basis
    total_profit = Column(Numeric(15, 2), nullable=True) # Total profit/loss
    daily_profit = Column(Numeric(15, 2), nullable=True) # Daily profit/loss

    # Return metrics
    return_rate = Column(Numeric(10, 4), nullable=True)  # Simple return rate (%)
    twr = Column(Numeric(10, 4), nullable=True)          # Time-Weighted Return (%)
    xirr = Column(Numeric(10, 4), nullable=True)         # Money-Weighted Return (% annualized)

    # Metadata
    is_estimated = Column(Boolean, default=False)        # True if any NAV is estimated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('portfolio_id', 'date', name='unique_portfolio_date'),
    )

    def __repr__(self):
        return f"<PortfolioReturnCacheDB(portfolio_id='{self.portfolio_id}', date='{self.date}', return_rate={self.return_rate})>"
