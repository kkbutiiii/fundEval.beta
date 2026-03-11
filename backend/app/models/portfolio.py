"""
Portfolio Pydantic models for API request/response.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PortfolioFund(BaseModel):
    """Fund holding in a portfolio."""
    fund_code: str = Field(..., description="Fund code")
    fund_name: str = Field(..., description="Fund name")
    shares: float = Field(..., description="Number of shares held", ge=0)


class PortfolioFundCreate(BaseModel):
    """Request model for adding a fund to portfolio."""
    fund_code: str = Field(..., description="Fund code")
    fund_name: str = Field(..., description="Fund name")
    shares: float = Field(default=0, description="Number of shares held", ge=0)


class PortfolioFundUpdate(BaseModel):
    """Request model for updating fund shares."""
    shares: float = Field(..., description="Number of shares held", ge=0)


class PortfolioFundWithValue(PortfolioFund):
    """Fund holding with calculated values from real-time data."""
    estimated_nav: Optional[float] = Field(None, description="Estimated NAV")
    estimated_growth: Optional[float] = Field(None, description="Estimated change percent (%)")
    latest_nav: Optional[float] = Field(None, description="Latest NAV (yesterday close)")
    latest_growth: Optional[float] = Field(None, description="Latest change percent (%)")
    estimated_value: Optional[float] = Field(None, description="Estimated value = shares * estimated_nav")
    latest_value: Optional[float] = Field(None, description="Latest value = shares * latest_nav")


class PortfolioBase(BaseModel):
    """Base portfolio model."""
    name: str = Field(..., description="Portfolio name", min_length=1, max_length=255)


class PortfolioCreate(PortfolioBase):
    """Request model for creating a portfolio."""
    pass


class PortfolioUpdate(PortfolioBase):
    """Request model for updating a portfolio."""
    pass


class Portfolio(PortfolioBase):
    """Portfolio response model."""
    id: str = Field(..., description="Portfolio ID")
    funds: List[PortfolioFund] = Field(default_factory=list, description="List of funds")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        from_attributes = True


class PortfolioWithValues(Portfolio):
    """Portfolio with real-time fund values."""
    funds: List[PortfolioFundWithValue] = Field(default_factory=list, description="List of funds with values")


class PortfolioSummary(BaseModel):
    """Portfolio summary statistics."""
    total_estimated_value: float = Field(..., description="Total estimated value")
    total_latest_value: float = Field(..., description="Total latest value")
    total_estimated_growth: float = Field(..., description="Total estimated growth (weighted average %)")
    total_latest_growth: float = Field(..., description="Total latest growth (weighted average %)")
    fund_count: int = Field(..., description="Number of funds")


class PortfolioDetail(PortfolioWithValues):
    """Portfolio detail with summary statistics."""
    summary: PortfolioSummary = Field(..., description="Portfolio summary statistics")


class PortfolioListResponse(BaseModel):
    """Response model for portfolio list."""
    portfolios: List[Portfolio] = Field(..., description="List of portfolios")
    total: int = Field(..., description="Total count")


class BatchAddFundsRequest(BaseModel):
    """Request model for batch adding funds."""
    funds: List[PortfolioFundCreate] = Field(..., description="List of funds to add")


class BatchAddFundsResponse(BaseModel):
    """Response model for batch adding funds."""
    success: bool = Field(..., description="Whether the operation was successful")
    added_count: int = Field(..., description="Number of funds added")
    skipped_count: int = Field(..., description="Number of funds skipped (duplicates)")
    message: str = Field(..., description="Result message")
