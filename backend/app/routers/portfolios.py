"""
Portfolio management API router.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.portfolio import (
    Portfolio, PortfolioCreate, PortfolioUpdate,
    PortfolioFundCreate, PortfolioFundUpdate, PortfolioDetail,
    PortfolioListResponse, BatchAddFundsRequest, BatchAddFundsResponse
)
from app.models.transaction import (
    FundTransaction, FundTransactionCreate, FundTransactionList,
    TransactionSummary
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


# =============================================================================
# Transaction Endpoints
# =============================================================================

@router.post("/{portfolio_id}/funds/{fund_code}/transactions", response_model=FundTransaction, status_code=201)
async def create_transaction(
    portfolio_id: str,
    fund_code: str,
    data: FundTransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a buy/sell transaction for a fund in a portfolio."""
    try:
        transaction = await portfolio_service.create_transaction(
            db, portfolio_id, fund_code, data
        )
        if not transaction:
            raise HTTPException(status_code=404, detail="Portfolio or fund not found")
        return transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{portfolio_id}/transactions", response_model=FundTransactionList)
async def get_portfolio_transactions(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all transactions for a portfolio."""
    transactions = await portfolio_service.get_transactions(db, portfolio_id)
    return transactions


@router.get("/{portfolio_id}/funds/{fund_code}/transactions", response_model=FundTransactionList)
async def get_fund_transactions(
    portfolio_id: str,
    fund_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all transactions for a specific fund in a portfolio."""
    transactions = await portfolio_service.get_transactions(db, portfolio_id, fund_code)
    return transactions


@router.delete("/{portfolio_id}/transactions/{transaction_id}", status_code=204)
async def delete_transaction(
    portfolio_id: str,
    transaction_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a transaction."""
    success = await portfolio_service.delete_transaction(db, portfolio_id, transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return None


@router.get("/{portfolio_id}/funds/{fund_code}/transaction-summary", response_model=TransactionSummary)
async def get_transaction_summary(
    portfolio_id: str,
    fund_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get transaction summary for a specific fund."""
    summary = await portfolio_service.get_transaction_summary(db, portfolio_id, fund_code)
    if not summary:
        raise HTTPException(status_code=404, detail="Fund not found in portfolio")
    return summary


# =============================================================================
# Historical Value and Return Endpoints
# =============================================================================

class PortfolioHistoryResponse(BaseModel):
    """Response model for portfolio history."""
    portfolio_id: str
    period: str
    data: List[dict]


@router.get("/{portfolio_id}/history", response_model=PortfolioHistoryResponse)
async def get_portfolio_history(
    portfolio_id: str,
    period: str = Query("30d", regex="^(30d|60d|6m|ytd)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio historical value and return data.

    - **period**: Time period (30d, 60d, 6m, ytd)
    """
    history = await portfolio_service.get_portfolio_history(db, portfolio_id, period)
    if not history:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return PortfolioHistoryResponse(**history)
