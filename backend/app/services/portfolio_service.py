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
from app.db_models.fund_nav_cache import FundNavCacheDB
from app.db_models.portfolio_return_cache import PortfolioReturnCacheDB
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
            # Get current total shares from transaction records only
            # Note: We calculate from transactions rather than holding.shares
            # to maintain consistency and avoid double counting
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
            # Note: We don't add holding.shares here because:
            # 1. When fund is first added, holding.shares is 0
            # 2. All share changes come from transactions which update holding.shares
            # 3. Adding holding.shares would cause double counting

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

        # Invalidate portfolio cache from transaction date
        await cls.invalidate_portfolio_cache(db, portfolio_id, data.transaction_date)

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
            # Calculate what the shares would be after deletion
            if transaction.transaction_type == 'buy':
                new_shares = holding.shares - transaction.shares
                # Check if deletion would result in negative shares
                if new_shares < 0:
                    raise ValueError(
                        f"Cannot delete this buy transaction: it would result in negative shares ({new_shares}). "
                        f"You may have already sold some of these shares. "
                        f"Current shares: {holding.shares}, Transaction shares: {transaction.shares}"
                    )
                holding.shares = new_shares
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

        # Invalidate portfolio cache from transaction date
        await cls.invalidate_portfolio_cache(db, portfolio_id, transaction.transaction_date)

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
        period: str = '30d',
        use_cache: bool = True
    ) -> Optional[dict]:
        """Get portfolio historical value and return data.

        Args:
            db: Database session
            portfolio_id: Portfolio ID
            period: Time period ('30d', '60d', '6m', 'ytd')
            use_cache: Whether to use cache (default True)
        """
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

        # Try to get from cache first
        cached_data = []
        if use_cache:
            cached_data = await cls._get_cached_portfolio_returns(db, portfolio_id, start_date, end_date)
            if cached_data:
                print(f"[Cache Hit] Portfolio {portfolio_id}: {len(cached_data)} days cached")

        # Build set of cached dates
        cached_dates = {item['date'] for item in cached_data}

        # Generate all dates in range
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

        # Find missing dates
        missing_dates = [d for d in all_dates if d not in cached_dates]

        if not missing_dates:
            # All data is cached, return cached data
            return {
                'portfolio_id': portfolio_id,
                'period': period,
                'data': sorted(cached_data, key=lambda x: x['date'])
            }

        print(f"[Cache Miss] Portfolio {portfolio_id}: {len(missing_dates)} days need calculation")

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
        # Structure: {fund_code: {date_str: {'nav': float, 'is_estimated': bool, 'actual_date': str}}}
        fund_nav_history = {}
        # Structure: {date_str: {'shares': {fund_code: shares}, 'values': {fund_code: market_value}, 'costs': {}, 'cash_flow': {}}}
        daily_data = {}

        # Only calculate for missing dates
        for date_str in sorted(missing_dates):
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            daily_data[date_str] = {'shares': {}, 'values': {}, 'costs': {}, 'cash_flow': 0, 'is_estimated': False}

            # Calculate cash flow for this date (buy = negative, sell = positive)
            daily_cash_flow = sum(
                -tx.amount for tx in transactions
                if tx.transaction_type == 'buy' and tx.transaction_date == current_date
            ) + sum(
                tx.amount for tx in transactions
                if tx.transaction_type == 'sell' and tx.transaction_date == current_date
            )
            daily_data[date_str]['cash_flow'] = daily_cash_flow

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

                    # Get NAV for this date (with fallback to previous trading day)
                    try:
                        nav_result = await cls._get_nav_for_date_safe(
                            db, holding.fund_code, current_date
                        )

                        if nav_result['nav'] and nav_result['nav'] > 0:
                            if holding.fund_code not in fund_nav_history:
                                fund_nav_history[holding.fund_code] = {}
                            fund_nav_history[holding.fund_code][date_str] = nav_result

                            daily_data[date_str]['values'][holding.fund_code] = shares * nav_result['nav']

                            # Mark as estimated if any fund uses estimated NAV
                            if nav_result['is_estimated']:
                                daily_data[date_str]['is_estimated'] = True
                    except Exception as e:
                        print(f"Error getting NAV for {holding.fund_code} on {date_str}: {e}")

        # Second pass: Calculate returns and profits
        history_data = []
        sorted_dates = sorted(daily_data.keys())

        # For TWR calculation: track sub-period returns between cash flows
        sub_period_start_value = None
        sub_period_start_index = 0

        for i, date_str in enumerate(sorted_dates):
            data = daily_data[date_str]
            total_value = sum(data['values'].values())
            total_cost = sum(data['costs'].values())
            total_profit = total_value - total_cost

            # Calculate daily profit: today's value - yesterday's value - cash_flow
            daily_profit = 0.0
            if i > 0:
                prev_date = sorted_dates[i - 1]
                prev_value = sum(daily_data[prev_date]['values'].values())
                daily_profit = total_value - prev_value - data['cash_flow']

            # Simple Return Rate: (Total Value - Total Cost) / Total Cost
            simple_return = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0.0

            # TWR (Time-Weighted Return) calculation
            # TWR = product of (1 + sub_period_return) - 1
            twr = simple_return  # Default to simple return if no cash flows

            # Calculate daily TWR component based on NAV changes (not cash flows)
            daily_nav_return = 0.0
            total_weight = 0.0

            for fund_code, market_value in data['values'].items():
                if market_value > 0:
                    weight = market_value / total_value if total_value > 0 else 0
                    total_weight += weight

                    # Get previous day's NAV for this fund
                    if i > 0:
                        prev_date = sorted_dates[i - 1]
                        prev_nav_data = fund_nav_history.get(fund_code, {}).get(prev_date)
                        curr_nav_data = fund_nav_history.get(fund_code, {}).get(date_str)

                        if prev_nav_data and curr_nav_data and prev_nav_data['nav'] > 0:
                            fund_return = (curr_nav_data['nav'] - prev_nav_data['nav']) / prev_nav_data['nav'] * 100
                            daily_nav_return += weight * fund_return

            # Calculate cumulative TWR from daily NAV returns
            if i == 0:
                twr = 0.0
            else:
                prev_data = history_data[i - 1]
                prev_twr = prev_data.get('twr', 0.0)
                # TWR compounds: (1 + r1) * (1 + r2) - 1
                twr = ((1 + prev_twr / 100) * (1 + daily_nav_return / 100) - 1) * 100

            # XIRR calculation (simplified - using simple return as approximation)
            # Full XIRR requires solving for rate where NPV = 0
            # For now, we approximate with annualized simple return
            days_since_start = i
            if days_since_start > 0 and simple_return != 0:
                # Annualized return: (1 + r)^(365/days) - 1
                xirr = ((1 + simple_return / 100) ** (365 / days_since_start) - 1) * 100
            else:
                xirr = None

            history_item = {
                'date': date_str,
                'total_value': round(total_value, 2),
                'total_cost': round(total_cost, 2),
                'total_profit': round(total_profit, 2),
                'daily_profit': round(daily_profit, 2),
                'return_rate': round(simple_return, 4),  # Simple return (main metric)
                'twr': round(twr, 4),  # Time-Weighted Return
                'xirr': round(xirr, 4) if xirr is not None else None,  # Money-Weighted Return
                'is_estimated': data['is_estimated'],
            }

            history_data.append(history_item)

        # Save newly calculated data to cache
        if history_data:
            await cls._save_portfolio_returns_to_cache(db, portfolio_id, history_data)
            print(f"[Cache Saved] Portfolio {portfolio_id}: {len(history_data)} days saved to cache")

        # Merge cached data and newly calculated data
        all_data = cached_data + history_data

        # Sort by date and return
        return {
            'portfolio_id': portfolio_id,
            'period': period,
            'data': sorted(all_data, key=lambda x: x['date'])
        }

    @classmethod
    async def _get_nav_for_date_safe(
        cls,
        db: AsyncSession,
        fund_code: str,
        date: datetime.date
    ) -> dict:
        """Get NAV for a fund on a specific date with fallback to previous trading day.

        Uses cache first, then falls back to Wind API.

        Returns:
            dict: {
                'nav': float or None,
                'is_estimated': bool,
                'actual_date': str or None  # YYYY-MM-DD format
            }
        """
        try:
            # 1. Try to get from cache first
            cached = await cls._get_cached_nav(db, fund_code, date)
            if cached:
                return cached

            # 2. Try to get NAV for the exact date from Wind API
            from app.services.wind_client import wind_client
            date_str = date.strftime('%Y%m%d')

            nav_history = await asyncio.to_thread(
                wind_client.get_nav_history,
                fund_code,
                date_str,
                date_str
            )

            if nav_history and len(nav_history) > 0:
                nav = nav_history[0].nav
                result = {
                    'nav': nav,
                    'is_estimated': False,
                    'actual_date': date.strftime('%Y-%m-%d')
                }
                # Save to cache
                await cls._save_nav_to_cache(db, fund_code, date, nav, False, None)
                return result

            # 3. If not found, look back up to 10 days for the nearest trading day
            for i in range(1, 10):
                prev_date = date - timedelta(days=i)

                # Check cache first for previous date
                cached_prev = await cls._get_cached_nav(db, fund_code, prev_date)
                if cached_prev:
                    # Save the estimated value for current date to cache
                    await cls._save_nav_to_cache(
                        db, fund_code, date,
                        cached_prev['nav'], True, prev_date
                    )
                    return {
                        'nav': cached_prev['nav'],
                        'is_estimated': True,
                        'actual_date': prev_date.strftime('%Y-%m-%d')
                    }

                # Try Wind API for previous date
                prev_date_str = prev_date.strftime('%Y%m%d')
                nav_history = await asyncio.to_thread(
                    wind_client.get_nav_history,
                    fund_code,
                    prev_date_str,
                    prev_date_str
                )

                if nav_history and len(nav_history) > 0:
                    nav = nav_history[0].nav
                    print(f"[NAV Fallback] {fund_code} on {date}: using NAV from {prev_date}")
                    # Save to cache for both the actual date and current date (as estimated)
                    await cls._save_nav_to_cache(db, fund_code, prev_date, nav, False, None)
                    await cls._save_nav_to_cache(db, fund_code, date, nav, True, prev_date)
                    return {
                        'nav': nav,
                        'is_estimated': True,
                        'actual_date': prev_date.strftime('%Y-%m-%d')
                    }

        except Exception as e:
            print(f"Error fetching NAV for {fund_code} on {date}: {e}")

        return {'nav': None, 'is_estimated': False, 'actual_date': None}

    # ==========================================================================
    # Cache Methods
    # ==========================================================================

    @classmethod
    async def _get_cached_nav(cls, db: AsyncSession, fund_code: str, date: datetime.date) -> Optional[dict]:
        """Get NAV from cache."""
        try:
            result = await db.execute(
                select(FundNavCacheDB).where(
                    FundNavCacheDB.fund_code == fund_code,
                    FundNavCacheDB.date == date
                )
            )
            cached = result.scalar_one_or_none()
            if cached and cached.nav:
                return {
                    'nav': float(cached.nav),
                    'is_estimated': cached.is_estimated,
                    'actual_date': cached.actual_date.strftime('%Y-%m-%d') if cached.actual_date else None
                }
        except Exception as e:
            print(f"Error reading NAV cache: {e}")
        return None

    @classmethod
    async def _save_nav_to_cache(cls, db: AsyncSession, fund_code: str, date: datetime.date,
                                  nav: float, is_estimated: bool, actual_date: Optional[datetime.date]):
        """Save NAV to cache."""
        try:
            # Check if exists
            result = await db.execute(
                select(FundNavCacheDB).where(
                    FundNavCacheDB.fund_code == fund_code,
                    FundNavCacheDB.date == date
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.nav = nav
                existing.is_estimated = is_estimated
                existing.actual_date = actual_date
                existing.updated_at = datetime.utcnow()
            else:
                cached = FundNavCacheDB(
                    fund_code=fund_code,
                    date=date,
                    nav=nav,
                    is_estimated=is_estimated,
                    actual_date=actual_date
                )
                db.add(cached)
            await db.flush()
        except Exception as e:
            print(f"Error saving NAV cache: {e}")

    @classmethod
    async def _get_cached_portfolio_returns(cls, db: AsyncSession, portfolio_id: str,
                                            start_date: datetime.date, end_date: datetime.date) -> List[dict]:
        """Get portfolio return data from cache."""
        try:
            result = await db.execute(
                select(PortfolioReturnCacheDB).where(
                    PortfolioReturnCacheDB.portfolio_id == portfolio_id,
                    PortfolioReturnCacheDB.date >= start_date,
                    PortfolioReturnCacheDB.date <= end_date
                ).order_by(PortfolioReturnCacheDB.date)
            )
            cached = result.scalars().all()
            return [
                {
                    'date': c.date.strftime('%Y-%m-%d'),
                    'total_value': float(c.total_value) if c.total_value else 0,
                    'total_cost': float(c.total_cost) if c.total_cost else 0,
                    'total_profit': float(c.total_profit) if c.total_profit else 0,
                    'daily_profit': float(c.daily_profit) if c.daily_profit else 0,
                    'return_rate': float(c.return_rate) if c.return_rate else 0,
                    'twr': float(c.twr) if c.twr else 0,
                    'xirr': float(c.xirr) if c.xirr else None,
                    'is_estimated': c.is_estimated,
                }
                for c in cached
            ]
        except Exception as e:
            print(f"Error reading portfolio cache: {e}")
        return []

    @classmethod
    async def _save_portfolio_returns_to_cache(cls, db: AsyncSession, portfolio_id: str, data: List[dict]):
        """Save portfolio return data to cache."""
        try:
            for item in data:
                date = datetime.strptime(item['date'], '%Y-%m-%d').date()

                result = await db.execute(
                    select(PortfolioReturnCacheDB).where(
                        PortfolioReturnCacheDB.portfolio_id == portfolio_id,
                        PortfolioReturnCacheDB.date == date
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.total_value = item['total_value']
                    existing.total_cost = item['total_cost']
                    existing.total_profit = item['total_profit']
                    existing.daily_profit = item['daily_profit']
                    existing.return_rate = item['return_rate']
                    existing.twr = item.get('twr', 0)
                    existing.xirr = item.get('xirr')
                    existing.is_estimated = item.get('is_estimated', False)
                    existing.updated_at = datetime.utcnow()
                else:
                    cached = PortfolioReturnCacheDB(
                        portfolio_id=portfolio_id,
                        date=date,
                        total_value=item['total_value'],
                        total_cost=item['total_cost'],
                        total_profit=item['total_profit'],
                        daily_profit=item['daily_profit'],
                        return_rate=item['return_rate'],
                        twr=item.get('twr', 0),
                        xirr=item.get('xirr'),
                        is_estimated=item.get('is_estimated', False)
                    )
                    db.add(cached)
            await db.flush()
        except Exception as e:
            print(f"Error saving portfolio cache: {e}")

    @classmethod
    async def invalidate_portfolio_cache(cls, db: AsyncSession, portfolio_id: str, from_date: Optional[datetime.date] = None):
        """Invalidate portfolio return cache from a specific date.

        Call this when new transactions are added to ensure cache is recalculated.
        """
        try:
            query = delete(PortfolioReturnCacheDB).where(
                PortfolioReturnCacheDB.portfolio_id == portfolio_id
            )
            if from_date:
                query = query.where(PortfolioReturnCacheDB.date >= from_date)

            result = await db.execute(query)
            await db.flush()
            print(f"[Cache] Invalidated {result.rowcount} cached entries for portfolio {portfolio_id}")
        except Exception as e:
            print(f"Error invalidating portfolio cache: {e}")


portfolio_service = PortfolioService()
