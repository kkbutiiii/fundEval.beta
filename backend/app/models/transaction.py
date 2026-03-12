"""
Transaction Pydantic models for API request/response.
"""
from datetime import datetime, date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class FundTransactionBase(BaseModel):
    """Base transaction model."""
    transaction_type: Literal["buy", "sell"] = Field(..., description="Transaction type: buy or sell")
    transaction_date: date = Field(..., description="Confirmation date")
    nav: float = Field(..., description="NAV at transaction", gt=0)
    shares: Optional[float] = Field(None, description="Number of shares", ge=0)
    amount: Optional[float] = Field(None, description="Transaction amount", ge=0)

    @model_validator(mode="after")
    def validate_shares_or_amount(self):
        """Validate that at least one of shares or amount is provided."""
        if self.shares is None and self.amount is None:
            raise ValueError("Either shares or amount must be provided")
        if self.shares is not None and self.amount is not None:
            # Both provided, check consistency
            expected_amount = round(self.shares * self.nav, 2)
            if abs(expected_amount - self.amount) > 0.01:
                raise ValueError(f"Amount {self.amount} inconsistent with shares {self.shares} * nav {self.nav}")
        return self


class FundTransactionCreate(FundTransactionBase):
    """Request model for creating a transaction."""
    pass


class FundTransactionUpdate(BaseModel):
    """Request model for updating a transaction."""
    transaction_date: Optional[date] = None
    nav: Optional[float] = Field(None, gt=0)
    shares: Optional[float] = Field(None, ge=0)
    amount: Optional[float] = Field(None, ge=0)


class FundTransaction(FundTransactionBase):
    """Transaction response model."""
    id: int = Field(..., description="Transaction ID")
    portfolio_id: str = Field(..., description="Portfolio ID")
    fund_code: str = Field(..., description="Fund code")
    fund_name: str = Field(..., description="Fund name")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class FundTransactionList(BaseModel):
    """Response model for transaction list."""
    transactions: List[FundTransaction] = Field(default_factory=list)
    total: int = Field(..., description="Total count")


class TransactionSummary(BaseModel):
    """Summary of transactions for a fund."""
    fund_code: str
    fund_name: str
    total_bought_shares: float
    total_sold_shares: float
    current_shares: float
    total_bought_amount: float
    total_sold_amount: float
    net_investment: float
