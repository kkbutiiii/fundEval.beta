"""
基金估值API客户端
调用 fund_estimation_system 提供的HTTP API获取天天基金官方实时估值数据
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import httpx

from app.config import get_settings
from app.models.valuation import FundEstimation, EstimationDataPoint, EstimationSummary

logger = logging.getLogger(__name__)


class EstimationAPIError(Exception):
    """估值API错误"""
    pass


class EstimationAPIClient:
    """
    基金估值API客户端
    调用 fund_estimation_system 提供的HTTP API
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """
        初始化客户端

        Args:
            base_url: API基础URL，默认从配置读取
            timeout: 请求超时时间（秒），默认从配置读取
        """
        settings = get_settings()
        self.base_url = base_url or settings.estimation_api_base_url
        self.timeout = timeout or settings.estimation_api_timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送HTTP请求到估值API

        Args:
            endpoint: API端点路径
            params: 查询参数

        Returns:
            API响应数据

        Raises:
            EstimationAPIError: 当API请求失败时
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"Estimation API timeout: {url}")
            raise EstimationAPIError(f"估值服务请求超时，请稍后重试")
        except httpx.ConnectError as e:
            logger.error(f"Estimation API connection error: {url} - {e}")
            raise EstimationAPIError(f"估值服务暂时不可用，请检查服务是否已启动")
        except httpx.HTTPStatusError as e:
            logger.error(f"Estimation API HTTP error: {e.response.status_code} - {e.response.text}")
            raise EstimationAPIError(f"估值服务返回错误: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Estimation API error: {url} - {e}")
            raise EstimationAPIError(f"估值服务请求失败: {str(e)}")

    async def get_fund_estimation(self, fund_code: str, date: Optional[str] = None) -> FundEstimation:
        """
        获取基金日内估值序列

        Args:
            fund_code: 基金代码
            date: 日期（YYYYMMDD格式），默认为今天

        Returns:
            FundEstimation: 基金估值数据

        Raises:
            EstimationAPIError: 当API请求失败时
        """
        params = {"code": fund_code}
        if date:
            params["date"] = date

        data = await self._make_request("/api/v1/fund/estimation", params=params)

        # 转换API响应为FundEstimation模型
        estimation_data = [
            EstimationDataPoint(time=item["time"], nav=item["nav"], growth=item["growth"])
            for item in data.get("data", [])
        ]

        return FundEstimation(
            code=data.get("code", fund_code),
            name=data.get("name"),
            date=data.get("date", int(datetime.now().strftime("%Y%m%d"))),
            data=estimation_data,
            count=data.get("count", len(estimation_data)),
            first_time=data.get("first_time"),
            last_time=data.get("last_time")
        )

    async def get_latest_estimations(self, limit: int = 20) -> List[EstimationSummary]:
        """
        获取最新估值排名

        Args:
            limit: 返回数量限制

        Returns:
            List[EstimationSummary]: 基金估值摘要列表

        Raises:
            EstimationAPIError: 当API请求失败时
        """
        params = {"limit": limit}
        data = await self._make_request("/api/v1/fund/latest", params=params)

        funds = data.get("data", [])  # API returns "data" not "funds"
        return [
            EstimationSummary(
                code=item.get("code", ""),
                name=item.get("name"),
                date=item.get("date", 0),
                latest_nav=item.get("nav"),  # API returns "nav" (estimate_nav)
                latest_growth=item.get("growth"),  # API returns "growth" (estimate_growth)
                actual_nav=item.get("actual_nav"),  # API returns "actual_nav" (yesterday's official NAV)
                last_time=item.get("last_time"),
                data_count=item.get("data_count", 0)
            )
            for item in funds
        ]

    async def get_fund_list(self) -> List[Dict[str, Any]]:
        """
        获取支持的基金列表

        Returns:
            List[Dict]: 基金代码和名称列表

        Raises:
            EstimationAPIError: 当API请求失败时
        """
        data = await self._make_request("/api/v1/fund/list")
        return data.get("funds", [])

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息

        Returns:
            Dict: 系统统计信息

        Raises:
            EstimationAPIError: 当API请求失败时
        """
        return await self._make_request("/api/v1/system/stats")

    async def health_check(self) -> bool:
        """
        检查估值API服务是否健康

        Returns:
            bool: 服务是否可用
        """
        try:
            # 尝试获取系统统计信息作为健康检查
            await self._make_request("/api/v1/system/stats")
            return True
        except Exception as e:
            logger.warning(f"Estimation API health check failed: {e}")
            return False

    async def get_batch_estimations(self, fund_codes: List[str]) -> List[EstimationSummary]:
        """
        批量获取基金最新估值（包含实际净值）

        使用 /api/v1/fund/latest 端点获取数据，包含 actual_nav（昨日官方净值）

        Args:
            fund_codes: 基金代码列表

        Returns:
            List[EstimationSummary]: 估值摘要列表（仅包含成功获取的数据）
        """
        results = []

        # 首先获取所有基金的最新估值（包含 actual_nav）
        try:
            # 获取足够多的数据以确保包含所有请求的基金
            all_estimations = await self.get_latest_estimations(limit=max(100, len(fund_codes) * 2))
            estimation_dict = {e.code: e for e in all_estimations}

            # 筛选出请求的基金
            for code in fund_codes:
                if code in estimation_dict:
                    results.append(estimation_dict[code])
                else:
                    # 如果不在列表中，尝试单独获取
                    try:
                        estimation = await self.get_fund_estimation(code)
                        if estimation.data:
                            latest = estimation.data[-1]
                            results.append(EstimationSummary(
                                code=estimation.code,
                                name=estimation.name,
                                date=estimation.date,
                                latest_nav=latest.nav,
                                latest_growth=latest.growth,
                                last_time=estimation.last_time or latest.time,
                                data_count=estimation.count
                            ))
                        else:
                            logger.warning(f"[BatchEstimation] No estimation data for {code}")
                    except Exception as e:
                        logger.warning(f"[BatchEstimation] Failed to get estimation for {code}: {type(e).__name__}: {e}")
        except Exception as e:
            logger.error(f"Error fetching batch estimations: {e}")

        return results

    async def get_fund_with_actual_nav(self, fund_code: str) -> Optional[EstimationSummary]:
        """
        获取单个基金的估值（包含 actual_nav）

        Args:
            fund_code: 基金代码

        Returns:
            EstimationSummary 或 None
        """
        try:
            # 尝试从 latest 端点获取
            all_estimations = await self.get_latest_estimations(limit=1000)
            for est in all_estimations:
                if est.code == fund_code:
                    return est

            # 如果找不到，从 estimation 端点获取（不含 actual_nav）
            estimation = await self.get_fund_estimation(fund_code)
            if estimation.data:
                latest = estimation.data[-1]
                return EstimationSummary(
                    code=estimation.code,
                    name=estimation.name,
                    date=estimation.date,
                    latest_nav=latest.nav,
                    latest_growth=latest.growth,
                    last_time=estimation.last_time or latest.time,
                    data_count=estimation.count
                )
        except EstimationAPIError as e:
            logger.warning(f"Failed to get fund with actual NAV for {fund_code}: {e}")

        return None


# 全局客户端实例
_estimation_client: Optional[EstimationAPIClient] = None


def get_estimation_client() -> EstimationAPIClient:
    """获取全局估值API客户端实例"""
    global _estimation_client
    if _estimation_client is None:
        _estimation_client = EstimationAPIClient()
    return _estimation_client


async def close_estimation_client():
    """关闭全局客户端连接"""
    global _estimation_client
    if _estimation_client is not None:
        await _estimation_client.client.aclose()
        _estimation_client = None
