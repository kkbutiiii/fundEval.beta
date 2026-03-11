"""
Stock price service using East Money API.
"""
import requests
import json
import akshare as ak
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from app.models import StockPrice
from app.utils.cache import cache
from app.config import get_settings


class StockService:
    """Service for fetching real-time stock prices from East Money."""

    # East Money API base URL
    STOCK_API_URL = "https://push2.eastmoney.com/api/qt/stock/get"
    BATCH_API_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"

    def __init__(self):
        self.settings = get_settings()

    def _get_secid(self, stock_code: str) -> str:
        """
        Get security ID for East Money API.

        Args:
            stock_code: Stock code (6 digits)

        Returns:
            Security ID in format "0.{code}" for Shenzhen, "1.{code}" for Shanghai
        """
        stock_code = stock_code.strip().zfill(6)
        # Shanghai: 600xxx, 601xxx, 603xxx, 688xxx (STAR Market)
        # Shenzhen: 000xxx, 002xxx, 300xxx (ChiNext)
        if stock_code.startswith(('6', '68', '51', '56', '58')):
            return f"1.{stock_code}"
        else:
            return f"0.{stock_code}"

    async def get_stock_price(self, stock_code: str) -> Optional[StockPrice]:
        """
        Get real-time price for a single stock.

        Args:
            stock_code: Stock code

        Returns:
            StockPrice object or None
        """
        stock_code = stock_code.strip().zfill(6)
        cache_key = f"price_{stock_code}"
        cached = cache.get("stock_price", cache_key, self.settings.cache_ttl_stock_price)
        if cached:
            return StockPrice(**cached)

        try:
            secid = self._get_secid(stock_code)

            params = {
                "secid": secid,
                "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f107,f170,f171"
            }

            response = requests.get(
                self.STOCK_API_URL,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if "data" not in data or data["data"] is None:
                return None

            stock_data = data["data"]

            # Parse East Money fields
            # f43: current price (multiply by 0.01)
            # f44: highest price
            # f45: lowest price
            # f46: open price
            # f47: volume
            # f48: amount
            # f57: stock code
            # f58: stock name
            # f60: previous close (multiply by 0.01)
            # f107: market type
            # f170: change percent (multiply by 0.01)
            # f171: change amount

            current_price = stock_data.get("f43", 0) * 0.01 if stock_data.get("f43") else 0
            previous_close = stock_data.get("f60", 0) * 0.01 if stock_data.get("f60") else 0
            change_percent = stock_data.get("f170", 0) * 0.01 if stock_data.get("f170") else 0

            stock_price = StockPrice(
                stock_code=stock_code,
                stock_name=stock_data.get("f58", ""),
                current_price=current_price,
                previous_close=previous_close,
                change_percent=change_percent,
                update_time=datetime.now()
            )

            cache.set("stock_price", cache_key, stock_price.model_dump(),
                     self.settings.cache_ttl_stock_price)

            return stock_price

        except Exception as e:
            print(f"Error getting stock price for {stock_code}: {e}")
            return None

    async def get_batch_stock_prices(self, stock_codes: List[str]) -> Dict[str, StockPrice]:
        """
        Get real-time prices for multiple stocks.

        Args:
            stock_codes: List of stock codes

        Returns:
            Dict mapping stock codes to StockPrice objects
        """
        results = {}
        codes_to_fetch = []

        # Check cache first
        for code in stock_codes:
            code = code.strip().zfill(6)
            cache_key = f"price_{code}"
            cached = cache.get("stock_price", cache_key, self.settings.cache_ttl_stock_price)
            if cached:
                results[code] = StockPrice(**cached)
            else:
                codes_to_fetch.append(code)

        if not codes_to_fetch:
            return results

        try:
            # Build secid list for batch query
            secids = [self._get_secid(code) for code in codes_to_fetch]

            # Use AKShare for batch stock quotes as it's more reliable
            try:
                spot_df = ak.stock_zh_a_spot_em()

                for code in codes_to_fetch:
                    row = spot_df[spot_df["代码"] == code]
                    if not row.empty:
                        current_price = float(row["最新价"].iloc[0]) if pd.notna(row["最新价"].iloc[0]) else 0
                        previous_close = float(row["昨收"].iloc[0]) if pd.notna(row["昨收"].iloc[0]) else 0
                        change_percent = float(row["涨跌幅"].iloc[0]) if pd.notna(row["涨跌幅"].iloc[0]) else 0
                        stock_name = row["名称"].iloc[0]

                        stock_price = StockPrice(
                            stock_code=code,
                            stock_name=stock_name,
                            current_price=current_price,
                            previous_close=previous_close,
                            change_percent=change_percent,
                            update_time=datetime.now()
                        )

                        results[code] = stock_price
                        cache.set("stock_price", f"price_{code}", stock_price.model_dump(),
                                 self.settings.cache_ttl_stock_price)
            except Exception as e:
                print(f"Error using AKShare batch query: {e}")
                # Fallback to individual requests
                for code in codes_to_fetch:
                    price = await self.get_stock_price(code)
                    if price:
                        results[code] = price

        except Exception as e:
            print(f"Error in batch stock prices: {e}")

        return results

    async def get_index_change(self, index_code: str) -> float:
        """
        Get index change percent.

        Args:
            index_code: Index code (e.g., "000300.SH", "399987.SZ")

        Returns:
            Change percent
        """
        cache_key = f"index_{index_code}"
        cached = cache.get("index_price", cache_key, self.settings.cache_ttl_stock_price)
        if cached is not None:
            return cached

        try:
            # Convert index code format
            # East Money uses different format for indices
            # 000300.SH -> sh000300
            # 399987.SZ -> sz399987

            parts = index_code.split(".")
            if len(parts) == 2:
                if parts[1].upper() == "SH":
                    em_code = f"sh{parts[0]}"
                elif parts[1].upper() == "SZ":
                    em_code = f"sz{parts[0]}"
                elif parts[1].upper() == "CSI":
                    # For CSI indices, try to use different approach
                    em_code = f"zs{parts[0]}"
                else:
                    em_code = parts[0]
            else:
                em_code = index_code

            # Try using AKShare for index quotes
            try:
                index_df = ak.index_zh_a_hist(symbol=parts[0], period="daily", start_date="20991231", end_date="20991231", adjust="")
                if not index_df.empty:
                    latest = index_df.iloc[-1]
                    change_pct = float(latest.get("涨跌幅", 0))
                    cache.set("index_price", cache_key, change_pct, self.settings.cache_ttl_stock_price)
                    return change_pct
            except Exception:
                pass

            # Fallback to real-time API
            secid = self._get_secid(parts[0])
            params = {
                "secid": secid,
                "fields": "f170"
            }

            response = requests.get(
                self.STOCK_API_URL,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if "data" in data and data["data"] is not None:
                change_percent = data["data"].get("f170", 0) * 0.01 if data["data"].get("f170") else 0
                cache.set("index_price", cache_key, change_percent, self.settings.cache_ttl_stock_price)
                return change_percent

            return 0.0

        except Exception as e:
            print(f"Error getting index change for {index_code}: {e}")
            return 0.0

    def detect_fund_type(self, fund_name: str) -> str:
        """
        Detect fund type based on fund name.

        Args:
            fund_name: Fund name

        Returns:
            Detected fund type category
        """
        fund_name_lower = fund_name.lower()

        for fund_type, config in self.settings.fund_type_mapping.items():
            keywords = config["keywords"]
            for keyword in keywords:
                if keyword in fund_name_lower:
                    return fund_type

        return "混合型"  # Default to mixed type


# Singleton instance
stock_service = StockService()
