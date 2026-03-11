"""
天天基金网API客户端
用于获取基金持仓(股票)、债券持仓、资产配置等数据
作为Wind API的替代数据源，提供更快的响应速度

数据优先级:
1. 后端缓存数据
2. 天天基金网API (本模块)
3. Akshare API (补充字段)
4. Wind API (降级选项)
"""
import requests
import json
import re
import time
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 可选导入akshare和pandas
try:
    import akshare as ak
    import pandas as pd
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    pd = None


# 性能日志装饰器
def log_performance(func):
    """记录函数执行时间的装饰器"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        print(f"[Performance] {func.__name__}: {elapsed:.1f}ms")
        return result
    return wrapper


def async_log_performance(func):
    """记录异步函数执行时间的装饰器"""
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        print(f"[Performance] {func.__name__}: {elapsed:.1f}ms")
        return result
    return wrapper


@dataclass
class StockHolding:
    """股票持仓数据类"""
    seq: int              # 序号
    stock_code: str       # 股票代码
    stock_name: str       # 股票名称
    ratio: float          # 占净值比例(%)
    shares: float         # 持股数(万股)
    market_value: float   # 持仓市值(万元)
    change_percent: Optional[float] = None  # 实时涨跌幅(%)


@dataclass
class BondHolding:
    """债券持仓数据类"""
    seq: int              # 序号
    bond_code: str        # 债券代码
    bond_name: str        # 债券名称
    ratio: float          # 占净值比例(%)
    market_value: float   # 持仓市值(万元)
    is_convertible: bool = False  # 是否为可转债
    change_percent: Optional[float] = None  # 实时涨跌幅(%)


@dataclass
class AssetAllocationData:
    """资产配置数据类"""
    report_date: str      # 报告期 (YYYYMMDD格式)
    stock_ratio: float    # 股票占净比(%)
    bond_ratio: float     # 债券占净比(%)
    cash_ratio: float     # 现金占净比(%)
    other_ratio: float    # 其他占净比(%)
    net_asset: float      # 净资产(亿元)


@dataclass
class FundDetailInfo:
    """基金详情信息数据类"""
    fund_code: str = ""                 # 基金代码
    fund_name: str = ""                 # 基金名称
    fund_type: str = ""                 # 基金类型
    nav: Optional[float] = None         # 单位净值
    acc_nav: Optional[float] = None     # 累计净值
    nav_date: str = ""                  # 净值日期
    daily_change: Optional[float] = None  # 日涨跌幅(%)
    return_1m: Optional[float] = None   # 近1月收益率(%)
    return_3m: Optional[float] = None   # 近3月收益率(%)
    return_6m: Optional[float] = None   # 近6月收益率(%)
    return_1y: Optional[float] = None   # 近1年收益率(%)
    return_3y: Optional[float] = None   # 近3年收益率(%)
    return_since_inception: Optional[float] = None  # 成立来收益率(%)
    return_ytd: Optional[float] = None  # 今年以来收益率(%)
    fund_manager: str = ""              # 基金经理
    management_company: str = ""        # 管理人
    inception_date: str = ""            # 成立日
    fund_scale: Optional[float] = None  # 基金规模(亿元)
    risk_level: Optional[str] = None    # 风险等级
    rating: Optional[int] = None        # 基金评级(1-5星)
    estimate_nav: Optional[float] = None       # 估算净值
    estimate_change: Optional[float] = None    # 估算涨跌幅(%)
    estimate_time: str = ""             # 估算时间


class TTJJClient:
    """天天基金网API客户端"""

    BASE_URL = "https://fundf10.eastmoney.com/FundArchivesDatas.aspx"
    PAGE_URL = "https://fundf10.eastmoney.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://fundf10.eastmoney.com/'
        })

    def _parse_js_response(self, response_text: str) -> Optional[str]:
        """解析JavaScript响应，提取HTML内容"""
        # 匹配 var apidata={ content:"...",...};
        match = re.search(r'var apidata=\{ content:"(.*?)"[,}]', response_text, re.DOTALL)
        if match:
            html = match.group(1)
            # 解码转义字符
            html = html.replace('\\"', '"').replace('\\n', '').replace('\\t', '')
            return html
        return None

    def _extract_report_date(self, html: str) -> Optional[str]:
        """从HTML中提取报告期"""
        # 查找报告期信息，如 "2024年4季度股票投资明细"
        match = re.search(r'(\d{4})年(\d)季度', html)
        if match:
            year = match.group(1)
            quarter = int(match.group(2))
            # 转换为季度末日期
            month = quarter * 3
            day = 31 if month in [3, 12] else 30
            return f"{year}{month:02d}{day:02d}"
        return None

    def _get_stock_realtime_quotes(self, stock_codes: List[str]) -> Dict[str, float]:
        """
        获取股票实时行情数据（涨跌幅）
        使用腾讯股票API获取

        Args:
            stock_codes: 股票代码列表 (如: ["002683", "601899"])

        Returns:
            Dict[str, float]: {股票代码: 涨跌幅%}
        """
        if not stock_codes:
            return {}

        try:
            # 使用腾讯股票API获取实时行情
            result = {}
            # 限制只获取前20只股票
            codes = stock_codes[:20]

            # 构建腾讯代码格式
            tencent_codes = []
            for code in codes:
                if code.startswith('6'):
                    tencent_codes.append(f"sh{code}")
                else:
                    tencent_codes.append(f"sz{code}")

            codes_str = ','.join(tencent_codes)
            url = f"https://qt.gtimg.cn/q={codes_str}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            resp = requests.get(url, headers=headers, timeout=5)
            resp.encoding = 'gb2312'

            # 解析响应，格式: v_sh601899="1~紫金矿业~...~涨跌幅~...";
            for match in re.finditer(r'v_([a-z]{2})(\d{6})="([^"]+)"', resp.text):
                market, code, data = match.groups()
                fields = data.split('~')
                # 腾讯格式: 0-未知,1-名称,2-代码,3-当前价,4-昨收,5-今开...32-涨跌幅
                if len(fields) > 32:
                    try:
                        change_pct = float(fields[32]) if fields[32] else 0
                        result[code] = round(change_pct, 2)
                    except (ValueError, IndexError):
                        continue

            return result
        except Exception as e:
            print(f"Error fetching stock quotes: {e}")
            return {}

    def _get_bond_realtime_quotes(self, bond_codes: List[str]) -> Dict[str, float]:
        """
        获取债券/可转债实时行情数据（涨跌幅）
        使用腾讯API获取可转债实时行情

        Args:
            bond_codes: 债券代码列表 (如: ["110075", "113052"])

        Returns:
            Dict[str, float]: {债券代码: 涨跌幅%}
        """
        if not bond_codes:
            return {}

        try:
            result = {}
            # 只获取前20个可转债的涨跌幅
            convertible_codes = [c for c in bond_codes if c.startswith(('11', '12'))][:20]

            if not convertible_codes:
                return {}

            # 构建腾讯代码格式
            tencent_codes = []
            for code in convertible_codes:
                if code.startswith('11'):
                    tencent_codes.append(f"sh{code}")
                elif code.startswith('12'):
                    tencent_codes.append(f"sz{code}")

            codes_str = ','.join(tencent_codes)
            url = f"https://qt.gtimg.cn/q={codes_str}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            resp = requests.get(url, headers=headers, timeout=5)
            resp.encoding = 'gb2312'

            # 解析响应，格式: v_sh110075="1~上机转债~...~涨跌幅~...";
            for match in re.finditer(r'v_([a-z]{2})(\d{6})="([^"]+)"', resp.text):
                market, code, data = match.groups()
                fields = data.split('~')
                # 腾讯格式: 0-未知,1-名称,2-代码,3-当前价,4-昨收,5-今开...32-涨跌幅
                if len(fields) > 32:
                    try:
                        change_pct = float(fields[32]) if fields[32] else 0
                        result[code] = round(change_pct, 2)
                    except (ValueError, IndexError):
                        continue

            return result
        except Exception as e:
            print(f"Error fetching bond quotes: {e}")
            return {}

    def get_stock_holdings(self, fund_code: str, year: str = "", show_all: bool = True) -> Tuple[List[StockHolding], Optional[str]]:
        """
        获取基金股票持仓

        Args:
            fund_code: 基金代码 (如: "002474")
            year: 年份筛选 (可选)
            show_all: 是否显示所有报告期

        Returns:
            Tuple[List[StockHolding], Optional[str]]: (持仓列表, 报告期)
        """
        params = {
            'type': 'jjcc',
            'code': fund_code,
            'topline': 100,  # 获取更多数据
            'year': year,
            'month': '',
            'rt': '0.5'
        }

        if show_all:
            params['showAll'] = 'true'

        try:
            resp = self.session.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()

            html = self._parse_js_response(resp.text)
            if not html:
                return [], None

            # 提取报告期
            report_date = self._extract_report_date(html)

            # 使用正则提取表格数据
            rows = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL)
            holdings = []

            for row in rows[1:]:  # 跳过表头
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)

                # 处理不同季度的列数差异
                # Q4年报有9列，Q1-Q3季报有7列
                if len(cols) >= 7:
                    # 清理文本
                    texts = [re.sub(r'<[^>]+>', '', col).strip() for col in cols]
                    texts = [t.replace(',', '') for t in texts]

                    try:
                        # 根据列数判断数据位置
                        if len(cols) >= 9:
                            # Q4格式: 序号,代码,名称,数量,比例,市值,...
                            stock_code = texts[1]
                            stock_name = texts[2]
                            ratio_str = texts[6] if len(texts) > 6 else "0%"
                            shares_str = texts[7] if len(texts) > 7 else "0"
                            market_value_str = texts[8] if len(texts) > 8 else "0"
                        else:
                            # Q1-Q3格式: 序号,代码,名称,数量,比例,市值,...
                            stock_code = texts[1]
                            stock_name = texts[2]
                            ratio_str = texts[4] if len(texts) > 4 else "0%"
                            shares_str = texts[5] if len(texts) > 5 else "0"
                            market_value_str = texts[6] if len(texts) > 6 else "0"

                        # 只处理A股（6位数字代码）
                        if not re.match(r'^\d{6}$', stock_code):
                            continue

                        ratio = float(ratio_str.replace('%', '')) if ratio_str and ratio_str != '-' else 0
                        shares = float(shares_str) if shares_str and shares_str != '-' else 0
                        market_value = float(market_value_str) if market_value_str and market_value_str != '-' else 0

                        if ratio > 0:  # 只添加有持仓的数据
                            holdings.append(StockHolding(
                                seq=len(holdings) + 1,
                                stock_code=stock_code,
                                stock_name=stock_name,
                                ratio=ratio,
                                shares=shares,
                                market_value=market_value
                            ))
                    except (ValueError, IndexError) as e:
                        continue

            # 获取实时涨跌幅数据
            if holdings:
                stock_codes = [h.stock_code for h in holdings]
                quotes = self._get_stock_realtime_quotes(stock_codes)
                for h in holdings:
                    h.change_percent = quotes.get(h.stock_code)

            return holdings, report_date

        except Exception as e:
            print(f"Error fetching stock holdings for {fund_code}: {e}")
            return [], None

    def get_bond_holdings(self, fund_code: str, year: str = "", show_all: bool = True) -> Tuple[List[BondHolding], List[BondHolding], Optional[str]]:
        """
        获取基金债券持仓（包括普通债券和可转债）

        Args:
            fund_code: 基金代码 (如: "002474")
            year: 年份筛选 (可选)
            show_all: 是否显示所有报告期

        Returns:
            Tuple[List[BondHolding], List[BondHolding], Optional[str]]: (普通债券, 可转债, 报告期)
        """
        params = {
            'type': 'zqcc',
            'code': fund_code,
            'year': year,
            'rt': '0.5'
        }

        if show_all:
            params['showAll'] = 'true'

        try:
            resp = self.session.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()

            html = self._parse_js_response(resp.text)
            if not html:
                return [], [], None

            # 提取报告期
            report_date = self._extract_report_date(html)

            # 只提取第一个表格的数据（最新报告期）
            # HTML中包含多个报告期的表格，找到第一个<table>...</table>
            table_match = re.search(r'<table[^>]*>.*?</table>', html, re.DOTALL | re.IGNORECASE)
            if table_match:
                first_table_html = table_match.group(0)
            else:
                first_table_html = html

            rows = re.findall(r'<tr>(.*?)</tr>', first_table_html, re.DOTALL)
            regular_bonds = []
            convertible_bonds = []

            for row in rows[1:]:
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cols) >= 5:
                    texts = [re.sub(r'<[^>]+>', '', col).strip() for col in cols]
                    texts = [t.replace(',', '') for t in texts]

                    try:
                        bond_code = texts[1]
                        bond_name = texts[2]
                        ratio_str = texts[3] if len(texts) > 3 else "0%"
                        market_value_str = texts[4] if len(texts) > 4 else "0"

                        ratio = float(ratio_str.replace('%', '')) if ratio_str and ratio_str != '-' else 0
                        market_value = float(market_value_str) if market_value_str and market_value_str != '-' else 0

                        # 判断是否为可转债：名称中包含"转债"或"可转"
                        is_convertible = "转债" in bond_name or "可转" in bond_name

                        holding = BondHolding(
                            seq=len(regular_bonds) + len(convertible_bonds) + 1,
                            bond_code=bond_code,
                            bond_name=bond_name,
                            ratio=ratio,
                            market_value=market_value,
                            is_convertible=is_convertible
                        )

                        if is_convertible:
                            convertible_bonds.append(holding)
                        else:
                            regular_bonds.append(holding)

                    except (ValueError, IndexError):
                        continue

            # 获取债券实时涨跌幅数据
            all_bonds = regular_bonds + convertible_bonds
            if all_bonds:
                bond_codes = [b.bond_code for b in all_bonds]
                quotes = self._get_bond_realtime_quotes(bond_codes)
                for b in all_bonds:
                    b.change_percent = quotes.get(b.bond_code)

            return regular_bonds, convertible_bonds, report_date

        except Exception as e:
            print(f"Error fetching bond holdings for {fund_code}: {e}")
            return [], [], None

    def get_asset_allocation(self, fund_code: str, quarters: int = 8) -> List[AssetAllocationData]:
        """
        获取基金资产配置历史

        Args:
            fund_code: 基金代码 (如: "002474")
            quarters: 获取最近几个季度的数据

        Returns:
            List[AssetAllocationData]: 资产配置列表
        """
        url = f"{self.PAGE_URL}/zcpz_{fund_code}.html"

        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()

            # 提取chartData
            match = re.search(r'var chartData =\s*(\{.*?\});', resp.text, re.DOTALL)
            if not match:
                # 尝试其他格式
                match = re.search(r'var chartData=(\{.*?\});', resp.text, re.DOTALL)
            if not match:
                return []

            chart_data = json.loads(match.group(1))

            allocations = []
            dates = chart_data.get('Dates', [])
            gp = chart_data.get('GP', [])  # 股票占比
            zq = chart_data.get('ZQ', [])  # 债券占比
            xj = chart_data.get('XJ', [])  # 现金占比
            ctpz = chart_data.get('CTPZ', [])  # 存托凭证占比
            jzc = chart_data.get('JZC', [])  # 净资产
            other = chart_data.get('QT', [])  # 其他资产

            for i in range(len(dates)):
                # 转换日期格式从 YYYY-MM-DD 到 YYYYMMDD
                date_str = dates[i]
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    report_date = dt.strftime("%Y%m%d")
                except:
                    report_date = date_str.replace("-", "")

                stock_ratio = gp[i] if i < len(gp) else 0
                bond_ratio = zq[i] if i < len(zq) else 0
                cash_ratio = xj[i] if i < len(xj) else 0
                ctpz_ratio = ctpz[i] if i < len(ctpz) else 0
                net_asset = jzc[i] if i < len(jzc) else 0
                other_ratio = other[i] if i < len(other) else max(0, 100 - stock_ratio - bond_ratio - cash_ratio - ctpz_ratio)

                allocations.append(AssetAllocationData(
                    report_date=report_date,
                    stock_ratio=stock_ratio,
                    bond_ratio=bond_ratio,
                    cash_ratio=cash_ratio,
                    other_ratio=other_ratio + ctpz_ratio,  # 合并其他和存托凭证
                    net_asset=net_asset
                ))

            return allocations[:quarters]

        except Exception as e:
            print(f"Error fetching asset allocation for {fund_code}: {e}")
            return []

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """
        获取基金基本信息

        Args:
            fund_code: 基金代码

        Returns:
            Dict: 基金基本信息
        """
        url = f"https://fund.eastmoney.com/{fund_code}.html"

        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()

            info = {}

            # 基金名称
            name_match = re.search(r'<h1[^>]*>(.*?)</h1>', resp.text)
            if name_match:
                info['name'] = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()

            # 最新净值
            nav_match = re.search(r'单位净值.*?<b[^>]*>([\d.]+)', resp.text)
            if nav_match:
                info['nav'] = float(nav_match.group(1))

            return info

        except Exception as e:
            print(f"Error fetching fund info for {fund_code}: {e}")
            return {}


    def get_realtime_estimate(self, fund_code: str) -> Dict[str, Any]:
        """
        获取基金实时估值数据

        Args:
            fund_code: 基金代码 (如: "019827")

        Returns:
            Dict: 实时估值数据，包含:
                - fundcode: 基金代码
                - name: 基金名称
                - jzrq: 净值日期
                - dwjz: 单位净值
                - gsz: 估算净值
                - gszzl: 估算涨跌幅(%)
                - gztime: 估算时间
        """
        timestamp = int(time.time() * 1000)
        url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js?rt={timestamp}"

        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()

            # 解析JSONP格式: jsonpgz({...})
            match = re.search(r'jsonpgz\((.*?)\);', resp.text)
            if match:
                data = json.loads(match.group(1))
                return data
            else:
                return {}

        except Exception as e:
            print(f"Error fetching realtime estimate for {fund_code}: {e}")
            return {}

    def get_fund_detail_info(self, fund_code: str) -> Optional[FundDetailInfo]:
        """
        获取基金详情完整信息

        整合多个API获取基金的完整信息:
        1. pingzhongdata API - 获取净值走势、基金名称、收益率、基金经理等
        2. 实时估值API - 获取盘中估算数据、最新净值
        3. fundf10/jbgk页面 - 获取类型、规模、成立日、管理人、风险等级、评级等
        4. 主基金页面 - 获取补充信息（备用方案）

        Args:
            fund_code: 基金代码 (如: "019827")

        Returns:
            FundDetailInfo: 基金详情信息，失败返回None
        """
        detail = FundDetailInfo(fund_code=fund_code)

        try:
            # 1. 获取综合数据 (pingzhongdata) - 包含净值、收益率、基金经理、基金类型等
            self._fetch_pingzhong_data(detail)

            # 2. 获取实时估值
            self._fetch_estimate_data(detail)

            # 3. 从fundf10获取详细信息（类型、规模、成立日、管理人、风险等级、评级等）
            missing_fields = not all([
                detail.fund_name,
                detail.fund_type,
                detail.inception_date,
                detail.management_company,
                detail.fund_scale,
                detail.risk_level,
                detail.rating
            ])

            if missing_fields:
                self._fetch_html_info(detail)

            # 4. 如果仍有字段缺失，从主基金页面获取（备用方案）
            still_missing = not all([
                detail.fund_name,
                detail.fund_type,
                detail.risk_level
            ])

            if still_missing:
                self._fetch_fund_page_info(detail)

            # 5. 使用akshare获取仍然缺失的字段（成立日期、风险等级等）
            akshare_needed = not all([
                detail.inception_date,
                detail.risk_level
            ])

            if akshare_needed and AKSHARE_AVAILABLE:
                self._fetch_akshare_info(detail)

            return detail

        except Exception as e:
            print(f"Error fetching fund detail info for {fund_code}: {e}")
            # 返回已获取的部分数据
            if detail.fund_name or detail.nav:
                return detail
            return None

    def _fetch_pingzhong_data(self, detail: FundDetailInfo) -> None:
        """从pingzhongdata API获取数据"""
        timestamp = int(time.time() * 1000)
        url = f"http://fund.eastmoney.com/pingzhongdata/{detail.fund_code}.js?v={timestamp}"

        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            text = resp.text

            # 提取基金名称
            name_match = re.search(r'var fS_name = "(.*?)";', text)
            if name_match:
                detail.fund_name = name_match.group(1)

            # 提取基金代码
            code_match = re.search(r'var fS_code = "(.*?)";', text)
            if code_match:
                # 确认代码匹配
                pass

            # 提取最新净值
            nav_match = re.search(r'var Data_netWorthTrend = (\[.*?\]);', text, re.DOTALL)
            if nav_match:
                try:
                    nav_data = json.loads(nav_match.group(1))
                    if nav_data:
                        latest = nav_data[-1]
                        detail.nav = float(latest.get('y', 0))
                        detail.nav_date = datetime.fromtimestamp(
                            latest.get('x', 0) / 1000
                        ).strftime('%Y-%m-%d')
                        detail.daily_change = float(latest.get('equityReturn', 0))
                except:
                    pass

            # 提取累计净值
            acc_nav_match = re.search(r'var Data_ACWorthTrend = (\[.*?\]);', text, re.DOTALL)
            if acc_nav_match:
                try:
                    acc_nav_data = json.loads(acc_nav_match.group(1))
                    if acc_nav_data:
                        latest_acc = acc_nav_data[-1]
                        if isinstance(latest_acc, list) and len(latest_acc) >= 2:
                            detail.acc_nav = float(latest_acc[1])
                        elif isinstance(latest_acc, dict):
                            detail.acc_nav = float(latest_acc.get('y', 0))
                except:
                    pass

            # 提取基金经理信息 - 使用更精确的正则，避免匹配到后续代码
            manager_match = re.search(r'var Data_currentFundManager = (\[[^\]]*?\])\s*;', text)
            if not manager_match:
                # 备用：尝试匹配直到遇到第一个 ]; 后面的注释
                manager_match = re.search(r'var Data_currentFundManager = (\[.*?\])\s*;/\*', text, re.DOTALL)
            if manager_match:
                try:
                    manager_data = json.loads(manager_match.group(1))
                    if manager_data and len(manager_data) > 0:
                        manager = manager_data[0]
                        detail.fund_manager = manager.get('name', '')
                        # 从power或fundSize字段提取管理规模
                        fund_size_str = manager.get('fundSize', '')
                        if fund_size_str:
                            # 解析 "308.52亿(14只基金)" 格式
                            size_match = re.search(r'([\d.]+)亿', fund_size_str)
                            if size_match:
                                detail.fund_scale = float(size_match.group(1))
                        # 从业时间
                        work_time = manager.get('workTime', '')
                        if work_time:
                            detail.fund_manager += f" ({work_time})"
                except Exception as e:
                    pass

            # 从pingzhongdata提取收益率数据（替代rankhandler）
            # 格式: var syl_1n="17.36" (等号无空格，值带引号)

            # 近1月
            syl_1y_match = re.search(r'var\s+syl_1y\s*=\s*"?([-\d.]+)"?', text)
            if syl_1y_match:
                try:
                    detail.return_1m = float(syl_1y_match.group(1))
                except:
                    pass

            # 近3月
            syl_3y_match = re.search(r'var\s+syl_3y\s*=\s*"?([-\d.]+)"?', text)
            if syl_3y_match:
                try:
                    detail.return_3m = float(syl_3y_match.group(1))
                except:
                    pass

            # 近6月
            syl_6y_match = re.search(r'var\s+syl_6y\s*=\s*"?([-\d.]+)"?', text)
            if syl_6y_match:
                try:
                    detail.return_6m = float(syl_6y_match.group(1))
                except:
                    pass

            # 近1年
            syl_1n_match = re.search(r'var\s+syl_1n\s*=\s*"?([-\d.]+)"?', text)
            if syl_1n_match:
                try:
                    detail.return_1y = float(syl_1n_match.group(1))
                except:
                    pass

            # 近3年
            syl_3n_match = re.search(r'var\s+syl_3n\s*=\s*"?([-\d.]+)"?', text)
            if syl_3n_match:
                try:
                    detail.return_3y = float(syl_3n_match.group(1))
                except:
                    pass

            # 成立以来
            syl_bg_match = re.search(r'var\s+syl_bg\s*=\s*"?([-\d.]+)"?', text)
            if syl_bg_match:
                try:
                    detail.return_since_inception = float(syl_bg_match.group(1))
                except:
                    pass

            # 今年来
            jnzf_match = re.search(r'var\s+jnzf\s*=\s*"?([-\d.]+)"?', text)
            if jnzf_match:
                try:
                    detail.return_ytd = float(jnzf_match.group(1))
                except:
                    pass

            # 提取基金类型（从swithSameType或其他变量）
            fund_type_match = re.search(r'var fundType = "(\d+)"', text)
            if fund_type_match:
                fund_type_code = fund_type_match.group(1)
                type_map = {
                    '001': '股票型',
                    '002': '混合型',
                    '003': '债券型',
                    '004': '指数型',
                    '005': 'QDII',
                    '006': '货币型',
                    '007': '理财型',
                    '008': '分级杠杆',
                    '009': '其他'
                }
                detail.fund_type = type_map.get(fund_type_code, '')

            # 尝试从Data_FundShares获取基金规模（更准确的规模数据）
            shares_match = re.search(r'var Data_FundShares = (\[.*?\]);', text, re.DOTALL)
            if shares_match:
                try:
                    shares_data = json.loads(shares_match.group(1))
                    if shares_data and len(shares_data) > 0:
                        # 获取最新一期份额数据
                        latest_share = shares_data[-1]
                        if isinstance(latest_share, dict):
                            # shares字段是万份，转换为亿份
                            shares = latest_share.get('shares', 0)
                            if shares and not detail.fund_scale:
                                # 粗略估算规模（用最新净值 * 份额）
                                if detail.nav:
                                    detail.fund_scale = round(shares * detail.nav / 10000, 2)
                except:
                    pass

            # 尝试从Data_fundYearPerformance获取更多信息
            year_perf_match = re.search(r'var Data_fundYearPerformance = (\{.*?\});', text, re.DOTALL)
            if year_perf_match:
                try:
                    year_perf = json.loads(year_perf_match.group(1))
                    # 可以从中提取年度收益等信息
                except:
                    pass

        except Exception as e:
            print(f"Error fetching pingzhong data for {detail.fund_code}: {e}")

    def _fetch_fund_page_info(self, detail: FundDetailInfo) -> None:
        """从主基金页面获取信息（备用方案）"""
        try:
            url = f"https://fund.eastmoney.com/{detail.fund_code}.html"
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            text = resp.text

            # 基金名称
            if not detail.fund_name:
                name_match = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.DOTALL)
                if name_match:
                    detail.fund_name = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()

            # 基金类型
            if not detail.fund_type:
                type_match = re.search(r'基金类型[:：]\s*<span[^>]*>([^<]+)</span>', text)
                if type_match:
                    detail.fund_type = self._normalize_fund_type(type_match.group(1).strip())

            # 风险等级
            if not detail.risk_level:
                risk_match = re.search(r'风险等级[:：]\s*<span[^>]*>([^<]+)</span>', text)
                if risk_match:
                    detail.risk_level = self._normalize_risk_level(risk_match.group(1).strip())

            # 基金规模
            if not detail.fund_scale:
                scale_match = re.search(r'规模[:：]\s*<span[^>]*>([\d.]+)\s*亿元', text)
                if scale_match:
                    try:
                        detail.fund_scale = float(scale_match.group(1))
                    except:
                        pass

            # 成立日期
            if not detail.inception_date:
                date_match = re.search(r'成立日[:：]\s*<span[^>]*>(\d{4}-\d{2}-\d{2})</span>', text)
                if date_match:
                    detail.inception_date = date_match.group(1)

            # 基金管理人
            if not detail.management_company:
                company_match = re.search(r'管理人[:：]\s*<span[^>]*>.*?>([^<]+)</a>', text)
                if company_match:
                    detail.management_company = company_match.group(1).strip()

            # 基金经理
            if not detail.fund_manager:
                manager_match = re.search(r'基金经理[:：]\s*<span[^>]*>.*?>([^<]+)</a>', text)
                if manager_match:
                    detail.fund_manager = manager_match.group(1).strip()

        except Exception as e:
            pass  # 备用方法失败不影响主流程

    def _fetch_ranking_data(self, detail: FundDetailInfo) -> None:
        """从rankhandler API获取收益率数据 (已废弃，使用pingzhongdata替代)

        注意：rankhandler API现在需要特殊授权(cookie)，已无法直接访问。
        收益率数据现在直接从pingzhongdata API获取 (在_fetch_pingzhong_data中实现)
        """
        # 此API已不可用，ErrCode: -999 "无法获取授权"
        # 所有收益率数据已从pingzhongdata获取
        pass

    def _fetch_estimate_data(self, detail: FundDetailInfo) -> None:
        """获取实时估值数据"""
        try:
            estimate_data = self.get_realtime_estimate(detail.fund_code)
            if estimate_data:
                try:
                    detail.estimate_nav = float(estimate_data.get('gsz', 0))
                except:
                    pass
                try:
                    detail.estimate_change = float(estimate_data.get('gszzl', 0))
                except:
                    pass
                detail.estimate_time = estimate_data.get('gztime', '')
                # 如果之前没有获取到净值，使用估值数据中的净值
                if not detail.nav:
                    try:
                        detail.nav = float(estimate_data.get('dwjz', 0))
                    except:
                        pass
                if not detail.nav_date:
                    detail.nav_date = estimate_data.get('jzrq', '')
        except Exception as e:
            print(f"Error fetching estimate data for {detail.fund_code}: {e}")

    def _fetch_html_info(self, detail: FundDetailInfo) -> None:
        """从fundf10接口获取补充信息"""
        try:
            # 使用fundf10/jbgk接口获取基金概况
            url = f"https://fundf10.eastmoney.com/jbgk_{detail.fund_code}.html"
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()

            text = resp.text

            # 基金名称
            if not detail.fund_name:
                name_match = re.search(r'基金简称\s*</th>\s*<td[^>]*>(.*?)</td>', text, re.DOTALL)
                if name_match:
                    detail.fund_name = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()

            # 基金类型 - 更精确的匹配，支持多种格式
            if not detail.fund_type:
                # 尝试从基金类型字段获取
                type_match = re.search(r'基金类型\s*</th>\s*<td[^>]*>(.*?)</td>', text, re.DOTALL)
                if type_match:
                    fund_type_text = re.sub(r'<[^>]+>', '', type_match.group(1)).strip()
                    # 清理格式，提取主类型
                    detail.fund_type = self._normalize_fund_type(fund_type_text)

            # 基金管理人
            if not detail.management_company:
                company_match = re.search(r'基金管理人\s*</th>\s*<td[^>]*>.*?>([^<]+)</a>', text, re.DOTALL)
                if company_match:
                    detail.management_company = company_match.group(1).strip()

            # 基金经理
            if not detail.fund_manager:
                manager_match = re.search(r'基金经理人?\s*</th>\s*<td[^>]*>.*?>([^<]+)</a>', text, re.DOTALL)
                if manager_match:
                    detail.fund_manager = manager_match.group(1).strip()

            # 成立日期 - 尝试多种格式
            if not detail.inception_date:
                # 格式1: 标准日期格式
                date_match = re.search(r'成立日期\s*</th>\s*<td[^>]*>(\d{4}-\d{2}-\d{2})</td>', text)
                if date_match:
                    detail.inception_date = date_match.group(1)
                else:
                    # 格式2: 带class的td
                    date_match = re.search(r'成立日期.*?<td[^>]*>(?:\s*<span[^>]*>)?\s*(\d{4}-\d{2}-\d{2})', text, re.DOTALL)
                    if date_match:
                        detail.inception_date = date_match.group(1)

            # 基金规模 - 使用更宽松的正则
            if not detail.fund_scale:
                # 尝试从资产规模字段获取最新规模
                scale_match = re.search(r'资产规模.*?>([\d.]+)\s*亿元', text, re.DOTALL)
                if scale_match:
                    try:
                        detail.fund_scale = float(scale_match.group(1))
                    except:
                        pass
                else:
                    # 备用：从其他位置查找
                    scale_match = re.search(r'规模.*?([\d.]+)\s*亿元', text, re.DOTALL)
                    if scale_match:
                        try:
                            detail.fund_scale = float(scale_match.group(1))
                        except:
                            pass

            # 风险等级
            if not detail.risk_level:
                risk_match = re.search(r'风险等级\s*</th>\s*<td[^>]*>(.*?)</td>', text, re.DOTALL)
                if risk_match:
                    risk_text = re.sub(r'<[^>]+>', '', risk_match.group(1)).strip()
                    detail.risk_level = self._normalize_risk_level(risk_text)

            # 基金评级（从当前页面尝试获取）
            if not detail.rating:
                # 尝试从HTML中直接获取评级
                rating_match = re.search(r'基金评级\s*</th>\s*<td[^>]*>.*?star_(\d)', text, re.DOTALL)
                if rating_match:
                    detail.rating = int(rating_match.group(1))

            # 如果还没获取到评级，调用专门的评级获取方法
            if not detail.rating:
                self._fetch_fund_rating(detail)

            # 尝试从HTML页面获取收益率数据（如果pingzhongdata中没有）
            if not detail.return_1y:
                self._extract_returns_from_html(detail, text)

        except Exception as e:
            print(f"Error fetching HTML info for {detail.fund_code}: {e}")

    def _extract_returns_from_html(self, detail: FundDetailInfo, html: str) -> None:
        """从HTML页面提取收益率数据（备用方案）"""
        try:
            # 查找收益率表格
            # 通常格式: <td>近1年</td><td>-0.54%</td>
            return_patterns = [
                (r'近1年.*?([-\d.]+)%', 'return_1y'),
                (r'近3年.*?([-\d.]+)%', 'return_3y'),
                (r'近6月.*?([-\d.]+)%', 'return_6m'),
                (r'近3月.*?([-\d.]+)%', 'return_3m'),
                (r'近1月.*?([-\d.]+)%', 'return_1m'),
                (r'成立以来.*?([-\d.]+)%', 'return_since_inception'),
            ]

            for pattern, attr in return_patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        value = float(match.group(1))
                        setattr(detail, attr, value)
                    except:
                        pass

        except Exception as e:
            pass

    def _fetch_fund_rating(self, detail: FundDetailInfo) -> None:
        """获取基金评级（从基金评级页面）"""
        try:
            # 使用晨星评级页面
            url = f"https://fundf10.eastmoney.com/FundRating_{detail.fund_code}.html"
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            text = resp.text

            # 方法1: 从晨星三年评级表格获取
            # 查找包含评级的HTML结构
            rating_match = re.search(r'晨星评级.*?star_(\d)star', text, re.IGNORECASE | re.DOTALL)
            if rating_match:
                detail.rating = int(rating_match.group(1))
                return

            # 方法2: 从图片文件名获取星级
            rating_match = re.search(r'star_([1-5])\.gif', text, re.IGNORECASE)
            if rating_match:
                detail.rating = int(rating_match.group(1))
                return

            # 方法3: 从class名称获取
            rating_match = re.search(r'class="[^"]*star([1-5])[^"]*"', text, re.IGNORECASE)
            if rating_match:
                detail.rating = int(rating_match.group(1))
                return

            # 方法4: 计算star_on类数量
            rating_match = re.search(r'(<div[^>]*class="[^"]*rating[^"]*"[^>]*>.*?</div>)', text, re.DOTALL)
            if rating_match:
                star_count = rating_match.group(1).count('star_on')
                if star_count > 0:
                    detail.rating = star_count
                    return

            # 方法5: 从data属性获取
            rating_match = re.search(r'data-rating="([1-5])"', text)
            if rating_match:
                detail.rating = int(rating_match.group(1))
                return

            # 方法6: 从其他可能的格式
            rating_match = re.search(r'评级.*?([1-5])\s*星', text)
            if rating_match:
                detail.rating = int(rating_match.group(1))
                return

        except Exception as e:
            # 评级获取失败不影响主要功能
            pass

    def _normalize_fund_type(self, fund_type_text: str) -> str:
        """标准化基金类型文本"""
        if not fund_type_text:
            return ""

        # 清理文本
        fund_type = fund_type_text.strip()

        # 映射常见类型
        type_mappings = {
            '股票型': '股票型',
            '混合型': '混合型',
            '债券型': '债券型',
            '指数型': '指数型',
            'QDII': 'QDII',
            '货币型': '货币型',
            '理财型': '理财型',
            '分级杠杆': '分级杠杆',
            '商品型': '商品型',
            'FOF': 'FOF',
        }

        # 查找主类型
        for main_type in type_mappings:
            if main_type in fund_type:
                # 检查是否有子类型
                if '-' in fund_type or '—' in fund_type:
                    # 保留子类型信息
                    return fund_type
                return type_mappings[main_type]

        return fund_type

    def _normalize_risk_level(self, risk_text: str) -> str:
        """标准化风险等级文本"""
        if not risk_text:
            return ""

        risk_text = risk_text.strip().upper()

        # 映射风险等级
        risk_mappings = {
            'R1': '低风险',
            'R2': '中低风险',
            'R3': '中风险',
            'R4': '中高风险',
            'R5': '高风险',
            '低风险': '低风险',
            '中低风险': '中低风险',
            '中风险': '中风险',
            '中高风险': '中高风险',
            '高风险': '高风险',
        }

        for key, value in risk_mappings.items():
            if key in risk_text:
                return value

        # 如果没有匹配，返回原始文本（清理后）
        return risk_text.strip()

    def _fetch_akshare_info(self, detail: FundDetailInfo) -> None:
        """
        使用akshare获取基金补充信息

        用于获取天天基金网API难以获取的字段:
        - 成立日期
        - 风险等级
        - 基金类型(更准确的分类)
        - 基金公司
        - 基金经理
        - 基金规模(最新)
        """
        if not AKSHARE_AVAILABLE:
            return

        try:
            # 获取基金基本信息
            fund_info = ak.fund_individual_basic_info_xq(symbol=detail.fund_code)

            if fund_info is None or fund_info.empty:
                return

            # 将DataFrame转换为字典以便查找
            info_dict = {}
            for _, row in fund_info.iterrows():
                item = str(row['item']).strip()
                value = row['value']
                info_dict[item] = value

            # 字段映射 (处理中文编码问题，使用部分匹配)
            for key, value in info_dict.items():
                if value is None or value == '<NA>':
                    continue

                value_str = str(value).strip()

                # 成立时间/成立日期
                if '成立' in key and '时间' in key and not detail.inception_date:
                    # 格式: 2016-08-25
                    if re.match(r'\d{4}-\d{2}-\d{2}', value_str):
                        detail.inception_date = value_str

                # 基金类型
                elif '类型' in key and not detail.fund_type:
                    detail.fund_type = self._normalize_fund_type(value_str)

                # 基金公司/管理人
                elif ('公司' in key or '管理人' in key) and not detail.management_company:
                    detail.management_company = value_str

                # 基金经理
                elif '经理' in key and not detail.fund_manager:
                    detail.fund_manager = value_str

                # 基金规模
                elif '规模' in key and detail.fund_scale is None:
                    # 解析 "94.66亿" 格式
                    scale_match = re.search(r'([\d.]+)\s*亿', value_str)
                    if scale_match:
                        try:
                            detail.fund_scale = float(scale_match.group(1))
                        except:
                            pass

                # 风险等级 (可能在akshare中)
                elif ('风险' in key or 'RISK' in key.upper()) and not detail.risk_level:
                    detail.risk_level = self._normalize_risk_level(value_str)

            # 尝试获取基金详情页面（可能有风险等级）
            try:
                fund_detail = ak.fund_individual_detail_info_xq(symbol=detail.fund_code)
                if fund_detail is not None and not fund_detail.empty:
                    for _, row in fund_detail.iterrows():
                        item = str(row['item']).strip()
                        value = row['value']
                        if value is not None and value != '<NA>':
                            value_str = str(value).strip()

                            # 风险等级
                            if '风险' in item and not detail.risk_level:
                                detail.risk_level = self._normalize_risk_level(value_str)
            except Exception:
                pass

        except Exception as e:
            # akshare调用失败不影响主流程
            pass

    # ==================== 异步优化方法 ====================

    async def get_fund_detail_info_async(self, fund_code: str) -> Optional[FundDetailInfo]:
        """
        【优化版】异步并行获取基金详情完整信息

        使用asyncio.gather并行调用多个数据源，将响应时间从~3秒降低到~1秒

        数据获取策略:
        1. 并行获取所有数据源 (pingzhongdata, 实时估值, fundf10, 主页面, akshare)
        2. 合并结果，优先使用质量更高的数据源
        3. 返回完整的基金详情

        Args:
            fund_code: 基金代码

        Returns:
            FundDetailInfo: 基金详情信息
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        start_time = time.time()
        detail = FundDetailInfo(fund_code=fund_code)

        # 创建线程池用于执行同步IO操作
        executor = ThreadPoolExecutor(max_workers=5)
        loop = asyncio.get_event_loop()

        try:
            # 定义所有数据获取任务
            async def fetch_pingzhong():
                """获取pingzhongdata数据（核心数据源）"""
                task_start = time.time()
                try:
                    await loop.run_in_executor(executor, self._fetch_pingzhong_data, detail)
                    elapsed = (time.time() - task_start) * 1000
                    print(f"[Async] pingzhong_data: {elapsed:.1f}ms")
                    return True
                except Exception as e:
                    print(f"[Async] pingzhong_data failed: {e}")
                    return False

            async def fetch_estimate():
                """获取实时估值"""
                task_start = time.time()
                try:
                    await loop.run_in_executor(executor, self._fetch_estimate_data, detail)
                    elapsed = (time.time() - task_start) * 1000
                    print(f"[Async] estimate_data: {elapsed:.1f}ms")
                    return True
                except Exception as e:
                    print(f"[Async] estimate_data failed: {e}")
                    return False

            async def fetch_fundf10():
                """获取fundf10页面数据"""
                task_start = time.time()
                try:
                    await loop.run_in_executor(executor, self._fetch_html_info, detail)
                    elapsed = (time.time() - task_start) * 1000
                    print(f"[Async] fundf10_data: {elapsed:.1f}ms")
                    return True
                except Exception as e:
                    print(f"[Async] fundf10_data failed: {e}")
                    return False

            async def fetch_main_page():
                """获取主基金页面数据"""
                task_start = time.time()
                try:
                    await loop.run_in_executor(executor, self._fetch_fund_page_info, detail)
                    elapsed = (time.time() - task_start) * 1000
                    print(f"[Async] main_page_data: {elapsed:.1f}ms")
                    return True
                except Exception as e:
                    print(f"[Async] main_page_data failed: {e}")
                    return False

            async def fetch_akshare():
                """获取akshare数据（成立日期等）"""
                if not AKSHARE_AVAILABLE:
                    return False
                task_start = time.time()
                try:
                    await loop.run_in_executor(executor, self._fetch_akshare_info, detail)
                    elapsed = (time.time() - task_start) * 1000
                    print(f"[Async] akshare_data: {elapsed:.1f}ms")
                    return True
                except Exception as e:
                    print(f"[Async] akshare_data failed: {e}")
                    return False

            # 并行执行所有数据获取任务
            print(f"\n[Async] Starting parallel fetch for {fund_code}...")
            tasks = [
                fetch_pingzhong(),
                fetch_estimate(),
                fetch_fundf10(),
                fetch_main_page(),
                fetch_akshare(),
            ]

            # 等待所有任务完成（不报错）
            results = await asyncio.gather(*tasks, return_exceptions=True)

            total_time = (time.time() - start_time) * 1000
            success_count = sum(1 for r in results if r is True)
            print(f"[Async] Total fetch time: {total_time:.1f}ms, Success: {success_count}/{len(tasks)}")

            # 如果至少获取到了基本数据，返回结果
            if detail.fund_name or detail.nav:
                return detail
            return None

        except Exception as e:
            print(f"[Async] Error in get_fund_detail_info_async: {e}")
            if detail.fund_name or detail.nav:
                return detail
            return None
        finally:
            executor.shutdown(wait=False)


# Singleton instance
ttjj_client = TTJJClient()
