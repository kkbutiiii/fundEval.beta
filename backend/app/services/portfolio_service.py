"""
Portfolio service for CRUD operations.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db_models.portfolio import PortfolioDB, PortfolioHoldingDB
from app.models.portfolio import (
    Portfolio, PortfolioCreate, PortfolioUpdate,
    PortfolioFund, PortfolioFundCreate, PortfolioFundUpdate,
    PortfolioDetail, PortfolioSummary, PortfolioFundWithValue,
    BatchAddFundsResponse
)
from app.services.estimation_api_client import get_estimation_client


class PortfolioService:
    """Service class for portfolio operations."""

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique portfolio ID."""
        return f"portfolio_{datetime.utcnow().timestamp()}_{id(object())}"

    @staticmethod
    def _db_to_model(db_portfolio: PortfolioDB) -> Portfolio:
        """Convert database model to Pydantic model."""
        # Handle holdings - may be already loaded or need to be accessed carefully
        funds = []
        if hasattr(db_portfolio, 'holdings'):
            # Check if holdings are already loaded to avoid lazy loading in async
            if isinstance(db_portfolio.holdings, list):
                funds = [
                    PortfolioFund(
                        fund_code=h.fund_code,
                        fund_name=h.fund_name,
                        shares=h.shares
                    )
                    for h in db_portfolio.holdings
                ]
        return Portfolio(
            id=db_portfolio.id,
            name=db_portfolio.name,
            funds=funds,
            created_at=db_portfolio.created_at,
            updated_at=db_portfolio.updated_at
        )

    @classmethod
    async def get_all_portfolios(cls, db: AsyncSession) -> List[Portfolio]:
        """Get all portfolios."""
        result = await db.execute(
            select(PortfolioDB)
            .options(selectinload(PortfolioDB.holdings))
            .order_by(PortfolioDB.created_at.desc())
        )
        portfolios = result.scalars().all()
        return [cls._db_to_model(p) for p in portfolios]

    @classmethod
    async def get_portfolio(cls, db: AsyncSession, portfolio_id: str) -> Optional[Portfolio]:
        """Get a portfolio by ID."""
        result = await db.execute(
            select(PortfolioDB)
            .options(selectinload(PortfolioDB.holdings))
            .where(PortfolioDB.id == portfolio_id)
        )
        db_portfolio = result.scalar_one_or_none()
        if db_portfolio:
            return cls._db_to_model(db_portfolio)
        return None

    @classmethod
    async def create_portfolio(cls, db: AsyncSession, data: PortfolioCreate) -> Portfolio:
        """Create a new portfolio."""
        db_portfolio = PortfolioDB(
            id=cls._generate_id(),
            name=data.name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_portfolio)
        await db.flush()
        # Refresh to load the object with any defaults from DB
        await db.refresh(db_portfolio)
        # Eager load holdings (empty for new portfolio)
        result = await db.execute(
            select(PortfolioDB)
            .options(selectinload(PortfolioDB.holdings))
            .where(PortfolioDB.id == db_portfolio.id)
        )
        db_portfolio = result.scalar_one()
        return cls._db_to_model(db_portfolio)

    @classmethod
    async def update_portfolio(
        cls, db: AsyncSession, portfolio_id: str, data: PortfolioUpdate
    ) -> Optional[Portfolio]:
        """Update a portfolio name."""
        result = await db.execute(
            select(PortfolioDB)
            .options(selectinload(PortfolioDB.holdings))
            .where(PortfolioDB.id == portfolio_id)
        )
        db_portfolio = result.scalar_one_or_none()
        if not db_portfolio:
            return None

        db_portfolio.name = data.name
        db_portfolio.updated_at = datetime.utcnow()
        await db.flush()
        return cls._db_to_model(db_portfolio)

    @classmethod
    async def delete_portfolio(cls, db: AsyncSession, portfolio_id: str) -> bool:
        """Delete a portfolio."""
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        db_portfolio = result.scalar_one_or_none()
        if not db_portfolio:
            return False

        await db.delete(db_portfolio)
        await db.flush()
        return True

    @classmethod
    async def add_fund(
        cls, db: AsyncSession, portfolio_id: str, data: PortfolioFundCreate
    ) -> Optional[PortfolioFund]:
        """Add a fund to a portfolio."""
        # Check if portfolio exists
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        db_portfolio = result.scalar_one_or_none()
        if not db_portfolio:
            return None

        # Check if fund already exists in portfolio
        result = await db.execute(
            select(PortfolioHoldingDB).where(
                PortfolioHoldingDB.portfolio_id == portfolio_id,
                PortfolioHoldingDB.fund_code == data.fund_code
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Update shares if fund already exists
            existing.shares = data.shares
            existing.updated_at = datetime.utcnow()
            await db.flush()
            return PortfolioFund(
                fund_code=existing.fund_code,
                fund_name=existing.fund_name,
                shares=existing.shares
            )

        # Create new holding
        holding = PortfolioHoldingDB(
            portfolio_id=portfolio_id,
            fund_code=data.fund_code,
            fund_name=data.fund_name,
            shares=data.shares,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(holding)

        # Update portfolio updated_at
        db_portfolio.updated_at = datetime.utcnow()
        await db.flush()

        return PortfolioFund(
            fund_code=holding.fund_code,
            fund_name=holding.fund_name,
            shares=holding.shares
        )

    @classmethod
    async def update_fund_shares(
        cls, db: AsyncSession, portfolio_id: str, fund_code: str, data: PortfolioFundUpdate
    ) -> Optional[PortfolioFund]:
        """Update fund shares in a portfolio."""
        result = await db.execute(
            select(PortfolioHoldingDB).where(
                PortfolioHoldingDB.portfolio_id == portfolio_id,
                PortfolioHoldingDB.fund_code == fund_code
            )
        )
        holding = result.scalar_one_or_none()
        if not holding:
            return None

        holding.shares = data.shares
        holding.updated_at = datetime.utcnow()

        # Update portfolio updated_at
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        db_portfolio = result.scalar_one_or_none()
        if db_portfolio:
            db_portfolio.updated_at = datetime.utcnow()

        await db.flush()

        return PortfolioFund(
            fund_code=holding.fund_code,
            fund_name=holding.fund_name,
            shares=holding.shares
        )

    @classmethod
    async def remove_fund(
        cls, db: AsyncSession, portfolio_id: str, fund_code: str
    ) -> bool:
        """Remove a fund from a portfolio."""
        result = await db.execute(
            select(PortfolioHoldingDB).where(
                PortfolioHoldingDB.portfolio_id == portfolio_id,
                PortfolioHoldingDB.fund_code == fund_code
            )
        )
        holding = result.scalar_one_or_none()
        if not holding:
            return False

        await db.delete(holding)

        # Update portfolio updated_at
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        db_portfolio = result.scalar_one_or_none()
        if db_portfolio:
            db_portfolio.updated_at = datetime.utcnow()

        await db.flush()
        return True

    @classmethod
    async def batch_add_funds(
        cls, db: AsyncSession, portfolio_id: str, funds: List[PortfolioFundCreate]
    ) -> BatchAddFundsResponse:
        """Batch add funds to a portfolio."""
        # Check if portfolio exists
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        db_portfolio = result.scalar_one_or_none()
        if not db_portfolio:
            return BatchAddFundsResponse(
                success=False,
                added_count=0,
                skipped_count=0,
                message="Portfolio not found"
            )

        # Get existing fund codes
        result = await db.execute(
            select(PortfolioHoldingDB.fund_code).where(
                PortfolioHoldingDB.portfolio_id == portfolio_id
            )
        )
        existing_codes = {row[0] for row in result.all()}

        added_count = 0
        skipped_count = 0

        for fund in funds:
            if fund.fund_code in existing_codes:
                skipped_count += 1
                continue

            holding = PortfolioHoldingDB(
                portfolio_id=portfolio_id,
                fund_code=fund.fund_code,
                fund_name=fund.fund_name,
                shares=fund.shares,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(holding)
            existing_codes.add(fund.fund_code)
            added_count += 1

        if added_count > 0:
            db_portfolio.updated_at = datetime.utcnow()

        await db.flush()

        return BatchAddFundsResponse(
            success=True,
            added_count=added_count,
            skipped_count=skipped_count,
            message=f"Added {added_count} funds, skipped {skipped_count} duplicates"
        )

    @classmethod
    async def get_portfolio_with_values(
        cls, db: AsyncSession, portfolio_id: str
    ) -> Optional[PortfolioDetail]:
        """Get portfolio with real-time fund values."""
        # Get portfolio
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        db_portfolio = result.scalar_one_or_none()
        if not db_portfolio:
            return None

        # Get real-time data for all funds
        fund_codes = [h.fund_code for h in db_portfolio.holdings]
        estimations = {}

        if fund_codes:
            try:
                client = get_estimation_client()
                estimations_list = await client.get_batch_estimations(fund_codes)
                estimations = {e.code: e for e in estimations_list}
            except Exception as e:
                # Log error but continue without real-time data
                print(f"Error fetching estimations: {e}")

        # Build funds with values
        funds_with_values = []
        total_estimated_value = 0.0
        total_latest_value = 0.0
        total_estimated_weighted_growth = 0.0
        total_latest_weighted_growth = 0.0

        for holding in db_portfolio.holdings:
            estimation = estimations.get(holding.fund_code)

            fund_with_value = PortfolioFundWithValue(
                fund_code=holding.fund_code,
                fund_name=holding.fund_name,
                shares=holding.shares,
                estimated_nav=estimation.latest_nav if estimation else None,
                estimated_growth=estimation.latest_growth if estimation else None,
                latest_nav=estimation.latest_nav if estimation else None,
                latest_growth=estimation.latest_growth if estimation else None,
            )

            # Calculate values
            if fund_with_value.estimated_nav is not None:
                fund_with_value.estimated_value = holding.shares * fund_with_value.estimated_nav
                total_estimated_value += fund_with_value.estimated_value

            if fund_with_value.latest_nav is not None:
                fund_with_value.latest_value = holding.shares * fund_with_value.latest_nav
                total_latest_value += fund_with_value.latest_value

            # For weighted growth calculation
            if fund_with_value.estimated_growth is not None and fund_with_value.estimated_value:
                total_estimated_weighted_growth += (
                    fund_with_value.estimated_growth * fund_with_value.estimated_value
                )

            if fund_with_value.latest_growth is not None and fund_with_value.latest_value:
                total_latest_weighted_growth += (
                    fund_with_value.latest_growth * fund_with_value.latest_value
                )

            funds_with_values.append(fund_with_value)

        # Calculate weighted average growth
        total_estimated_growth = (
            total_estimated_weighted_growth / total_estimated_value
            if total_estimated_value > 0 else 0.0
        )
        total_latest_growth = (
            total_latest_weighted_growth / total_latest_value
            if total_latest_value > 0 else 0.0
        )

        summary = PortfolioSummary(
            total_estimated_value=total_estimated_value,
            total_latest_value=total_latest_value,
            total_estimated_growth=total_estimated_growth,
            total_latest_growth=total_latest_growth,
            fund_count=len(funds_with_values)
        )

        return PortfolioDetail(
            id=db_portfolio.id,
            name=db_portfolio.name,
            funds=funds_with_values,
            created_at=db_portfolio.created_at,
            updated_at=db_portfolio.updated_at,
            summary=summary
        )


portfolio_service = PortfolioService()
