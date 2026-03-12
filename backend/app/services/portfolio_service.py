"""
Portfolio service for CRUD operations.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db_models.portfolio import PortfolioDB, PortfolioHoldingDB
from app.db_models.transaction import FundTransactionDB
from app.models.portfolio import (
    Portfolio, PortfolioCreate, PortfolioUpdate,
    PortfolioFund, PortfolioFundCreate, PortfolioFundUpdate,
    PortfolioDetail, PortfolioSummary, PortfolioFundWithValue,
    BatchAddFundsResponse
)
from app.models.transaction import (
    FundTransaction, FundTransactionCreate, FundTransactionUpdate,
    FundTransactionList, TransactionSummary
)
from app.services.estimation_api_client import get_estimation_client
from app.db_models.fund_data import FundInfoDB
from app.services.fund_data_db_service import fund_data_db_service
from sqlalchemy import select as sa_select
import asyncio


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

        # Get real-time estimation data for all funds
        fund_codes = [h.fund_code for h in db_portfolio.holdings]
        estimations = {}

        if fund_codes:
            try:
                client = get_estimation_client()
                estimations_list = await client.get_batch_estimations(fund_codes)
                estimations = {e.code: e for e in estimations_list}
            except Exception as e:
                print(f"Error fetching estimations: {e}")

        # Get official NAV data from TTJJ for all funds (for accurate daily_change)
        # 【关键】最新净值必须来自天天基金网官方数据（昨日净值），而不是估算服务
        official_nav_data = {}
        if fund_codes:
            from app.services.ttjj_client import ttjj_client

            # 逐个获取基金详情，确保每个基金都有官方净值数据
            for code in fund_codes:
                detail = None
                try:
                    # 使用同步方法的异步包装
                    detail = await asyncio.to_thread(ttjj_client.get_fund_detail_info, code)
                except Exception as e:
                    print(f"Error fetching fund detail for {code}: {e}")

                if detail and detail.nav:
                    official_nav_data[code] = {
                        'nav': detail.nav,  # 昨日官方单位净值
                        'nav_date': detail.nav_date,
                        'daily_change': detail.daily_change,  # 昨日日涨跌幅
                        'fund_name': detail.fund_name
                    }
                    print(f"[TTJJ] Got official NAV for {code}: nav={detail.nav}, date={detail.nav_date}, change={detail.daily_change}%")
                else:
                    print(f"[TTJJ] Failed to get official NAV for {code}, detail={detail}")

            # Fallback: 从数据库获取缓存的净值数据（仅当TTJJ失败时）
            for code in fund_codes:
                if code not in official_nav_data or official_nav_data[code].get('nav') is None:
                    try:
                        db_fund_info = await fund_data_db_service.get_fund_info_from_db(code, db)
                        if db_fund_info and db_fund_info.nav:
                            official_nav_data[code] = {
                                'nav': db_fund_info.nav,
                                'nav_date': db_fund_info.nav_date,
                                'daily_change': None,  # 数据库可能不缓存日涨跌幅
                                'fund_name': db_fund_info.fund_name
                            }
                            print(f"[DB Fallback] Using cached NAV for {code}: {db_fund_info.nav}")
                    except Exception as e:
                        print(f"Error fetching cached NAV from DB for {code}: {e}")

        # Build funds with values
        funds_with_values = []
        total_estimated_value = 0.0
        total_latest_value = 0.0
        total_estimated_weighted_growth = 0.0
        total_latest_weighted_growth = 0.0

        for holding in db_portfolio.holdings:
            estimation = estimations.get(holding.fund_code)
            official = official_nav_data.get(holding.fund_code, {})

            # Estimation data (from estimation service)
            estimated_nav = estimation.latest_nav if estimation else None
            estimated_growth = estimation.latest_growth if estimation else None

            # Official NAV data (from database - 昨日收盘净值)
            official_nav = official.get('nav')
            official_nav_date = official.get('nav_date')

            # Format time fields
            estimation_time = None
            nav_date_str = None

            if estimation and estimation.last_time:
                try:
                    if len(estimation.last_time) > 10:
                        dt = datetime.strptime(estimation.last_time, "%Y-%m-%d %H:%M:%S")
                        estimation_time = dt.strftime("%m/%d %H:%M")
                    else:
                        estimation_time = estimation.last_time[:5]
                except:
                    estimation_time = estimation.last_time

            if official_nav_date:
                try:
                    # nav_date is string like "2026-03-10"
                    if isinstance(official_nav_date, str):
                        dt = datetime.strptime(official_nav_date, "%Y-%m-%d")
                        nav_date_str = dt.strftime("%m/%d")
                    else:
                        nav_date_str = official_nav_date.strftime("%m/%d")
                except:
                    nav_date_str = None

            # Official daily change from TTJJ (日涨跌幅)
            official_growth = official.get('daily_change')

            fund_with_value = PortfolioFundWithValue(
                fund_code=holding.fund_code,
                fund_name=holding.fund_name,
                shares=holding.shares,
                # 估算数据（实时估值）
                estimated_nav=estimated_nav,
                estimated_growth=estimated_growth,
                # 最新净值（官方昨日收盘）
                latest_nav=official_nav,
                latest_growth=official_growth,
                # 时间字段
                estimation_time=estimation_time,
                nav_date=nav_date_str,
            )

            # Calculate values
            # 【优化】当估算净值不存在时，使用最新净值计算估算市值，避免显示为0
            effective_estimated_nav = fund_with_value.estimated_nav if fund_with_value.estimated_nav is not None else fund_with_value.latest_nav
            if effective_estimated_nav is not None:
                fund_with_value.estimated_value = holding.shares * effective_estimated_nav
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

    # ==========================================================================
    # Transaction Methods
    # ==========================================================================

    @classmethod
    async def create_transaction(
        cls,
        db: AsyncSession,
        portfolio_id: str,
        fund_code: str,
        data: FundTransactionCreate,
        fund_name: Optional[str] = None
    ) -> Optional[FundTransaction]:
        """Create a buy/sell transaction for a fund in a portfolio."""
        # Check if portfolio exists
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        if not result.scalar_one_or_none():
            return None

        # Check if fund exists in portfolio
        result = await db.execute(
            select(PortfolioHoldingDB).where(
                PortfolioHoldingDB.portfolio_id == portfolio_id,
                PortfolioHoldingDB.fund_code == fund_code
            )
        )
        holding = result.scalar_one_or_none()
        if not holding:
            return None

        # Calculate shares/amount if one is missing
        if data.shares is not None and data.amount is None:
            amount = round(data.shares * data.nav, 2)
            shares = data.shares
        elif data.amount is not None and data.shares is None:
            shares = round(data.amount / data.nav, 4)
            amount = data.amount
        else:
            shares = data.shares or 0
            amount = data.amount or 0

        # For sell transactions, check if enough shares
        if data.transaction_type == 'sell':
            # Get current total shares
            result = await db.execute(
                select(FundTransactionDB).where(
                    FundTransactionDB.portfolio_id == portfolio_id,
                    FundTransactionDB.fund_code == fund_code
                )
            )
            transactions = result.scalars().all()
            total_shares = sum(
                t.shares if t.transaction_type == 'buy' else -t.shares
                for t in transactions
            )
            # Add the initial holding shares as first buy
            total_shares += holding.shares

            if shares > total_shares:
                raise ValueError(f"Insufficient shares for sale. Available: {total_shares}, Requested: {shares}")

        # Create transaction
        transaction = FundTransactionDB(
            portfolio_id=portfolio_id,
            fund_code=fund_code,
            fund_name=fund_name or holding.fund_name,
            transaction_type=data.transaction_type,
            transaction_date=data.transaction_date,
            nav=data.nav,
            shares=shares,
            amount=amount,
            created_at=datetime.utcnow()
        )
        db.add(transaction)

        # Update holding shares
        if data.transaction_type == 'buy':
            holding.shares += shares
        else:  # sell
            holding.shares -= shares

        holding.updated_at = datetime.utcnow()

        # Update portfolio updated_at
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        portfolio = result.scalar_one()
        portfolio.updated_at = datetime.utcnow()

        await db.flush()

        return FundTransaction.model_validate(transaction)

    @classmethod
    async def get_transactions(
        cls,
        db: AsyncSession,
        portfolio_id: str,
        fund_code: Optional[str] = None
    ) -> FundTransactionList:
        """Get transactions for a portfolio or specific fund."""
        query = select(FundTransactionDB).where(
            FundTransactionDB.portfolio_id == portfolio_id
        )

        if fund_code:
            query = query.where(FundTransactionDB.fund_code == fund_code)

        query = query.order_by(FundTransactionDB.transaction_date.desc())

        result = await db.execute(query)
        transactions = result.scalars().all()

        return FundTransactionList(
            transactions=[FundTransaction.model_validate(t) for t in transactions],
            total=len(transactions)
        )

    @classmethod
    async def delete_transaction(
        cls,
        db: AsyncSession,
        portfolio_id: str,
        transaction_id: int
    ) -> bool:
        """Delete a transaction and adjust holding shares."""
        result = await db.execute(
            select(FundTransactionDB).where(
                FundTransactionDB.id == transaction_id,
                FundTransactionDB.portfolio_id == portfolio_id
            )
        )
        transaction = result.scalar_one_or_none()
        if not transaction:
            return False

        # Adjust holding shares
        result = await db.execute(
            select(PortfolioHoldingDB).where(
                PortfolioHoldingDB.portfolio_id == portfolio_id,
                PortfolioHoldingDB.fund_code == transaction.fund_code
            )
        )
        holding = result.scalar_one_or_none()

        if holding:
            if transaction.transaction_type == 'buy':
                holding.shares -= transaction.shares
            else:  # sell
                holding.shares += transaction.shares
            holding.updated_at = datetime.utcnow()

        # Delete transaction
        await db.delete(transaction)

        # Update portfolio updated_at
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()
        if portfolio:
            portfolio.updated_at = datetime.utcnow()

        await db.flush()
        return True

    @classmethod
    async def get_transaction_summary(
        cls,
        db: AsyncSession,
        portfolio_id: str,
        fund_code: str
    ) -> Optional[TransactionSummary]:
        """Get transaction summary for a specific fund."""
        result = await db.execute(
            select(PortfolioHoldingDB).where(
                PortfolioHoldingDB.portfolio_id == portfolio_id,
                PortfolioHoldingDB.fund_code == fund_code
            )
        )
        holding = result.scalar_one_or_none()
        if not holding:
            return None

        result = await db.execute(
            select(FundTransactionDB).where(
                FundTransactionDB.portfolio_id == portfolio_id,
                FundTransactionDB.fund_code == fund_code
            )
        )
        transactions = result.scalars().all()

        total_bought_shares = sum(
            t.shares for t in transactions if t.transaction_type == 'buy'
        )
        total_sold_shares = sum(
            t.shares for t in transactions if t.transaction_type == 'sell'
        )
        total_bought_amount = sum(
            t.amount for t in transactions if t.transaction_type == 'buy'
        )
        total_sold_amount = sum(
            t.amount for t in transactions if t.transaction_type == 'sell'
        )

        return TransactionSummary(
            fund_code=fund_code,
            fund_name=holding.fund_name,
            total_bought_shares=total_bought_shares,
            total_sold_shares=total_sold_shares,
            current_shares=holding.shares,
            total_bought_amount=total_bought_amount,
            total_sold_amount=total_sold_amount,
            net_investment=total_bought_amount - total_sold_amount
        )

    # ==========================================================================
    # Historical Value and Return Methods
    # ==========================================================================

    @classmethod
    async def get_portfolio_history(
        cls,
        db: AsyncSession,
        portfolio_id: str,
        period: str = '30d'
    ) -> Optional[dict]:
        """Get portfolio historical value and return data."""
        # Check if portfolio exists
        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()
        if not portfolio:
            return None

        # Calculate date range
        end_date = datetime.now().date()
        period_days = {
            '30d': 30,
            '60d': 60,
            '6m': 180,
            'ytd': (end_date - end_date.replace(month=1, day=1)).days + 1
        }
        days = period_days.get(period, 30)
        start_date = end_date - timedelta(days=days)

        # Get all holdings
        result = await db.execute(
            select(PortfolioHoldingDB).where(
                PortfolioHoldingDB.portfolio_id == portfolio_id
            )
        )
        holdings = result.scalars().all()

        if not holdings:
            return {
                'portfolio_id': portfolio_id,
                'period': period,
                'data': []
            }

        # Get all transactions for the period
        result = await db.execute(
            select(FundTransactionDB).where(
                FundTransactionDB.portfolio_id == portfolio_id,
                FundTransactionDB.transaction_date <= end_date
            )
        )
        transactions = result.scalars().all()

        # Import wind client for NAV history
        from app.services.wind_client import wind_client

        # First pass: Collect NAV history and calculate daily data
        # Structure: {fund_code: {date_str: nav_value}}
        fund_nav_history = {}
        # Structure: {date_str: {'shares': {fund_code: shares}, 'values': {fund_code: market_value}}}
        daily_data = {}

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_data[date_str] = {'shares': {}, 'values': {}, 'costs': {}}

            for holding in holdings:
                # Calculate shares held on this date
                shares = holding.shares

                # Adjust for transactions after this date
                for tx in transactions:
                    if tx.fund_code == holding.fund_code and tx.transaction_date > current_date:
                        if tx.transaction_type == 'buy':
                            shares -= tx.shares
                        else:  # sell
                            shares += tx.shares

                shares = max(0, shares)
                daily_data[date_str]['shares'][holding.fund_code] = shares

                if shares > 0:
                    # Calculate cost basis
                    cost_basis = sum(
                        tx.amount for tx in transactions
                        if tx.fund_code == holding.fund_code
                        and tx.transaction_type == 'buy'
                        and tx.transaction_date <= current_date
                    ) - sum(
                        tx.amount for tx in transactions
                        if tx.fund_code == holding.fund_code
                        and tx.transaction_type == 'sell'
                        and tx.transaction_date <= current_date
                    )
                    daily_data[date_str]['costs'][holding.fund_code] = cost_basis

                    # Get NAV for this date
                    try:
                        nav_data = await cls._get_nav_for_date(
                            db, holding.fund_code, current_date
                        )

                        if nav_data and nav_data > 0:
                            if holding.fund_code not in fund_nav_history:
                                fund_nav_history[holding.fund_code] = {}
                            fund_nav_history[holding.fund_code][date_str] = nav_data
                            daily_data[date_str]['values'][holding.fund_code] = shares * nav_data
                    except Exception as e:
                        print(f"Error getting NAV for {holding.fund_code} on {date_str}: {e}")

            current_date += timedelta(days=1)

        # Second pass: Calculate returns based on NAV changes (time-weighted)
        history_data = []
        sorted_dates = sorted(daily_data.keys())

        for i, date_str in enumerate(sorted_dates):
            data = daily_data[date_str]
            total_value = sum(data['values'].values())
            total_cost = sum(data['costs'].values())

            # Calculate return rate based on NAV changes (not cash flows)
            # This is the daily portfolio return weighted by holdings
            daily_return_rate = 0.0
            total_weight = 0.0

            for fund_code, market_value in data['values'].items():
                if market_value > 0:
                    weight = market_value / total_value if total_value > 0 else 0
                    total_weight += weight

                    # Get previous day's NAV for this fund
                    if i > 0:
                        prev_date = sorted_dates[i - 1]
                        prev_nav = fund_nav_history.get(fund_code, {}).get(prev_date)
                        curr_nav = fund_nav_history.get(fund_code, {}).get(date_str)

                        if prev_nav and curr_nav and prev_nav > 0:
                            fund_return = (curr_nav - prev_nav) / prev_nav * 100
                            daily_return_rate += weight * fund_return

            # Calculate cumulative return from start
            if i == 0:
                cumulative_return = 0.0
            else:
                # Alternative: calculate as (current_value / initial_cost - 1) * 100
                # But this includes cash flow effects
                # Use time-weighted approach: compound the daily returns
                prev_data = history_data[i - 1]
                prev_cumulative = prev_data['return_rate']
                # Simple compounding: (1 + r1/100) * (1 + r2/100) - 1
                cumulative_return = ((1 + prev_cumulative / 100) * (1 + daily_return_rate / 100) - 1) * 100

            history_data.append({
                'date': date_str,
                'total_value': round(total_value, 2),
                'total_cost': round(total_cost, 2),
                'return_rate': round(cumulative_return, 4)
            })

        return {
            'portfolio_id': portfolio_id,
            'period': period,
            'data': history_data
        }

    @classmethod
    async def _get_nav_for_date(
        cls,
        db: AsyncSession,
        fund_code: str,
        date: datetime.date
    ) -> Optional[float]:
        """Get NAV for a fund on a specific date."""
        try:
            # Try to get from FundInfoDB (cached data)
            result = await db.execute(
                select(FundInfoDB).where(FundInfoDB.fund_code == fund_code)
            )
            fund_info = result.scalar_one_or_none()

            # If we have cached NAV data and it's recent enough, use it
            if fund_info and fund_info.nav and fund_info.nav_date:
                nav_date = datetime.strptime(fund_info.nav_date, '%Y-%m-%d').date()
                # Use if within 5 days (approximation for non-trading days)
                if abs((date - nav_date).days) <= 5:
                    return fund_info.nav

            # Fallback: try Wind API for historical data
            from app.services.wind_client import wind_client
            date_str = date.strftime('%Y%m%d')

            # Use synchronous call in async context
            nav_history = await asyncio.to_thread(
                wind_client.get_nav_history,
                fund_code,
                date_str,
                date_str
            )

            if nav_history and len(nav_history) > 0:
                return nav_history[0].nav

        except Exception as e:
            print(f"Error fetching NAV for {fund_code} on {date}: {e}")

        return None


portfolio_service = PortfolioService()
