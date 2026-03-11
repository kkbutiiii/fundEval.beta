"""
Fund-related Pydantic models.
"""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FundHolding(BaseModel):
    """Fund holding information for a single stock."""
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    weight: float = Field(..., description="Weight in portfolio (%)", ge=0, le=100)
    shares: Optional[float] = Field(None, description="Number of shares held")
    market_value: Optional[float] = Field(None, description="Market value of holding")
    change_percent: Optional[float] = Field(None, description="Stock price change percent")
    contribution: Optional[float] = Field(None, description="Contribution to fund return")


class BondHolding(BaseModel):
    """Bond holding information."""
    bond_code: str = Field(..., description="Bond code")
    bond_name: str = Field(..., description="Bond name")
    weight: float = Field(..., description="Weight in portfolio (%)", ge=0, le=100)
    market_value: Optional[float] = Field(None, description="Market value of holding (in 万元)")
    change_percent: Optional[float] = Field(None, description="Real-time price change percent (%)")


class ConvertibleHolding(BaseModel):
    """Convertible bond holding information."""
    bond_code: str = Field(..., description="Bond code")
    bond_name: str = Field(..., description="Bond name")
    weight: float = Field(..., description="Weight in portfolio (%)", ge=0, le=100)
    market_value: Optional[float] = Field(None, description="Market value of holding (in 万元)")
    change_percent: Optional[float] = Field(None, description="Real-time price change percent (%)")
    conversion_premium: Optional[float] = Field(None, description="Conversion premium rate (%)")


class AssetAllocation(BaseModel):
    """Asset allocation data for a specific report date."""
    report_date: str = Field(..., description="Report date (YYYYMMDD)")
    stock_ratio: float = Field(..., description="Stock allocation ratio (%)", ge=0, le=100)
    bond_ratio: float = Field(..., description="Bond allocation ratio (%)", ge=0, le=100)
    cash_ratio: float = Field(..., description="Cash allocation ratio (%)", ge=0, le=100)
    other_ratio: float = Field(..., description="Other assets ratio (%)", ge=0, le=100)
    net_asset: Optional[float] = Field(None, description="Net asset value (yuan)")


class FundInfo(BaseModel):
    """Basic fund information."""
    fund_code: str = Field(..., description="Fund code")
    fund_name: str = Field(..., description="Fund name")
    fund_type: Optional[str] = Field(None, description="Fund type/category")
    nav: Optional[float] = Field(None, description="Latest NAV (net asset value)")
    nav_date: Optional[date] = Field(None, description="NAV date")
    total_assets: Optional[float] = Field(None, description="Total assets under management")
    manager: Optional[str] = Field(None, description="Fund manager")
    company: Optional[str] = Field(None, description="Fund management company")
    benchmark: Optional[str] = Field(None, description="Performance benchmark")

    # Extended fields from TTJJ
    nav_change_percent: Optional[float] = Field(None, description="Daily NAV change percentage (%)")
    accumulated_nav: Optional[float] = Field(None, description="Accumulated NAV")
    risk_level: Optional[str] = Field(None, description="Risk level (e.g., 中高风险)")
    rating: Optional[int] = Field(None, description="Fund rating (1-5 stars)", ge=1, le=5)
    return_1m: Optional[float] = Field(None, description="1-month return (%)")
    return_3m: Optional[float] = Field(None, description="3-month return (%)")
    return_6m: Optional[float] = Field(None, description="6-month return (%)")
    return_1y: Optional[float] = Field(None, description="1-year return (%)")
    return_3y: Optional[float] = Field(None, description="3-year return (%)")
    return_ytd: Optional[float] = Field(None, description="Year-to-date return (%)")
    return_since_inception: Optional[float] = Field(None, description="Return since inception (%)")
    inception_date: Optional[str] = Field(None, description="Fund inception date (YYYY-MM-DD)")


class Fund(BaseModel):
    """Complete fund information including holdings."""
    fund_code: str = Field(..., description="Fund code")
    fund_name: str = Field(..., description="Fund name")
    fund_type: Optional[str] = Field(None, description="Fund type/category")
    nav: Optional[float] = Field(None, description="Latest NAV")
    nav_date: Optional[date] = Field(None, description="NAV date")
    previous_nav: Optional[float] = Field(None, description="Previous trading day NAV")
    total_stock_ratio: float = Field(85.0, description="Total stock position ratio (%)", ge=0, le=100)
    total_bond_ratio: float = Field(0.0, description="Total bond position ratio (%)", ge=0, le=100)
    top10_holdings: List[FundHolding] = Field(default_factory=list, description="Top 10 holdings")
    top10_total_weight: float = Field(0.0, description="Total weight of top 10 holdings (%)")
    bond_holdings: List[BondHolding] = Field(default_factory=list, description="Bond holdings")
    bond_total_weight: float = Field(0.0, description="Total weight of bond holdings (%)")
    convertible_holdings: List[ConvertibleHolding] = Field(default_factory=list, description="Convertible bond holdings")
    convertible_total_weight: float = Field(0.0, description="Total weight of convertible holdings (%)")
    report_date: Optional[date] = Field(None, description="Report date of holdings data")

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None,
        }


class AssetAllocationHistory(BaseModel):
    """Asset allocation history for a fund."""
    fund_code: str = Field(..., description="Fund code")
    allocations: List[AssetAllocation] = Field(default_factory=list, description="List of asset allocations by date")
