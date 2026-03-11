"""
Valuation-related Pydantic models.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StockPrice(BaseModel):
    """Real-time stock price information."""
    stock_code: str = Field(..., description="Stock code")
    stock_name: Optional[str] = Field(None, description="Stock name")
    current_price: float = Field(..., description="Current price")
    previous_close: float = Field(..., description="Previous close price")
    change_percent: float = Field(..., description="Change percent")
    update_time: Optional[datetime] = Field(None, description="Price update time")


class HoldingContribution(BaseModel):
    """Contribution of a single holding to fund performance."""
    stock_code: str = Field(..., description="Stock code")
    stock_name: str = Field(..., description="Stock name")
    weight: float = Field(..., description="Portfolio weight (%)")
    change_percent: float = Field(..., description="Stock price change (%)")
    contribution: float = Field(..., description="Contribution to fund (%)")


class ValuationResult(BaseModel):
    """Fund valuation calculation result."""
    fund_code: str = Field(..., description="Fund code")
    fund_name: Optional[str] = Field(None, description="Fund name")

    # NAV information
    latest_nav: Optional[float] = Field(None, description="Latest official NAV")
    nav_date: Optional[str] = Field(None, description="NAV date")
    estimated_nav: float = Field(..., description="Estimated current NAV")
    estimated_change_percent: float = Field(..., description="Estimated change percent")

    # Holdings contribution
    top10_contribution: float = Field(..., description="Top 10 holdings contribution (%)")
    top10_weight: float = Field(..., description="Top 10 holdings total weight (%)")
    remaining_contribution: float = Field(0.0, description="Remaining positions contribution (%)")
    remaining_weight: float = Field(0.0, description="Remaining positions weight (%)")

    # Calculation details
    holdings_details: List[HoldingContribution] = Field(default_factory=list)
    completion_method: str = Field("market_average", description="Method used for remaining positions")
    completion_index: Optional[str] = Field(None, description="Index used for remaining positions")
    completion_index_change: Optional[float] = Field(None, description="Index change percent")

    # Metadata
    calculation_time: datetime = Field(default_factory=datetime.now)
    report_date: Optional[str] = Field(None, description="Holdings report date")
    data_source: str = Field("akshare", description="Data source")

    # Disclaimer
    disclaimer: str = Field(
        "估值结果仅供参考，基于最新季报持仓数据计算，基金经理可能已调仓。投资有风险，入市需谨慎。",
        description="Valuation disclaimer"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


# =============================================================================
# External Estimation API Models (from fund_estimation_system)
# =============================================================================

class EstimationDataPoint(BaseModel):
    """Single estimation data point from TTJJ API."""
    time: str = Field(..., description="Time string (HH:MM:SS)")
    nav: float = Field(..., description="Estimated NAV")
    growth: float = Field(..., description="Estimated growth rate (%)")


class FundEstimation(BaseModel):
    """Fund estimation response from external API."""
    code: str = Field(..., description="Fund code")
    name: Optional[str] = Field(None, description="Fund name")
    date: int = Field(..., description="Date (YYYYMMDD)")
    data: List[EstimationDataPoint] = Field(default_factory=list, description="Intraday estimation data")
    count: int = Field(0, description="Number of data points")
    first_time: Optional[str] = Field(None, description="First estimation time")
    last_time: Optional[str] = Field(None, description="Last estimation time")


class EstimationSummary(BaseModel):
    """Summary of a single fund's latest estimation."""
    code: str = Field(..., description="Fund code")
    name: Optional[str] = Field(None, description="Fund name")
    date: int = Field(..., description="Date (YYYYMMDD)")
    latest_nav: Optional[float] = Field(None, description="Latest estimated NAV")
    latest_growth: Optional[float] = Field(None, description="Latest growth rate (%)")
    previous_nav: Optional[float] = Field(None, description="Previous trading day NAV")
    last_time: Optional[str] = Field(None, description="Last update time")
    data_count: int = Field(0, description="Number of data points today")


class EstimationAPIResponse(BaseModel):
    """Generic response wrapper for estimation API."""
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field("", description="Response message")
    data: Optional[FundEstimation] = Field(None, description="Estimation data")
