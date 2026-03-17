"""
Portfolio Return Cache Model
Caches calculated portfolio return data to improve performance.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, UniqueConstraint
from app.database import Base


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

    # TWR calculation: Fund-of-Funds perspective
    fund_shares = Column(Numeric(20, 8), nullable=True)  # 母基金份额（仅在资金进出时变化）
    fund_nav = Column(Numeric(15, 6), nullable=True)     # 母基金净值

    # Cache version for invalidation
    calculation_version = Column(Integer, default=1)     # 缓存版本，算法更新时递增

    # Metadata
    is_estimated = Column(Boolean, default=False)        # True if any NAV is estimated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('portfolio_id', 'date', name='unique_portfolio_date'),
    )

    def __repr__(self):
        return f"<PortfolioReturnCacheDB(portfolio_id='{self.portfolio_id}', date='{self.date}', return_rate={self.return_rate})>"
