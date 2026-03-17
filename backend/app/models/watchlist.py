"""
Watchlist Pydantic models.
"""
from datetime import datetime
from pydantic import BaseModel


class WatchlistFund(BaseModel):
    """Watchlist fund model."""
    fund_code: str
    fund_name: str
    added_at: datetime

    class Config:
        from_attributes = True


class WatchlistFundCreate(BaseModel):
    """Create watchlist fund model."""
    fund_code: str
    fund_name: str


class WatchlistFundResponse(BaseModel):
    """Watchlist fund response model."""
    fund_code: str
    fund_name: str
    added_at: datetime

    class Config:
        from_attributes = True


class WatchlistListResponse(BaseModel):
    """Watchlist list response model."""
    watchlist: list[WatchlistFundResponse]
    total: int
