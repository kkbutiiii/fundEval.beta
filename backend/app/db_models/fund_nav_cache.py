"""
Fund NAV Cache Model
Caches historical NAV data for funds to avoid repeated API calls.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, DateTime, UniqueConstraint
from app.db.database import Base


class FundNavCacheDB(Base):
    """Database model for fund NAV cache."""
    __tablename__ = 'fund_nav_cache'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    nav = Column(Numeric(10, 4), nullable=True)
    is_estimated = Column(Boolean, default=False)  # True if NAV is from a previous trading day
    actual_date = Column(Date, nullable=True)  # The actual date the NAV is from
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('fund_code', 'date', name='unique_fund_date'),
    )

    def __repr__(self):
        return f"<FundNavCacheDB(fund_code='{self.fund_code}', date='{self.date}', nav={self.nav})>"
