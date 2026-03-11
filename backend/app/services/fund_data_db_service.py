"""
基金数据数据库查询服务
优先从本地数据库读取基金数据，未命中则从API获取并缓存到数据库
"""
from datetime import datetime, date
from typing import Optional, List
import logging

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import FundInfoDB, FundHoldingDB, AssetAllocationDB
from app.models import Fund, FundInfo, FundHolding, BondHolding, ConvertibleHolding, AssetAllocation
from app.database import AsyncSessionLocal
from app.services.ttjj_client import ttjj_client

logger = logging.getLogger(__name__)


class FundDataDBService:
    """基金数据数据库查询服务"""

    async def get_fund_info_from_db(self, fund_code: str, db: AsyncSession) -> Optional[FundInfo]:
        """
        从数据库获取基金基本信息

        Args:
            fund_code: 基金代码
            db: 数据库会话

        Returns:
            FundInfo 或 None
        """
        result = await db.execute(
            select(FundInfoDB).where(FundInfoDB.fund_code == fund_code)
        )
        db_fund = result.scalar_one_or_none()

        if not db_fund:
            return None

        return FundInfo(
            fund_code=db_fund.fund_code,
            fund_name=db_fund.fund_name,
            fund_type=db_fund.fund_type,
            company=db_fund.company,
            manager=db_fund.manager,
            benchmark=db_fund.benchmark,
            nav=db_fund.latest_nav,
            nav_date=db_fund.nav_date
        )

    async def get_fund_holdings_from_db(self, fund_code: str, db: AsyncSession) -> Optional[Fund]:
        """
        从数据库获取基金持仓数据

        Args:
            fund_code: 基金代码
            db: 数据库会话

        Returns:
            Fund 或 None
        """
        # 获取最新持仓数据
        result = await db.execute(
            select(FundHoldingDB)
            .where(FundHoldingDB.fund_code == fund_code)
            .order_by(desc(FundHoldingDB.report_date))
            .limit(1)
        )
        holding = result.scalar_one_or_none()

        if not holding:
            return None

        # 获取基金基本信息
        fund_info_result = await db.execute(
            select(FundInfoDB).where(FundInfoDB.fund_code == fund_code)
        )
        fund_info = fund_info_result.scalar_one_or_none()

        # 转换股票持仓
        top10_holdings = []
        for stock_data in holding.stock_holdings:
            top10_holdings.append(FundHolding(
                stock_code=stock_data.get("stock_code", ""),
                stock_name=stock_data.get("stock_name", ""),
                weight=stock_data.get("weight", 0),
                shares=stock_data.get("shares", 0),
                market_value=stock_data.get("market_value", 0)
            ))

        # 转换债券持仓
        bond_holdings = []
        convertible_holdings = []
        for bond_data in holding.bond_holdings:
            if bond_data.get("is_convertible"):
                convertible_holdings.append(ConvertibleHolding(
                    bond_code=bond_data.get("bond_code", ""),
                    bond_name=bond_data.get("bond_name", ""),
                    weight=bond_data.get("weight", 0),
                    market_value=bond_data.get("market_value", 0)
                ))
            else:
                bond_holdings.append(BondHolding(
                    bond_code=bond_data.get("bond_code", ""),
                    bond_name=bond_data.get("bond_name", ""),
                    weight=bond_data.get("weight", 0),
                    market_value=bond_data.get("market_value", 0)
                ))

        # 解析报告期
        report_date = None
        if holding.report_date:
            try:
                year = int(holding.report_date[:4])
                month = int(holding.report_date[4:6])
                day = int(holding.report_date[6:])
                report_date = date(year, month, day)
            except:
                pass

        return Fund(
            fund_code=fund_code,
            fund_name=fund_info.fund_name if fund_info else "",
            fund_type=fund_info.fund_type if fund_info else None,
            nav=fund_info.latest_nav if fund_info else None,
            nav_date=fund_info.nav_date if fund_info else None,
            top10_holdings=top10_holdings,
            top10_total_weight=holding.top10_total_weight,
            total_stock_ratio=holding.total_stock_ratio,
            total_bond_ratio=holding.total_bond_ratio,
            bond_holdings=bond_holdings,
            bond_total_weight=holding.bond_total_weight,
            convertible_holdings=convertible_holdings,
            convertible_total_weight=holding.convertible_total_weight,
            report_date=report_date
        )

    async def get_asset_allocation_from_db(
        self,
        fund_code: str,
        quarters: int = 8,
        db: AsyncSession = None
    ) -> List[AssetAllocation]:
        """
        从数据库获取资产配置历史

        Args:
            fund_code: 基金代码
            quarters: 获取季度数
            db: 数据库会话

        Returns:
            List[AssetAllocation]
        """
        result = await db.execute(
            select(AssetAllocationDB)
            .where(AssetAllocationDB.fund_code == fund_code)
            .order_by(desc(AssetAllocationDB.report_date))
            .limit(quarters)
        )
        allocations = result.scalars().all()

        return [
            AssetAllocation(
                report_date=a.report_date,
                stock_ratio=a.stock_ratio,
                bond_ratio=a.bond_ratio,
                cash_ratio=a.cash_ratio,
                other_ratio=a.other_ratio,
                net_asset=a.net_asset
            )
            for a in allocations
        ]

    async def save_fund_data_to_db(self, fund: Fund, db: AsyncSession) -> bool:
        """
        保存基金数据到数据库

        Args:
            fund: Fund对象
            db: 数据库会话

        Returns:
            bool: 是否成功
        """
        try:
            # 保存基本信息
            result = await db.execute(
                select(FundInfoDB).where(FundInfoDB.fund_code == fund.fund_code)
            )
            fund_info = result.scalar_one_or_none()

            if not fund_info:
                fund_info = FundInfoDB(
                    fund_code=fund.fund_code,
                    fund_name=fund.fund_name,
                    fund_type=fund.fund_type,
                    benchmark=fund.benchmark if hasattr(fund, 'benchmark') else None,
                    latest_nav=fund.nav,
                    nav_date=fund.nav_date
                )
                db.add(fund_info)
            else:
                fund_info.fund_name = fund.fund_name
                fund_info.fund_type = fund.fund_type
                fund_info.latest_nav = fund.nav
                fund_info.nav_date = fund.nav_date
                fund_info.updated_at = datetime.utcnow()

            # 保存持仓数据
            if fund.report_date:
                report_date_str = fund.report_date.strftime("%Y%m%d")

                # 检查是否已存在
                result = await db.execute(
                    select(FundHoldingDB).where(
                        and_(
                            FundHoldingDB.fund_code == fund.fund_code,
                            FundHoldingDB.report_date == report_date_str
                        )
                    )
                )
                if not result.scalar_one_or_none():
                    stock_holdings = [
                        {
                            "stock_code": h.stock_code,
                            "stock_name": h.stock_name,
                            "weight": h.weight,
                            "shares": h.shares,
                            "market_value": h.market_value
                        }
                        for h in fund.top10_holdings
                    ]

                    bond_holdings = [
                        {
                            "bond_code": h.bond_code,
                            "bond_name": h.bond_name,
                            "weight": h.weight,
                            "market_value": h.market_value,
                            "is_convertible": False
                        }
                        for h in fund.bond_holdings
                    ] + [
                        {
                            "bond_code": h.bond_code,
                            "bond_name": h.bond_name,
                            "weight": h.weight,
                            "market_value": h.market_value,
                            "is_convertible": True
                        }
                        for h in fund.convertible_holdings
                    ]

                    holding = FundHoldingDB(
                        fund_code=fund.fund_code,
                        report_date=report_date_str,
                        stock_holdings=stock_holdings,
                        bond_holdings=bond_holdings,
                        top10_total_weight=fund.top10_total_weight,
                        total_stock_ratio=fund.total_stock_ratio,
                        total_bond_ratio=fund.total_bond_ratio,
                        bond_total_weight=fund.bond_total_weight,
                        convertible_total_weight=fund.convertible_total_weight
                    )
                    db.add(holding)

            await db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to save fund data to DB: {e}")
            await db.rollback()
            return False


# 全局服务实例
fund_data_db_service = FundDataDBService()
