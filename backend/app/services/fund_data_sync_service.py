"""
基金数据同步服务
定期同步基金基本信息、持仓、资产配置到本地数据库
减少对外部API的依赖，提高响应速度
"""
import asyncio
from datetime import datetime, date
from typing import List, Optional, Dict, Tuple
import logging

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_models import (
    FundInfoDB, FundHoldingDB, AssetAllocationDB, FundDataSyncLog
)
from app.database import AsyncSessionLocal
from app.services.ttjj_client import ttjj_client, StockHolding, BondHolding
from app.utils.fund_list_cache import fund_list_cache

logger = logging.getLogger(__name__)


class FundDataSyncService:
    """基金数据同步服务"""

    def __init__(self):
        self.ttjj = ttjj_client
        self.batch_size = 50  # 每批处理的基金数量

    async def sync_single_fund(self, fund_code: str, db: AsyncSession) -> bool:
        """
        同步单个基金的数据

        Args:
            fund_code: 基金代码
            db: 数据库会话

        Returns:
            bool: 是否成功
        """
        try:
            logger.info(f"Syncing fund data for {fund_code}...")

            # 获取股票持仓
            stocks, stock_report_date = self.ttjj.get_stock_holdings(fund_code)

            # 获取债券持仓
            regular_bonds, convertibles, bond_report_date = self.ttjj.get_bond_holdings(fund_code)

            # 获取资产配置
            allocations = self.ttjj.get_asset_allocation(fund_code, quarters=1)

            # 确定报告期
            report_date = stock_report_date or bond_report_date
            if not report_date:
                logger.warning(f"No report date for {fund_code}, skipping...")
                return False

            # 检查是否已存在该报告期的数据
            existing = await db.execute(
                select(FundHoldingDB).where(
                    and_(
                        FundHoldingDB.fund_code == fund_code,
                        FundHoldingDB.report_date == report_date
                    )
                )
            )
            if existing.scalar_one_or_none():
                logger.info(f"Data for {fund_code} report {report_date} already exists, skipping...")
                return True

            # 计算统计数据
            top10_stocks = stocks[:10] if stocks else []
            top10_total_weight = sum(s.ratio for s in top10_stocks)

            bond_total_weight = sum(b.ratio for b in regular_bonds)
            convertible_total_weight = sum(c.ratio for c in convertibles)

            # 资产配置
            latest_allocation = allocations[0] if allocations else None
            total_stock_ratio = latest_allocation.stock_ratio if latest_allocation else 0
            total_bond_ratio = latest_allocation.bond_ratio if latest_allocation else 0

            # 保存或更新基金基本信息
            fund_info = await self._get_or_create_fund_info(fund_code, db)

            # 转换持仓数据为JSON格式
            stock_holdings_json = [
                {
                    "stock_code": s.stock_code,
                    "stock_name": s.stock_name,
                    "weight": s.ratio,
                    "shares": s.shares,
                    "market_value": s.market_value
                }
                for s in top10_stocks
            ]

            bond_holdings_json = [
                {
                    "bond_code": b.bond_code,
                    "bond_name": b.bond_name,
                    "weight": b.ratio,
                    "market_value": b.market_value,
                    "is_convertible": b.is_convertible
                }
                for b in (regular_bonds + convertibles)
            ]

            # 保存持仓数据
            holding = FundHoldingDB(
                fund_code=fund_code,
                report_date=report_date,
                stock_holdings=stock_holdings_json,
                bond_holdings=bond_holdings_json,
                top10_total_weight=top10_total_weight,
                total_stock_ratio=total_stock_ratio,
                total_bond_ratio=total_bond_ratio,
                bond_total_weight=bond_total_weight,
                convertible_total_weight=convertible_total_weight
            )
            db.add(holding)

            # 保存资产配置
            if latest_allocation:
                allocation = AssetAllocationDB(
                    fund_code=fund_code,
                    report_date=latest_allocation.report_date,
                    stock_ratio=latest_allocation.stock_ratio,
                    bond_ratio=latest_allocation.bond_ratio,
                    cash_ratio=latest_allocation.cash_ratio,
                    other_ratio=latest_allocation.other_ratio,
                    net_asset=latest_allocation.net_asset
                )
                db.add(allocation)

            await db.commit()
            logger.info(f"Successfully synced {fund_code} (report: {report_date})")
            return True

        except Exception as e:
            logger.error(f"Failed to sync {fund_code}: {e}")
            await db.rollback()
            return False

    async def _get_or_create_fund_info(self, fund_code: str, db: AsyncSession) -> FundInfoDB:
        """获取或创建基金基本信息"""
        result = await db.execute(
            select(FundInfoDB).where(FundInfoDB.fund_code == fund_code)
        )
        fund_info = result.scalar_one_or_none()

        if not fund_info:
            # 从TTJJ获取基金信息
            info = self.ttjj.get_fund_info(fund_code)
            fund_info = FundInfoDB(
                fund_code=fund_code,
                fund_name=info.get("name", ""),
                fund_type=None,  # TTJJ接口不返回类型，需要AKShare补充
                company=None,
                manager=None,
                benchmark=None,
                latest_nav=info.get("nav")
            )
            db.add(fund_info)
            await db.flush()

        return fund_info

    async def sync_fund_list(self, fund_codes: List[str], sync_type: str = "incremental") -> Dict:
        """
        批量同步基金数据

        Args:
            fund_codes: 基金代码列表
            sync_type: 同步类型 ('full', 'incremental', 'quarterly')

        Returns:
            Dict: 同步结果统计
        """
        logger.info(f"Starting {sync_type} sync for {len(fund_codes)} funds...")

        # 创建同步日志
        async with AsyncSessionLocal() as db:
            sync_log = FundDataSyncLog(
                sync_type=sync_type,
                status="running",
                total_funds=len(fund_codes),
                start_fund_code=fund_codes[0] if fund_codes else None,
                end_fund_code=fund_codes[-1] if fund_codes else None
            )
            db.add(sync_log)
            await db.commit()
            sync_id = sync_log.id

        # 分批处理
        success_count = 0
        failed_count = 0
        failed_codes = []

        for i in range(0, len(fund_codes), self.batch_size):
            batch = fund_codes[i:i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1}/{(len(fund_codes) + self.batch_size - 1) // self.batch_size}")

            for fund_code in batch:
                async with AsyncSessionLocal() as db:
                    success = await self.sync_single_fund(fund_code, db)
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_codes.append(fund_code)

                # 避免请求过快
                await asyncio.sleep(0.5)

        # 更新同步日志
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(FundDataSyncLog).where(FundDataSyncLog.id == sync_id)
            )
            sync_log = result.scalar_one()
            sync_log.status = "completed" if failed_count == 0 else "partial"
            sync_log.processed_funds = success_count
            sync_log.failed_funds = failed_count
            sync_log.completed_at = datetime.utcnow()
            if failed_codes:
                sync_log.error_message = f"Failed funds: {', '.join(failed_codes[:10])}..."
            await db.commit()

        logger.info(f"Sync completed: {success_count} success, {failed_count} failed")

        return {
            "sync_id": sync_id,
            "total": len(fund_codes),
            "success": success_count,
            "failed": failed_count,
            "failed_codes": failed_codes
        }

    async def sync_all_funds(self, limit: Optional[int] = None) -> Dict:
        """
        同步所有基金数据

        Args:
            limit: 限制同步数量（用于测试）

        Returns:
            Dict: 同步结果
        """
        # 从缓存获取所有基金列表
        all_funds = fund_list_cache.get_fund_list()
        fund_codes = [f["fund_code"] for f in all_funds]

        if limit:
            fund_codes = fund_codes[:limit]

        return await self.sync_fund_list(fund_codes, sync_type="full")

    async def sync_hot_funds(self, top_n: int = 1000) -> Dict:
        """
        同步热门基金（基金规模较大的前N只）

        Args:
            top_n: 同步数量

        Returns:
            Dict: 同步结果
        """
        # 获取最近有资产配置数据的基金（通常是规模较大的）
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AssetAllocationDB.fund_code)
                .order_by(desc(AssetAllocationDB.net_asset))
                .limit(top_n)
            )
            fund_codes = [row[0] for row in result.fetchall()]

        if not fund_codes:
            # 如果没有数据，同步前top_n只基金
            all_funds = fund_list_cache.get_fund_list()
            fund_codes = [f["fund_code"] for f in all_funds[:top_n]]

        return await self.sync_fund_list(fund_codes, sync_type="hot")

    async def check_and_update_outdated_funds(self) -> List[str]:
        """
        检查并获取需要更新的基金列表
        （报告期过期的基金）

        Returns:
            List[str]: 需要更新的基金代码列表
        """
        async with AsyncSessionLocal() as db:
            # 获取所有已同步的基金及其最新报告期
            result = await db.execute(
                select(
                    FundHoldingDB.fund_code,
                    FundHoldingDB.report_date
                ).distinct()
            )
            synced_funds = {row[0]: row[1] for row in result.fetchall()}

        # 获取当前应该的报告期（最近一个季度末）
        current_quarter_end = self._get_current_quarter_end()
        current_report_date = current_quarter_end.strftime("%Y%m%d")

        outdated = []
        for fund_code, report_date in synced_funds.items():
            if report_date != current_report_date:
                outdated.append(fund_code)

        logger.info(f"Found {len(outdated)} outdated funds (current report: {current_report_date})")
        return outdated

    def _get_current_quarter_end(self) -> date:
        """获取当前季度末日期"""
        today = date.today()
        quarter = (today.month - 1) // 3 + 1
        month = quarter * 3
        day = 31 if month in [3, 12] else 30
        return date(today.year, month, day)

    async def incremental_sync(self) -> Dict:
        """
        增量同步：只同步未同步过或数据过期的基金

        Returns:
            Dict: 同步结果
        """
        # 获取所有基金
        all_funds = fund_list_cache.get_fund_list()
        all_codes = {f["fund_code"] for f in all_funds}

        # 获取已同步的基金
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(FundHoldingDB.fund_code).distinct()
            )
            synced_codes = {row[0] for row in result.fetchall()}

        # 找出未同步的基金
        unsynced = list(all_codes - synced_codes)

        if unsynced:
            logger.info(f"Found {len(unsynced)} unsynced funds")
            return await self.sync_fund_list(unsynced, sync_type="incremental")

        # 如果没有新基金，检查过期数据
        outdated = await self.check_and_update_outdated_funds()
        if outdated:
            return await self.sync_fund_list(outdated, sync_type="quarterly_update")

        return {"message": "All funds are up to date", "total": 0, "success": 0, "failed": 0}


# 全局服务实例
fund_data_sync_service = FundDataSyncService()


async def run_daily_sync():
    """每日同步任务"""
    service = FundDataSyncService()
    result = await service.incremental_sync()
    logger.info(f"Daily sync result: {result}")
    return result


async def run_full_sync(limit: Optional[int] = None):
    """全量同步任务"""
    service = FundDataSyncService()
    result = await service.sync_all_funds(limit=limit)
    logger.info(f"Full sync result: {result}")
    return result
