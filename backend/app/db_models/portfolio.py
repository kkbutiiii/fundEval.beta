"""
Portfolio database models using SQLAlchemy.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base

# Forward reference for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.db_models.user import UserDB


class PortfolioDB(Base):
    """Portfolio database model."""
    __tablename__ = "portfolios"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship: portfolio has many holdings
    holdings = relationship(
        "PortfolioHoldingDB",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Relationship: portfolio belongs to a user
    user = relationship("UserDB", back_populates="portfolios")

    def __repr__(self):
        return f"<PortfolioDB(id={self.id}, name={self.name}, user_id={self.user_id})>"


class PortfolioHoldingDB(Base):
    """Portfolio holding (fund) database model."""
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(String(64), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    fund_code = Column(String(20), nullable=False)
    fund_name = Column(String(255), nullable=False)
    shares = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship: holding belongs to a portfolio
    portfolio = relationship("PortfolioDB", back_populates="holdings")

    # Unique constraint: one fund per portfolio
    __table_args__ = (
        # Composite unique index on portfolio_id + fund_code
        # This is handled at the application level since SQLite doesn't support
        # ALTER TABLE for adding constraints after table creation
    )

    def __repr__(self):
        return f"<PortfolioHoldingDB(portfolio_id={self.portfolio_id}, fund_code={self.fund_code}, shares={self.shares})>"
