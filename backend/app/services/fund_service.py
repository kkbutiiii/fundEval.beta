"""
Fund data service using AKShare.
优先从本地数据库读取，未命中则从TTJJ API获取并缓存到数据库。
"""
import re
import asyncio
import akshare as ak
import pandas as pd
from datetime import datetime, date
from typing import List, Optional, Dict
from app.models import Fund, FundHolding, FundInfo, BondHolding, ConvertibleHolding
from app.utils.cache import cache
from app.utils.fund_list_cache import fund_list_cache
from app.config import get_settings
from app.services.ttjj_client import ttjj_client
from app.services.fund_data_db_service import fund_data_db_service
from app.database import AsyncSessionLocal


class FundService:
    """Service for fetching fund data from AKShare."""

    def __init__(self):
        self.settings = get_settings()

    def _normalize_fund_code(self, fund_code: str) -> str:
        """Normalize fund code to 6 digits."""
        return fund_code.strip().zfill(6)

    async def search_funds(self, keyword: str, limit: int = 20) -> List[FundInfo]:
        """
        Search funds by keyword (code or name).
        使用内存缓存的基金列表，响应时间 < 100ms。

        Args:
            keyword: Search keyword
            limit: Maximum number of results

        Returns:
            List of FundInfo objects
        """
        # 使用内存缓存的基金列表进行搜索（O(1) 复杂度）
        return fund_list_cache.search_funds(keyword, limit)

    async def get_fund_info(self, fund_code: str) -> Optional[FundInfo]:
        """
        Get basic fund information.

        Args:
            fund_code: Fund code

        Returns:
            FundInfo object or None
        """
        fund_code = self._normalize_fund_code(fund_code)
        cache_key = f"info_{fund_code}"
        cached = cache.get("fund_info", cache_key, self.settings.cache_ttl_fund_list)
        if cached:
            return FundInfo(**cached)

        try:
            # Get fund info from AKShare
            fund_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)

            if fund_info_df.empty:
                return None

            info_dict = dict(zip(fund_info_df["item"], fund_info_df["value"]))

            fund_info = FundInfo(
                fund_code=fund_code,
                fund_name=info_dict.get("基金简称", ""),
                fund_type=info_dict.get("基金类型", None),
                company=info_dict.get("基金管理人", None),
                manager=info_dict.get("基金经理", None),
                benchmark=info_dict.get("业绩比较基准", None),
            )

            cache.set("fund_info", cache_key, fund_info.model_dump(),
                     self.settings.cache_ttl_fund_list)

            return fund_info
        except Exception as e:
            print(f"Error getting fund info for {fund_code}: {e}")
            return None

    def _enrich_with_realtime_quotes(self, fund: Fund) -> Fund:
        """补充实时涨跌幅数据到持仓"""
        try:
            # 获取股票实时涨跌幅
            if fund.top10_holdings:
                stock_codes = [h.stock_code for h in fund.top10_holdings]
                stock_quotes = ttjj_client._get_stock_realtime_quotes(stock_codes)
                for holding in fund.top10_holdings:
                    if holding.stock_code in stock_quotes:
                        holding.change_percent = stock_quotes[holding.stock_code]

            # 获取可转债实时涨跌幅
            if fund.convertible_holdings:
                bond_codes = [h.bond_code for h in fund.convertible_holdings]
                bond_quotes = ttjj_client._get_bond_realtime_quotes(bond_codes)
                for holding in fund.convertible_holdings:
                    if holding.bond_code in bond_quotes:
                        holding.change_percent = bond_quotes[holding.bond_code]

        except Exception as e:
            print(f"[Quote] Failed to enrich realtime quotes: {e}")

        return fund

    async def get_fund_holdings(self, fund_code: str, refresh: bool = False) -> Optional[Fund]:
        """
        Get fund holdings data.
        优先从本地数据库读取，未命中则从TTJJ API获取并保存到数据库。

        Args:
            fund_code: Fund code
            refresh: Force refresh data from API, skip all cache (default: False)

        Returns:
            Fund object with holdings or None
        """
        fund_code = self._normalize_fund_code(fund_code)
        cache_key = f"holdings_{fund_code}"

        # 强制刷新模式：跳过所有缓存，直接从API获取
        if refresh:
            print(f"[Force Refresh] Fetching fund {fund_code} holdings directly from TTJJ API...")
            try:
                fund = await self._fetch_from_ttjj(fund_code)
                if fund:
                    # 保存到数据库（更新缓存）
                    try:
                        async with AsyncSessionLocal() as db:
                            await fund_data_db_service.save_fund_data_to_db(fund, db)
                            print(f"[DB] Fund {fund_code} data saved to database (force refresh)")
                    except Exception as e:
                        print(f"[DB] Failed to save to database: {e}")

                    # 存入内存缓存（更新缓存）
                    cache_data = fund.model_dump()
                    cache.set("fund_holdings", cache_key, cache_data,
                             self.settings.cache_ttl_fund_holdings)

                return fund
            except Exception as e:
                print(f"[Force Refresh] Error fetching fund {fund_code}: {e}")
                import traceback
                traceback.print_exc()
                return None

        # 1. 优先检查内存缓存
        cached = cache.get("fund_holdings", cache_key, self.settings.cache_ttl_fund_holdings)
        if cached:
            holdings_data = cached.copy()
            if "top10_holdings" in holdings_data:
                holdings_data["top10_holdings"] = [
                    FundHolding(**h) for h in holdings_data["top10_holdings"]
                ]
            if "bond_holdings" in holdings_data:
                holdings_data["bond_holdings"] = [
                    BondHolding(**h) for h in holdings_data["bond_holdings"]
                ]
            if "convertible_holdings" in holdings_data:
                holdings_data["convertible_holdings"] = [
                    ConvertibleHolding(**h) for h in holdings_data["convertible_holdings"]
                ]
            fund = Fund(**holdings_data)
            # 补充实时涨跌幅
            fund = self._enrich_with_realtime_quotes(fund)
            print(f"[Cache] Fund {fund_code} holdings loaded from memory cache")
            return fund

        # 2. 从数据库读取
        try:
            async with AsyncSessionLocal() as db:
                db_fund = await fund_data_db_service.get_fund_holdings_from_db(fund_code, db)
                if db_fund:
                    print(f"[DB] Fund {fund_code} holdings loaded from database")
                    # 补充实时涨跌幅
                    db_fund = self._enrich_with_realtime_quotes(db_fund)
                    # 存入内存缓存
                    cache_data = db_fund.model_dump()
                    cache.set("fund_holdings", cache_key, cache_data,
                             self.settings.cache_ttl_fund_holdings)
                    return db_fund
        except Exception as e:
            print(f"[DB] Failed to load from database: {e}, falling back to API")

        # 3. 从TTJJ API获取
        print(f"[API] Fetching fund {fund_code} holdings from TTJJ API...")
        try:
            fund = await self._fetch_from_ttjj(fund_code)
            if fund:
                # 保存到数据库
                try:
                    async with AsyncSessionLocal() as db:
                        await fund_data_db_service.save_fund_data_to_db(fund, db)
                        print(f"[DB] Fund {fund_code} data saved to database")
                except Exception as e:
                    print(f"[DB] Failed to save to database: {e}")

                # 存入内存缓存
                cache_data = fund.model_dump()
                cache.set("fund_holdings", cache_key, cache_data,
                         self.settings.cache_ttl_fund_holdings)

            return fund

        except Exception as e:
            print(f"Error getting fund holdings for {fund_code}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _fetch_from_ttjj(self, fund_code: str) -> Optional[Fund]:
        """从TTJJ API获取基金数据"""
        # 并行获取基金信息和各类持仓数据
        fund_info_task = self.get_fund_info(fund_code)

        def fetch_ttjj_data():
            """在后台线程中获取TTJJ数据"""
            stocks, stock_report_date = ttjj_client.get_stock_holdings(fund_code)
            # 只获取最新报告期的债券/可转债数据
            regular_bonds, convertibles, bond_report_date = ttjj_client.get_bond_holdings(fund_code, show_all=False)
            allocations = ttjj_client.get_asset_allocation(fund_code, quarters=1)
            return stocks, stock_report_date, regular_bonds, convertibles, bond_report_date, allocations

        # 并行执行TTJJ数据获取和基金信息获取
        fund_info, ttjj_result = await asyncio.gather(
            fund_info_task,
            asyncio.to_thread(fetch_ttjj_data)
        )

        ttjj_stocks, stock_report_date, regular_bonds, convertibles, bond_report_date, allocations = ttjj_result

        # 处理股票持仓
        top10_holdings = []
        report_date = None

        if ttjj_stocks:
            print(f"[API] Got {len(ttjj_stocks)} stock holdings from TTJJ")
            for stock in ttjj_stocks[:10]:
                top10_holdings.append(FundHolding(
                    stock_code=stock.stock_code,
                    stock_name=stock.stock_name,
                    weight=stock.ratio,
                    shares=stock.shares,
                    market_value=stock.market_value,
                    change_percent=stock.change_percent
                ))

        # 使用股票报告期或债券报告期
        report_date_str = stock_report_date or bond_report_date
        if report_date_str:
            try:
                year = int(report_date_str[:4])
                month = int(report_date_str[4:6])
                day = int(report_date_str[6:])
                report_date = date(year, month, day)
            except:
                pass

        top10_total_weight = sum(h.weight for h in top10_holdings)

        # 处理债券持仓
        bond_holding_models = []
        bond_total_weight = 0
        for bh in regular_bonds:
            bond_holding_models.append(BondHolding(
                bond_code=bh.bond_code,
                bond_name=bh.bond_name,
                weight=bh.ratio,
                market_value=bh.market_value,
                change_percent=bh.change_percent
            ))
            bond_total_weight += bh.ratio

        convertible_holding_models = []
        convertible_total_weight = 0
        for ch in convertibles:
            convertible_holding_models.append(ConvertibleHolding(
                bond_code=ch.bond_code,
                bond_name=ch.bond_name,
                weight=ch.ratio,
                market_value=ch.market_value,
                change_percent=ch.change_percent
            ))
            convertible_total_weight += ch.ratio

        # 验证可转债数据合理性
        if len(convertible_holding_models) > 100:
            print(f"[Warning] Abnormal convertible bond count: {len(convertible_holding_models)} (expected <= 100)")
            print(f"[Warning] Total convertible weight: {convertible_total_weight:.2f}% (should be < 100%)")
            print(f"[Suggestion] This may indicate duplicate data from multiple report periods")
        if convertible_total_weight > 100:
            print(f"[Warning] Abnormal convertible total weight: {convertible_total_weight:.2f}% > 100%")

        # 处理资产配置
        if allocations:
            total_stock_ratio = allocations[0].stock_ratio
            total_bond_ratio = allocations[0].bond_ratio
        else:
            total_stock_ratio = top10_total_weight * 1.5 if top10_total_weight > 0 else 80.0
            total_bond_ratio = bond_total_weight + convertible_total_weight

        # 获取最新净值
        nav = None
        nav_date = None
        try:
            ttjj_info = ttjj_client.get_fund_info(fund_code)
            if ttjj_info.get('nav'):
                nav = ttjj_info['nav']
                nav_date = date.today()
        except Exception:
            pass

        return Fund(
            fund_code=fund_code,
            fund_name=fund_info.fund_name if fund_info else "",
            fund_type=fund_info.fund_type if fund_info else None,
            nav=nav,
            nav_date=nav_date,
            top10_holdings=top10_holdings,
            top10_total_weight=top10_total_weight,
            total_stock_ratio=total_stock_ratio,
            total_bond_ratio=total_bond_ratio,
            bond_holdings=bond_holding_models,
            bond_total_weight=bond_total_weight,
            convertible_holdings=convertible_holding_models,
            convertible_total_weight=convertible_total_weight,
            report_date=report_date,
        )

    async def get_all_funds(self, limit: int = 100) -> List[FundInfo]:
        """
        Get list of all funds.
        使用内存缓存的基金列表。

        Args:
            limit: Maximum number of funds to return

        Returns:
            List of FundInfo objects
        """
        # 从内存缓存获取基金列表
        all_funds = fund_list_cache.get_fund_list()
        limited_funds = all_funds[:limit]

        results = []
        for fund in limited_funds:
            results.append(FundInfo(
                fund_code=fund['fund_code'],
                fund_name=fund['fund_name'],
                fund_type=fund['fund_type']
            ))

        return results


# Singleton instance
fund_service = FundService()
