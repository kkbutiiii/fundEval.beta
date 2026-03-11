"""
Wind API client wrapper for fund data retrieval.
Provides fallback to AKShare when Wind is not available.
Now integrates 天天基金 (TTJJ) API as the primary data source.
"""
import re
from datetime import datetime, date
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import akshare as ak
import pandas as pd

# Import TTJJ client for primary data source
try:
    from app.services.ttjj_client import ttjj_client, AssetAllocationData as TTJJAssetAllocation
except ImportError:
    ttjj_client = None


@dataclass
class AssetAllocation:
    """Asset allocation data for a specific report date."""
    report_date: str
    stock_ratio: float
    bond_ratio: float
    cash_ratio: float
    other_ratio: float
    net_asset: Optional[float] = None


@dataclass
class BondHolding:
    """Bond holding information."""
    bond_code: str
    bond_name: str
    weight: float
    market_value: Optional[float] = None
    type: str = "bond"  # 'bond' or 'convertible'


@dataclass
class NavHistory:
    """NAV history data point."""
    date: str
    nav: float
    nav_acc: Optional[float] = None


class WindClient:
    """Wind API client with AKShare fallback."""

    def __init__(self):
        self._wind_available = None
        self._w = None

    def _check_wind(self) -> bool:
        """Check if WindPy is available and connected."""
        if self._wind_available is not None:
            return self._wind_available

        try:
            from WindPy import w
            self._w = w
            if w.isconnected():
                self._wind_available = True
            else:
                # Try to start Wind
                w.start()
                self._wind_available = w.isconnected()
        except Exception:
            self._wind_available = False

        return self._wind_available

    def _fund_code_to_wind(self, fund_code: str) -> str:
        """Convert fund code to Wind format (e.g., 002474 -> 002474.OF)."""
        fund_code = fund_code.strip().zfill(6)
        return f"{fund_code}.OF"

    def _fund_code_from_wind(self, wind_code: str) -> str:
        """Convert Wind format to fund code (e.g., 002474.OF -> 002474)."""
        return wind_code.replace(".OF", "").replace(".SH", "").replace(".SZ", "")

    def get_asset_allocation_history(self, fund_code: str, quarters: int = 8) -> List[AssetAllocation]:
        """
        Get asset allocation history for a fund.
        Priority: 1) TTJJ API, 2) Wind API, 3) AKShare

        Args:
            fund_code: Fund code (e.g., '002474')
            quarters: Number of quarters to retrieve

        Returns:
            List of AssetAllocation objects
        """
        # Try TTJJ API first (fastest)
        if ttjj_client:
            try:
                allocations = ttjj_client.get_asset_allocation(fund_code, quarters)
                if allocations:
                    print(f"Got asset allocation from TTJJ for {fund_code}")
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
            except Exception as e:
                print(f"TTJJ asset allocation failed for {fund_code}: {e}")

        # Fallback to Wind API
        if self._check_wind():
            return self._get_asset_allocation_from_wind(fund_code, quarters)
        else:
            return self._get_asset_allocation_from_akshare(fund_code, quarters)

    def _get_asset_allocation_from_wind(self, fund_code: str, quarters: int = 8) -> List[AssetAllocation]:
        """Get asset allocation from Wind API."""
        w = self._w
        wind_code = self._fund_code_to_wind(fund_code)

        # Generate report dates (quarter ends)
        report_dates = self._generate_report_dates(quarters)

        results = []
        for rpt_date in report_dates:
            try:
                result = w.wss(
                    wind_code,
                    "prt_stocktoasset,prt_bondtoasset,prt_cashtoasset,prt_othertoasset,prt_netasset",
                    f"rptDate={rpt_date}"
                )

                if result and result.Data and len(result.Data) == 5:
                    stock_ratio = result.Data[0][0] if result.Data[0][0] is not None else 0
                    bond_ratio = result.Data[1][0] if result.Data[1][0] is not None else 0
                    cash_ratio = result.Data[2][0] if result.Data[2][0] is not None else 0
                    other_ratio = result.Data[3][0] if result.Data[3][0] is not None else 0
                    net_asset = result.Data[4][0] if result.Data[4][0] is not None else None

                    results.append(AssetAllocation(
                        report_date=rpt_date,
                        stock_ratio=stock_ratio,
                        bond_ratio=bond_ratio,
                        cash_ratio=cash_ratio,
                        other_ratio=other_ratio,
                        net_asset=net_asset
                    ))
            except Exception as e:
                print(f"Error getting asset allocation from Wind for {fund_code} on {rpt_date}: {e}")
                continue

        return results

    def _get_asset_allocation_from_akshare(self, fund_code: str, quarters: int = 8) -> List[AssetAllocation]:
        """Get asset allocation from AKShare (fallback)."""
        try:
            fund_code = fund_code.strip().zfill(6)
            df = ak.fund_portfolio_hold_em(symbol=fund_code, date=str(date.today().year))

            if df.empty or "季度" not in df.columns:
                return []

            # Group by quarter and get unique quarters
            quarters_data = []
            seen_quarters = set()

            for _, row in df.iterrows():
                quarter = row.get("季度", "")
                if quarter and quarter not in seen_quarters:
                    seen_quarters.add(quarter)
                    # Parse quarter string like "2024年4季度"
                    match = re.search(r"(\d{4})年(\d)季度", quarter)
                    if match:
                        year = int(match.group(1))
                        q = int(match.group(2))
                        month = q * 3
                        rpt_date = f"{year}{month:02d}31" if month in [3, 12] else f"{year}{month:02d}30"

                        # AKShare doesn't provide breakdown, so we estimate
                        stock_ratio = float(row.get("占净值比例", 0)) if pd.notna(row.get("占净值比例")) else 0

                        quarters_data.append(AssetAllocation(
                            report_date=rpt_date,
                            stock_ratio=stock_ratio,
                            bond_ratio=0,  # Not available from AKShare
                            cash_ratio=0,
                            other_ratio=100 - stock_ratio if stock_ratio > 0 else 0,
                            net_asset=None
                        ))

            return quarters_data[:quarters]

        except Exception as e:
            print(f"Error getting asset allocation from AKShare for {fund_code}: {e}")
            return []

    def get_all_holdings(self, fund_code: str) -> Tuple[List[BondHolding], List[BondHolding]]:
        """
        Get all holdings including bonds and convertible bonds.
        Priority: 1) TTJJ API, 2) Wind API, 3) AKShare

        Args:
            fund_code: Fund code

        Returns:
            Tuple of (regular_bonds, convertible_bonds)
        """
        # Try TTJJ API first (fastest)
        if ttjj_client:
            try:
                regular, convertibles, report_date = ttjj_client.get_bond_holdings(fund_code)
                if regular or convertibles:
                    print(f"Got bond holdings from TTJJ for {fund_code}: {len(regular)} bonds, {len(convertibles)} convertibles")
                    return (
                        [
                            BondHolding(
                                bond_code=b.bond_code,
                                bond_name=b.bond_name,
                                weight=b.ratio,
                                market_value=b.market_value,
                                type="bond"
                            )
                            for b in regular
                        ],
                        [
                            BondHolding(
                                bond_code=b.bond_code,
                                bond_name=b.bond_name,
                                weight=b.ratio,
                                market_value=b.market_value,
                                type="convertible"
                            )
                            for b in convertibles
                        ]
                    )
            except Exception as e:
                print(f"TTJJ bond holdings failed for {fund_code}: {e}")

        # Fallback to Wind API
        if self._check_wind():
            return self._get_all_holdings_from_wind(fund_code)
        else:
            return self._get_all_holdings_from_akshare(fund_code)

    def _get_all_holdings_from_wind(self, fund_code: str) -> Tuple[List[BondHolding], List[BondHolding]]:
        """Get all holdings from Wind API with proper weight calculation."""
        w = self._w
        wind_code = self._fund_code_to_wind(fund_code)

        regular_bonds = []
        convertible_bonds = []

        try:
            # Get latest report date first
            latest_date = self.get_latest_report_date(fund_code)
            print(f"Latest report date for {fund_code}: {latest_date}")

            if latest_date:
                # Convert from YYYY-MM-DD to YYYYMMDD format
                rpt_date = latest_date.replace("-", "")
            else:
                # Fallback to most recent quarter end
                today = date.today()
                current_quarter = (today.month - 1) // 3 + 1
                month = current_quarter * 3
                year = today.year
                # Go back one quarter if current quarter hasn't ended
                if today.month < month:
                    current_quarter -= 1
                    if current_quarter == 0:
                        current_quarter = 4
                        year -= 1
                    month = current_quarter * 3
                day = 31 if month in [3, 12] else 30
                rpt_date = f"{year}{month:02d}{day:02d}"

            print(f"Using report date: {rpt_date}")

            # Get asset allocation for total net asset
            asset_result = w.wss(
                wind_code,
                "prt_netasset",
                f"rptDate={rpt_date}"
            )
            total_net_asset = asset_result.Data[0][0] if asset_result and asset_result.Data and asset_result.Data[0] else None
            print(f"Total net asset: {total_net_asset}")

            # Get all top holdings (up to 50)
            all_holdings = []
            for top_num in range(1, 51):
                try:
                    result = w.wss(
                        wind_code,
                        "prt_topsecuritiename,prt_topsecuritiecode,prt_topsecuritievalue,prt_topsecuritietype,prt_heavilyheldsectonav",
                        f"rptDate={rpt_date};topNum={top_num}"
                    )

                    if not result or not result.Data or result.ErrorCode != 0:
                        if top_num == 1:
                            print(f"Wind API error on first holding: {result.ErrorCode if result else 'No result'}")
                        break

                    name = result.Data[0][0] if result.Data[0] and len(result.Data[0]) > 0 else None
                    code = result.Data[1][0] if result.Data[1] and len(result.Data[1]) > 0 else None
                    market_value = result.Data[2][0] if result.Data[2] and len(result.Data[2]) > 0 else None
                    sec_type = result.Data[3][0] if result.Data[3] and len(result.Data[3]) > 0 else None
                    weight = result.Data[4][0] if len(result.Data) > 4 and result.Data[4] and len(result.Data[4]) > 0 else None

                    if not name or not code:
                        continue

                    # Debug: print all holdings
                    print(f"Holding {top_num}: {name} ({code}) - Type: {sec_type}, Weight: {weight}%")

                    # Skip stocks - only process bonds
                    # Note: sec_type might be encoded, check for both Chinese and possible encoding issues
                    if sec_type and "股票" in str(sec_type):
                        continue

                    # Calculate weight if not provided
                    if weight is None and market_value and total_net_asset and total_net_asset > 0:
                        weight = (market_value / (total_net_asset * 10000)) * 100

                    # Determine if it's a convertible bond
                    name_str = str(name)
                    is_convertible = "转债" in name_str or "可转" in name_str

                    holding = BondHolding(
                        bond_code=str(code),
                        bond_name=name_str,
                        weight=round(weight, 2) if weight else 0,
                        market_value=market_value,
                        type="convertible" if is_convertible else "bond"
                    )

                    # Classify as convertible or regular bond
                    if is_convertible:
                        convertible_bonds.append(holding)
                        print(f"  -> Added as convertible bond")
                    else:
                        regular_bonds.append(holding)
                        print(f"  -> Added as regular bond")

                except Exception as e:
                    print(f"Error fetching top {top_num} holding: {e}")
                    import traceback
                    traceback.print_exc()
                    break

            print(f"Wind holdings for {fund_code} on {rpt_date}: {len(regular_bonds)} bonds, {len(convertible_bonds)} convertibles")

        except Exception as e:
            print(f"Error getting holdings from Wind for {fund_code}: {e}")
            import traceback
            traceback.print_exc()

        return regular_bonds, convertible_bonds

    def _get_all_holdings_from_akshare(self, fund_code: str) -> Tuple[List[BondHolding], List[BondHolding]]:
        """Get all holdings from AKShare (limited bond data available)."""
        # AKShare doesn't provide detailed bond holdings, return empty lists
        return [], []

    def get_benchmark(self, fund_code: str) -> Optional[str]:
        """
        Get fund benchmark string.

        Args:
            fund_code: Fund code

        Returns:
            Benchmark string (e.g., "沪深300指数×80%+中证全债指数×20%")
        """
        if self._check_wind():
            return self._get_benchmark_from_wind(fund_code)
        else:
            return self._get_benchmark_from_akshare(fund_code)

    def _get_benchmark_from_wind(self, fund_code: str) -> Optional[str]:
        """Get benchmark from Wind API."""
        w = self._w
        wind_code = self._fund_code_to_wind(fund_code)

        try:
            trade_date = date.today().strftime("%Y%m%d")
            result = w.wss(wind_code, "fund_benchmark", f"tradeDate={trade_date}")

            if result and result.Data and result.Data[0]:
                return result.Data[0][0]
        except Exception as e:
            print(f"Error getting benchmark from Wind for {fund_code}: {e}")

        return None

    def _get_benchmark_from_akshare(self, fund_code: str) -> Optional[str]:
        """Get benchmark from AKShare."""
        try:
            fund_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code.zfill(6))
            if not fund_info_df.empty:
                info_dict = dict(zip(fund_info_df["item"], fund_info_df["value"]))
                return info_dict.get("业绩比较基准")
        except Exception as e:
            print(f"Error getting benchmark from AKShare for {fund_code}: {e}")

        return None

    def get_west_estimate(self, fund_code: str) -> Optional[Dict]:
        """
        Get Wind's estimated return (west_return).

        Args:
            fund_code: Fund code

        Returns:
            Dict with 'west_return' and 'west_return_error' or None
        """
        if not self._check_wind():
            return None

        w = self._w
        wind_code = self._fund_code_to_wind(fund_code)

        try:
            trade_date = date.today().strftime("%Y%m%d")
            result = w.wss(wind_code, "west_return,west_return_error", f"tradeDate={trade_date}")

            if result and result.Data and len(result.Data) == 2:
                return {
                    "west_return": result.Data[0][0] if result.Data[0] else None,
                    "west_return_error": result.Data[1][0] if result.Data[1] else None
                }
        except Exception as e:
            print(f"Error getting west estimate from Wind for {fund_code}: {e}")

        return None

    def get_nav_history(self, fund_code: str, start_date: str, end_date: str) -> List[NavHistory]:
        """
        Get NAV history for a fund.

        Args:
            fund_code: Fund code
            start_date: Start date (YYYYMMDD)
            end_date: End date (YYYYMMDD)

        Returns:
            List of NavHistory objects
        """
        if self._check_wind():
            return self._get_nav_history_from_wind(fund_code, start_date, end_date)
        else:
            return self._get_nav_history_from_akshare(fund_code, start_date, end_date)

    def _get_nav_history_from_wind(self, fund_code: str, start_date: str, end_date: str) -> List[NavHistory]:
        """Get NAV history from Wind API."""
        w = self._w
        wind_code = self._fund_code_to_wind(fund_code)

        results = []
        try:
            result = w.wsd(wind_code, "nav,NAV_acc", start_date, end_date, "")

            if result and result.Data and len(result.Data) == 2:
                dates = result.Times
                navs = result.Data[0]
                nav_accs = result.Data[1]

                for i, d in enumerate(dates):
                    date_str = d.strftime("%Y-%m-%d") if isinstance(d, datetime) else str(d)
                    nav = navs[i] if navs[i] is not None else 0
                    nav_acc = nav_accs[i] if nav_accs[i] is not None else None

                    results.append(NavHistory(
                        date=date_str,
                        nav=nav,
                        nav_acc=nav_acc
                    ))
        except Exception as e:
            print(f"Error getting NAV history from Wind for {fund_code}: {e}")

        return results

    def _get_nav_history_from_akshare(self, fund_code: str, start_date: str, end_date: str) -> List[NavHistory]:
        """Get NAV history from AKShare."""
        results = []

        try:
            fund_code = fund_code.zfill(6)
            # Convert dates
            start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

            df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

            if df.empty:
                return results

            for _, row in df.iterrows():
                try:
                    nav_date = str(row.get("净值日期", ""))
                    if start <= nav_date <= end:
                        nav = float(row.get("单位净值", 0)) if pd.notna(row.get("单位净值")) else 0
                        results.append(NavHistory(
                            date=nav_date,
                            nav=nav,
                            nav_acc=None
                        ))
                except (ValueError, TypeError):
                    continue

        except Exception as e:
            print(f"Error getting NAV history from AKShare for {fund_code}: {e}")

        return results

    def get_latest_report_date(self, fund_code: str) -> Optional[str]:
        """
        Get latest holdings report date from Wind.

        Args:
            fund_code: Fund code (e.g., '002474')

        Returns:
            Report date string (YYYY-MM-DD) or None
        """
        if not self._check_wind():
            return None

        w = self._w
        wind_code = self._fund_code_to_wind(fund_code)

        try:
            # Use wsd to get historical report dates from asset allocation data
            # Get data from beginning of previous year to now
            current_year = date.today().year
            start_date = f"{current_year - 1}0101"
            end_date = date.today().strftime("%Y%m%d")

            result = w.wsd(wind_code, "prt_stocktoasset", start_date, end_date, "Period=Q")

            if result and result.ErrorCode == 0 and result.Times:
                # Filter for valid quarter-end dates only
                # Quarter ends are: 03-31, 06-30, 09-30, 12-31
                valid_report_dates = []
                for dt in result.Times:
                    if isinstance(dt, (datetime, date)):
                        month, day = dt.month, dt.day
                        # Check if it's a quarter end date
                        if (month == 3 and day == 31) or \
                           (month == 6 and day == 30) or \
                           (month == 9 and day == 30) or \
                           (month == 12 and day == 31):
                            valid_report_dates.append(dt)

                print(f"Wind wsd returned times: {result.Times}")
                print(f"Valid quarter-end dates: {valid_report_dates}")

                if valid_report_dates:
                    # Get the latest valid report date
                    latest_date = valid_report_dates[-1]
                    print(f"Latest valid report date: {latest_date}")

                    # Format the date
                    if isinstance(latest_date, datetime):
                        formatted = latest_date.strftime("%Y-%m-%d")
                    elif isinstance(latest_date, date):
                        formatted = latest_date.isoformat()
                    elif hasattr(latest_date, 'strftime'):
                        formatted = latest_date.strftime("%Y-%m-%d")
                    else:
                        formatted = str(latest_date)

                    print(f"Formatted report date: {formatted}")
                    return formatted
        except Exception as e:
            print(f"Error getting report date from Wind: {e}")
            import traceback
            traceback.print_exc()

        return None

    def get_index_history(self, index_code: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Get index history data.

        Args:
            index_code: Index code (e.g., '000300.SH')
            start_date: Start date (YYYYMMDD)
            end_date: End date (YYYYMMDD)

        Returns:
            List of dicts with 'date' and 'close'
        """
        if self._check_wind():
            return self._get_index_history_from_wind(index_code, start_date, end_date)
        else:
            return self._get_index_history_from_akshare(index_code, start_date, end_date)

    def _get_index_history_from_wind(self, index_code: str, start_date: str, end_date: str) -> List[Dict]:
        """Get index history from Wind API."""
        w = self._w
        results = []

        try:
            result = w.wsd(index_code, "close", start_date, end_date, "")

            if result and result.Data and result.Data[0]:
                dates = result.Times
                closes = result.Data[0]

                for i, d in enumerate(dates):
                    date_str = d.strftime("%Y-%m-%d") if isinstance(d, datetime) else str(d)
                    close = closes[i] if closes[i] is not None else 0

                    results.append({
                        "date": date_str,
                        "close": close
                    })
        except Exception as e:
            print(f"Error getting index history from Wind for {index_code}: {e}")

        return results

    def _get_index_history_from_akshare(self, index_code: str, start_date: str, end_date: str) -> List[Dict]:
        """Get index history from AKShare."""
        results = []

        try:
            # Convert dates
            start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

            # Map common index codes
            if "000300" in index_code:
                # CSI 300
                df = ak.index_zh_a_hist(symbol="000300", period="daily",
                                        start_date=start, end_date=end)
            elif "000001" in index_code:
                # Shanghai Composite
                df = ak.index_zh_a_hist(symbol="000001", period="daily",
                                        start_date=start, end_date=end)
            elif "H11001" in index_code or "中证全债" in index_code:
                # CSI Aggregate Bond Index - not directly available, return empty
                return []
            else:
                return []

            if df.empty:
                return results

            for _, row in df.iterrows():
                try:
                    results.append({
                        "date": str(row.get("日期", "")),
                        "close": float(row.get("收盘", 0)) if pd.notna(row.get("收盘")) else 0
                    })
                except (ValueError, TypeError):
                    continue

        except Exception as e:
            print(f"Error getting index history from AKShare for {index_code}: {e}")

        return results

    @staticmethod
    def _generate_report_dates(quarters: int) -> List[str]:
        """Generate quarter end dates going back from current quarter.

        Only returns dates that have actual data (not future dates).
        """
        today = date.today()
        current_year = today.year
        current_month = today.month

        # Determine current quarter
        current_quarter = (current_month - 1) // 3 + 1

        dates = []
        year = current_year
        quarter = current_quarter

        for _ in range(quarters * 2):  # Generate more dates to account for future filtering
            month = quarter * 3
            day = 31 if month in [3, 12] else 30
            rpt_date = f"{year}{month:02d}{day:02d}"

            # Only add dates that are not in the future
            # Report dates are at quarter end, so data is available after that date
            report_date = date(year, month, day)
            # Data is typically available a few weeks after quarter end
            # So we check if the report date has passed
            if report_date <= today:
                dates.append(rpt_date)

            quarter -= 1
            if quarter == 0:
                quarter = 4
                year -= 1

            # Stop once we have enough valid dates
            if len(dates) >= quarters:
                break

        return dates[:quarters]


# Singleton instance
wind_client = WindClient()
