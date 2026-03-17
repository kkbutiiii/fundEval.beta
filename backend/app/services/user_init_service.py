"""
用户数据初始化服务
为新注册账号自动初始化默认数据
"""
import logging
from datetime import datetime, date
from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models.watchlist import WatchlistDB
from app.db_models.portfolio import PortfolioDB, PortfolioHoldingDB
from app.db_models.transaction import FundTransactionDB
from app.db_models.fund_data import FundInfoDB
from app.services.fund_data_db_service import fund_data_db_service

logger = logging.getLogger(__name__)


# 默认自选基金代码列表
DEFAULT_WATCHLIST_FUNDS = ["024110", "016699", "011949", "005819"]

# 案例组合配置
DEMO_PORTFOLIO_NAME = "案例组合#1"
DEMO_PORTFOLIO_FUND_CODE = "008888"

# 案例组合交易记录 (16笔)
# 格式: (shares, amount, date_str, transaction_type)
DEMO_TRANSACTIONS = [
    (10000.0, 16396.0, "2026-02-02", "sell"),
    (15000.0, 25801.0, "2026-01-30", "sell"),
    (5885.47, 10000.0, "2026-01-29", "buy"),
    (2919.03, 5000.0, "2026-01-26", "buy"),
    (2968.24, 5000.0, "2026-01-20", "buy"),
    (3265.06, 5500.0, "2026-01-20", "buy"),
    (2077.77, 3500.0, "2026-01-20", "buy"),
    (883.08, 1500.0, "2026-01-19", "buy"),
    (933.88, 1500.0, "2026-01-13", "buy"),
    (933.88, 1500.0, "2026-01-13", "buy"),
    (3070.12, 5000.0, "2026-01-08", "buy"),
    (3341.35, 5000.0, "2025-12-31", "buy"),
    (3637.95, 5000.0, "2025-11-21", "buy"),
    (3449.23, 5000.0, "2025-11-19", "buy"),
    (3352.11, 5000.0, "2025-11-05", "buy"),
    (6877.27, 10863.36, "2025-09-26", "sell"),
    (6877.27, 10111.63, "2025-09-17", "buy"),
]


class UserInitService:
    """用户数据初始化服务"""

    @staticmethod
    def _generate_portfolio_id() -> str:
        """Generate a unique portfolio ID."""
        return f"portfolio_{datetime.utcnow().timestamp()}_{id(object())}"

    @staticmethod
    async def _get_fund_name(fund_code: str, db: AsyncSession) -> str:
        """
        获取基金名称，如果不存在则返回基金代码
        """
        try:
            fund_info = await fund_data_db_service.get_fund_info_from_db(fund_code, db)
            if fund_info and fund_info.fund_name:
                return fund_info.fund_name
        except Exception as e:
            logger.warning(f"Failed to get fund info for {fund_code}: {e}")

        # 如果数据库中没有，尝试从FundInfoDB直接查询
        try:
            result = await db.execute(
                select(FundInfoDB).where(FundInfoDB.fund_code == fund_code)
            )
            db_fund = result.scalar_one_or_none()
            if db_fund and db_fund.fund_name:
                return db_fund.fund_name
        except Exception as e:
            logger.warning(f"Failed to query FundInfoDB for {fund_code}: {e}")

        return fund_code

    @staticmethod
    async def initialize_watchlist(user_id: int, db: AsyncSession) -> None:
        """
        初始化用户自选基金
        """
        for fund_code in DEFAULT_WATCHLIST_FUNDS:
            try:
                fund_name = await UserInitService._get_fund_name(fund_code, db)

                watchlist_item = WatchlistDB(
                    user_id=user_id,
                    fund_code=fund_code,
                    fund_name=fund_name
                )
                db.add(watchlist_item)
                logger.info(f"Added watchlist item: {fund_code} - {fund_name} for user {user_id}")

            except Exception as e:
                logger.error(f"Failed to add watchlist item {fund_code} for user {user_id}: {e}")
                # 继续处理下一个基金
                continue

        try:
            await db.commit()
            logger.info(f"Successfully initialized watchlist for user {user_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to commit watchlist for user {user_id}: {e}")
            raise

    @staticmethod
    async def initialize_demo_portfolio(user_id: int, db: AsyncSession) -> None:
        """
        初始化案例组合
        """
        try:
            # 获取基金名称
            fund_name = await UserInitService._get_fund_name(DEMO_PORTFOLIO_FUND_CODE, db)

            # 创建组合
            portfolio_id = UserInitService._generate_portfolio_id()
            portfolio = PortfolioDB(
                id=portfolio_id,
                name=DEMO_PORTFOLIO_NAME,
                user_id=user_id
            )
            db.add(portfolio)

            # 创建持仓记录
            # 计算总份额（买入为正，卖出为负）
            total_shares = 0.0
            for shares, amount, date_str, tx_type in DEMO_TRANSACTIONS:
                if tx_type == "buy":
                    total_shares += shares
                else:
                    total_shares -= shares

            holding = PortfolioHoldingDB(
                portfolio_id=portfolio_id,
                fund_code=DEMO_PORTFOLIO_FUND_CODE,
                fund_name=fund_name,
                shares=total_shares
            )
            db.add(holding)

            # 创建交易记录
            for shares, amount, date_str, tx_type in DEMO_TRANSACTIONS:
                nav = amount / shares if shares > 0 else 0.0
                tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                transaction = FundTransactionDB(
                    portfolio_id=portfolio_id,
                    fund_code=DEMO_PORTFOLIO_FUND_CODE,
                    fund_name=fund_name,
                    transaction_type=tx_type,
                    transaction_date=tx_date,
                    nav=round(nav, 4),
                    shares=shares,
                    amount=amount
                )
                db.add(transaction)

            await db.commit()
            logger.info(f"Successfully initialized demo portfolio for user {user_id}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to initialize demo portfolio for user {user_id}: {e}")
            raise

    @staticmethod
    async def initialize_user_data(user_id: int, db: AsyncSession) -> None:
        """
        初始化新用户的所有默认数据

        Args:
            user_id: 用户ID
            db: 数据库会话
        """
        logger.info(f"Starting initialization for user {user_id}")

        try:
            # 初始化自选基金
            await UserInitService.initialize_watchlist(user_id, db)
        except Exception as e:
            logger.error(f"Watchlist initialization failed for user {user_id}: {e}")
            # 继续尝试初始化组合

        try:
            # 初始化案例组合
            await UserInitService.initialize_demo_portfolio(user_id, db)
        except Exception as e:
            logger.error(f"Demo portfolio initialization failed for user {user_id}: {e}")

        logger.info(f"Completed initialization for user {user_id}")


# 全局服务实例
user_init_service = UserInitService()


# 便捷函数
async def initialize_user_data(user_id: int, db: AsyncSession) -> None:
    """
    初始化新用户的所有默认数据（便捷函数）

    Args:
        user_id: 用户ID
        db: 数据库会话
    """
    await user_init_service.initialize_user_data(user_id, db)
