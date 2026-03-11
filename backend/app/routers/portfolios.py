"""
Portfolio management API router.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.portfolio import (
    Portfolio, PortfolioCreate, PortfolioUpdate,
    PortfolioFundCreate, PortfolioFundUpdate, PortfolioDetail,
    PortfolioListResponse, BatchAddFundsRequest, BatchAddFundsResponse
)
from app.services.portfolio_service import portfolio_service

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=PortfolioListResponse)
async def get_portfolios(db: AsyncSession = Depends(get_db)):
    """Get all portfolios."""
    portfolios = await portfolio_service.get_all_portfolios(db)
    return PortfolioListResponse(portfolios=portfolios, total=len(portfolios))


@router.post("", response_model=Portfolio, status_code=201)
async def create_portfolio(data: PortfolioCreate, db: AsyncSession = Depends(get_db)):
    """Create a new portfolio."""
    portfolio = await portfolio_service.create_portfolio(db, data)
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
async def get_portfolio(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    """Get a portfolio by ID with real-time values."""
    portfolio = await portfolio_service.get_portfolio_with_values(db, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.put("/{portfolio_id}", response_model=Portfolio)
async def update_portfolio(
    portfolio_id: str, data: PortfolioUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a portfolio name."""
    portfolio = await portfolio_service.update_portfolio(db, portfolio_id, data)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.delete("/{portfolio_id}", status_code=204)
async def delete_portfolio(portfolio_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a portfolio."""
    success = await portfolio_service.delete_portfolio(db, portfolio_id)
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return None


@router.post("/{portfolio_id}/funds", response_model=Portfolio)
async def add_fund_to_portfolio(
    portfolio_id: str, data: PortfolioFundCreate, db: AsyncSession = Depends(get_db)
):
    """Add a fund to a portfolio."""
    result = await portfolio_service.add_fund(db, portfolio_id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # Return the updated portfolio
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
    return portfolio


@router.put("/{portfolio_id}/funds/{fund_code}", response_model=Portfolio)
async def update_fund_shares(
    portfolio_id: str,
    fund_code: str,
    data: PortfolioFundUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update shares for a fund in a portfolio."""
    result = await portfolio_service.update_fund_shares(db, portfolio_id, fund_code, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Fund not found in portfolio")
    # Return the updated portfolio
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
    return portfolio


@router.delete("/{portfolio_id}/funds/{fund_code}", response_model=Portfolio)
async def remove_fund_from_portfolio(
    portfolio_id: str, fund_code: str, db: AsyncSession = Depends(get_db)
):
    """Remove a fund from a portfolio."""
    success = await portfolio_service.remove_fund(db, portfolio_id, fund_code)
    if not success:
        raise HTTPException(status_code=404, detail="Fund not found in portfolio")
    # Return the updated portfolio
    portfolio = await portfolio_service.get_portfolio(db, portfolio_id)
    return portfolio


@router.post("/{portfolio_id}/funds/batch", response_model=BatchAddFundsResponse)
async def batch_add_funds(
    portfolio_id: str, data: BatchAddFundsRequest, db: AsyncSession = Depends(get_db)
):
    """Batch add funds to a portfolio."""
    result = await portfolio_service.batch_add_funds(db, portfolio_id, data.funds)
    return result
