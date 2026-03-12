"""
Fund transaction database models using SQLAlchemy.
Records buy/sell transactions for portfolio funds.
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Date
from sqlalchemy.orm import relationship

from app.database import Base


class FundTransactionDB(Base):
    """Fund transaction database model for recording buy/sell operations."""
    __tablename__ = "fund_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(64), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    fund_code = Column(String(20), nullable=False, index=True)
    fund_name = Column(String(255), nullable=False)
    transaction_type = Column(String(10), nullable=False)  # 'buy' or 'sell'
    transaction_date = Column(Date, nullable=False)  # 确认日期
    nav = Column(Float, nullable=False)  # 确认净值
    shares = Column(Float, nullable=False)  # 份额
    amount = Column(Float, nullable=False)  # 金额
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<FundTransactionDB(id={self.id}, portfolio_id={self.portfolio_id}, fund_code={self.fund_code}, type={self.transaction_type})>"
