"""
Fund valuation calculation engine with smart completion based on benchmark.
"""
from typing import List, Optional, Dict
from datetime import datetime
from app.models import Fund, StockPrice, ValuationResult, HoldingContribution, FundHolding
from app.services.stock_service import stock_service
from app.services.fund_service import fund_service
from app.services.wind_client import wind_client
from app.utils.cache import cache
from app.utils.benchmark_parser import parse_benchmark, get_default_benchmark
from app.config import get_settings


class ValuationEngine:
    """Engine for calculating fund real-time valuation with smart completion."""

    def __init__(self):
        self.settings = get_settings()
        self.stock_service = stock_service
        self.fund_service = fund_service

    def _get_completion_index(self, fund_type: str) -> tuple[str, str]:
        """
        Get the appropriate index for remaining position estimation.

        Args:
            fund_type: Fund type category

        Returns:
            Tuple of (index_code, index_name)
        """
        mapping = self.settings.fund_type_mapping.get(fund_type)
        if mapping:
            return mapping["index"], mapping["index_name"]
        return self.settings.default_index, self.settings.default_index_name

    async def calculate_valuation(self, fund_code: str) -> Optional[ValuationResult]:
        """
        Calculate real-time valuation for a fund using smart completion
        based on benchmark parsing.

        Args:
            fund_code: Fund code

        Returns:
            ValuationResult object or None
        """
        cache_key = f"valuation_{fund_code}"
        cached = cache.get("valuation", cache_key, self.settings.cache_ttl_valuation)
        if cached:
            # Convert holdings_details back to HoldingContribution objects
            result_data = cached.copy()
            if "holdings_details" in result_data:
                result_data["holdings_details"] = [
                    HoldingContribution(**h) for h in result_data["holdings_details"]
                ]
            return ValuationResult(**result_data)

        try:
            # Step 1: Get fund holdings
            fund = await self.fund_service.get_fund_holdings(fund_code)
            if not fund:
                return None

            if not fund.top10_holdings:
                return ValuationResult(
                    fund_code=fund_code,
                    fund_name=fund.fund_name,
                    estimated_nav=fund.nav or 0,
                    estimated_change_percent=0,
                    top10_contribution=0,
                    top10_weight=0,
                    disclaimer="该基金暂无持仓数据"
                )

            # Step 2: Get fund info and benchmark
            fund_info = await self.fund_service.get_fund_info(fund_code)
            benchmark_str = fund_info.benchmark if fund_info else None

            # Parse benchmark for smart completion
            benchmark = parse_benchmark(benchmark_str) if benchmark_str else get_default_benchmark()

            # Step 3: Get real-time prices for top 10 holdings
            stock_codes = [h.stock_code for h in fund.top10_holdings]
            stock_prices = await self.stock_service.get_batch_stock_prices(stock_codes)

            # Step 4: Calculate contribution of each holding
            holdings_details = []
            top10_contribution = 0.0
            top10_stock_weight = 0.0

            for holding in fund.top10_holdings:
                price_info = stock_prices.get(holding.stock_code)
                if price_info:
                    change_pct = price_info.change_percent
                    contribution = (holding.weight / 100) * change_pct

                    holdings_details.append(HoldingContribution(
                        stock_code=holding.stock_code,
                        stock_name=holding.stock_name or price_info.stock_name,
                        weight=holding.weight,
                        change_percent=change_pct,
                        contribution=contribution
                    ))
                    top10_contribution += contribution
                    top10_stock_weight += holding.weight

            # Step 5: Smart completion based on asset allocation
            # Get actual asset allocation from Wind/AKShare
            asset_allocations = wind_client.get_asset_allocation_history(fund_code, quarters=1)
            if asset_allocations:
                stock_ratio = asset_allocations[0].stock_ratio
                bond_ratio = asset_allocations[0].bond_ratio
            else:
                # Fall back to disclosed holdings
                stock_ratio = fund.total_stock_ratio
                bond_ratio = fund.total_bond_ratio

            # Calculate remaining weights that need completion
            remaining_stock_weight = max(0, stock_ratio - top10_stock_weight)
            remaining_bond_weight = max(0, bond_ratio - fund.bond_total_weight)

            # Track completion details
            completion_details = []
            remaining_contribution = 0.0
            completion_index = None
            completion_index_change = None

            # Stock completion using benchmark stock index
            if remaining_stock_weight > 0 and benchmark.stock_index_code:
                stock_index_change = await self.stock_service.get_index_change(
                    benchmark.stock_index_code
                )
                stock_completion_contrib = (remaining_stock_weight / 100) * stock_index_change
                remaining_contribution += stock_completion_contrib

                completion_details.append({
                    "type": "stock",
                    "weight": remaining_stock_weight,
                    "index": f"{benchmark.stock_index_name}({benchmark.stock_index_code})",
                    "index_change": stock_index_change,
                    "contribution": stock_completion_contrib
                })

                if not completion_index:
                    completion_index = f"{benchmark.stock_index_name}(股票补全)"
                    completion_index_change = stock_index_change

            # Bond completion using benchmark bond index
            if remaining_bond_weight > 0 and benchmark.bond_index_code:
                bond_index_change = await self.stock_service.get_index_change(
                    benchmark.bond_index_code
                )
                bond_completion_contrib = (remaining_bond_weight / 100) * bond_index_change
                remaining_contribution += bond_completion_contrib

                completion_details.append({
                    "type": "bond",
                    "weight": remaining_bond_weight,
                    "index": f"{benchmark.bond_index_name}({benchmark.bond_index_code})",
                    "index_change": bond_index_change,
                    "contribution": bond_completion_contrib
                })

            # If no benchmark available, fall back to industry-based completion
            if not completion_details and remaining_stock_weight > 0:
                fund_type = self.stock_service.detect_fund_type(fund.fund_name)
                index_code, index_name = self._get_completion_index(fund_type)
                completion_index = f"{index_name}({index_code})"

                completion_index_change = await self.stock_service.get_index_change(index_code)
                remaining_contribution = (remaining_stock_weight / 100) * completion_index_change

                completion_details.append({
                    "type": "fallback",
                    "weight": remaining_stock_weight,
                    "index": completion_index,
                    "index_change": completion_index_change,
                    "contribution": remaining_contribution
                })

            # Step 6: Calculate total estimated change
            estimated_change = top10_contribution + remaining_contribution

            # Step 7: Calculate estimated NAV
            latest_nav = fund.nav
            estimated_nav = 0.0

            if latest_nav:
                estimated_nav = latest_nav * (1 + estimated_change / 100)
            else:
                # If no NAV available, use a placeholder calculation
                estimated_nav = 1.0 * (1 + estimated_change / 100)

            # Build completion method description
            if completion_details:
                completion_parts = []
                for detail in completion_details:
                    if detail["type"] == "stock":
                        completion_parts.append(f"股票:{benchmark.stock_index_name or '沪深300'}")
                    elif detail["type"] == "bond":
                        completion_parts.append(f"债券:{benchmark.bond_index_name or '中证全债'}")
                    elif detail["type"] == "fallback":
                        completion_parts.append(f"行业指数:{completion_index or 'N/A'}")
                completion_method = "+".join(completion_parts) if completion_parts else "无补全"
            else:
                completion_method = "无补全"

            # Create result
            result = ValuationResult(
                fund_code=fund_code,
                fund_name=fund.fund_name,
                latest_nav=latest_nav,
                nav_date=fund.nav_date.isoformat() if fund.nav_date else None,
                estimated_nav=round(estimated_nav, 4),
                estimated_change_percent=round(estimated_change, 2),
                top10_contribution=round(top10_contribution, 2),
                top10_weight=round(top10_stock_weight, 2),
                remaining_contribution=round(remaining_contribution, 2),
                remaining_weight=round(remaining_stock_weight + remaining_bond_weight, 2),
                holdings_details=holdings_details,
                completion_method=completion_method,
                completion_index=completion_index,
                completion_index_change=round(completion_index_change, 2) if completion_index_change else None,
                calculation_time=datetime.now(),
                report_date=fund.report_date.isoformat() if fund.report_date else None,
            )

            # Cache the result
            cache.set("valuation", cache_key, result.model_dump(),
                     self.settings.cache_ttl_valuation)

            return result

        except Exception as e:
            print(f"Error calculating valuation for {fund_code}: {e}")
            return None

    async def calculate_batch_valuation(self, fund_codes: List[str]) -> List[ValuationResult]:
        """
        Calculate valuation for multiple funds.

        Args:
            fund_codes: List of fund codes

        Returns:
            List of ValuationResult objects
        """
        results = []
        for code in fund_codes:
            result = await self.calculate_valuation(code)
            if result:
                results.append(result)
        return results


# Singleton instance
valuation_engine = ValuationEngine()
