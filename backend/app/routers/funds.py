"""
Fund-related API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.models import FundInfo, Fund, ValuationResult, AssetAllocationHistory
from app.models.valuation import FundEstimation, EstimationSummary, EstimationAPIResponse
from app.services.fund_service import fund_service
from app.services.wind_client import wind_client
from app.services.ttjj_client import ttjj_client
from app.services.estimation_api_client import (
    EstimationAPIClient, EstimationAPIError, get_estimation_client
)
from app.utils.fund_list_cache import fund_list_cache
from app.utils.benchmark_parser import parse_benchmark
from app.database import AsyncSessionLocal
from datetime import datetime, timedelta


router = APIRouter(prefix="/api/v1/funds", tags=["funds"])


class SearchResponse(BaseModel):
    """Search response model."""
    funds: List[FundInfo]
    total: int


class ValuationResponse(BaseModel):
    """Valuation response model."""
    success: bool
    data: Optional[ValuationResult] = None
    message: str = ""


@router.get("/search", response_model=SearchResponse)
async def search_funds(
    q: str = Query(..., description="Search keyword (fund code or name)", min_length=1),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100)
):
    """
    Search funds by keyword.

    - **q**: Search keyword (fund code or name)
    - **limit**: Maximum number of results to return
    """
    try:
        funds = await fund_service.search_funds(q, limit)
        return SearchResponse(funds=funds, total=len(funds))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/all", response_model=List[FundInfo])
async def get_all_funds(
    limit: int = Query(100, description="Maximum number of funds", ge=1, le=1000)
):
    """
    Get list of all funds.

    - **limit**: Maximum number of funds to return
    """
    try:
        funds = await fund_service.get_all_funds(limit)
        return funds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fund list: {str(e)}")


@router.get("/{fund_code}/info", response_model=FundInfo)
async def get_fund_info(fund_code: str):
    """
    Get basic information for a specific fund.
    【优化版】使用缓存和异步并行请求，响应时间从~3秒降低到~1秒

    - **fund_code**: Fund code (e.g., 000001)

    Returns rich fund information including:
    - Basic info (name, type, NAV, date)
    - Daily change percentage and accumulated NAV
    - Risk level and fund rating
    - Returns (1m, 3m, 6m, 1y, 3y, YTD, since inception)
    - Manager, company, and asset size
    """
    import time
    start_time = time.time()

    fund_code = fund_code.strip().zfill(6)
    cache_key = f"fund_info_detail_{fund_code}"

    # 1. 优先检查缓存（缓存5分钟）
    from app.utils.cache import cache
    from app.config import get_settings
    settings = get_settings()

    cached = cache.get("fund_detail", cache_key, ttl=300)  # 5分钟缓存
    if cached:
        print(f"[Cache] Fund {fund_code} info loaded from cache")
        elapsed = (time.time() - start_time) * 1000
        print(f"[Performance] Total time (cached): {elapsed:.1f}ms")
        return FundInfo(**cached)

    try:
        # 2. 使用异步并行方式获取基金详情
        print(f"\n[API] Fetching fund {fund_code} info with async parallel requests...")
        detail = await ttjj_client.get_fund_detail_info_async(fund_code)

        if not detail or not detail.fund_name:
            # Fallback to fund_service if ttjj fails
            print(f"[Fallback] TTJJ failed, trying fund_service for {fund_code}")
            fund_info = await fund_service.get_fund_info(fund_code)
            if not fund_info:
                raise HTTPException(status_code=404, detail=f"Fund {fund_code} not found")
            return fund_info

        # 3. Convert FundDetailInfo to FundInfo
        from datetime import date

        # Parse nav_date
        nav_date = None
        if detail.nav_date:
            try:
                nav_date = date.fromisoformat(detail.nav_date)
            except:
                pass

        fund_info = FundInfo(
            fund_code=detail.fund_code,
            fund_name=detail.fund_name,
            fund_type=detail.fund_type or None,
            nav=detail.nav,
            nav_date=nav_date,
            total_assets=detail.fund_scale,
            manager=detail.fund_manager or None,
            company=detail.management_company or None,
            benchmark=None,
            # Extended fields
            nav_change_percent=detail.daily_change,
            accumulated_nav=detail.acc_nav,
            risk_level=detail.risk_level,
            rating=detail.rating,
            return_1m=detail.return_1m,
            return_3m=detail.return_3m,
            return_6m=detail.return_6m,
            return_1y=detail.return_1y,
            return_3y=detail.return_3y,
            return_ytd=detail.return_ytd,
            return_since_inception=detail.return_since_inception,
            inception_date=detail.inception_date or None
        )

        # 4. 存入缓存
        cache.set("fund_detail", cache_key, fund_info.model_dump(), ttl=300)

        total_elapsed = (time.time() - start_time) * 1000
        print(f"[Performance] Total time (API): {total_elapsed:.1f}ms")

        return fund_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fund info: {str(e)}")


@router.get("/{fund_code}/holdings", response_model=Fund)
async def get_fund_holdings(fund_code: str, refresh: bool = False):
    """
    Get holdings data for a specific fund.

    - **fund_code**: Fund code (e.g., 000001)
    - **refresh**: Force refresh data from API, skip cache (default: False)
    """
    try:
        fund = await fund_service.get_fund_holdings(fund_code, refresh=refresh)
        if not fund:
            raise HTTPException(status_code=404, detail=f"Fund {fund_code} holdings not found")
        return fund
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fund holdings: {str(e)}")


@router.get("/{fund_code}/asset-allocation", response_model=AssetAllocationHistory)
async def get_asset_allocation(fund_code: str, quarters: int = Query(8, ge=1, le=20)):
    """
    Get asset allocation history for a specific fund.

    - **fund_code**: Fund code (e.g., 000001)
    - **quarters**: Number of quarters to retrieve (1-20, default 8)

    Returns historical asset allocation including:
    - Stock ratio
    - Bond ratio
    - Cash ratio
    - Other assets ratio
    - Net asset value
    """
    try:
        allocations = wind_client.get_asset_allocation_history(fund_code, quarters)

        if not allocations:
            # Return empty response if no data
            return AssetAllocationHistory(
                fund_code=fund_code,
                allocations=[]
            )

        from app.models import AssetAllocation as AssetAllocationModel

        return AssetAllocationHistory(
            fund_code=fund_code,
            allocations=[
                AssetAllocationModel(
                    report_date=a.report_date,
                    stock_ratio=a.stock_ratio,
                    bond_ratio=a.bond_ratio,
                    cash_ratio=a.cash_ratio,
                    other_ratio=a.other_ratio,
                    net_asset=a.net_asset
                )
                for a in allocations
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get asset allocation: {str(e)}")


@router.get("/{fund_code}/intraday-valuation", response_model=FundEstimation)
async def get_intraday_valuation(fund_code: str, request: Request):
    """
    Get intraday valuation history for a specific fund.

    Returns the official real-time estimation data from 天天基金网 (TTJJ).
    Data is collected every 2 minutes during trading hours.

    - **fund_code**: Fund code (e.g., 000001)

    Returns:
        - code: Fund code
        - name: Fund name
        - date: Date (YYYYMMDD)
        - data: List of estimation data points (time, nav, growth)
        - count: Number of data points
        - first_time: First estimation time of the day
        - last_time: Last estimation time of the day
    """
    client = get_estimation_client()
    try:
        estimation = await client.get_fund_estimation(fund_code)
        return estimation
    except EstimationAPIError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get intraday valuation: {str(e)}")


@router.get("/{fund_code}/nav-history")
async def get_nav_history(
    fund_code: str,
    period: str = Query("1y", regex="^(1m|3m|6m|1y|2y|5y)$")
):
    """
    Get NAV history for a specific fund with benchmark comparison.
    【优化版】使用缓存减少Wind API调用

    - **fund_code**: Fund code (e.g., 000001)
    - **period**: Time period (1m, 3m, 6m, 1y, 2y, 5y)

    Returns NAV history including:
    - Fund NAV history
    - Benchmark index history
    - Market index (CSI 300) history
    """
    import time
    start_time = time.time()

    fund_code = fund_code.strip().zfill(6)
    cache_key = f"nav_history_{fund_code}_{period}"

    # 1. 检查缓存（缓存1小时，净值数据不频繁变化）
    from app.utils.cache import cache
    cached = cache.get("nav_history", cache_key, ttl=3600)
    if cached:
        print(f"[Cache] Fund {fund_code} NAV history loaded from cache")
        elapsed = (time.time() - start_time) * 1000
        print(f"[Performance] NAV history (cached): {elapsed:.1f}ms")
        return cached

    try:
        # Calculate date range
        end_date = datetime.now()
        period_map = {
            "1m": timedelta(days=30),
            "3m": timedelta(days=90),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365),
            "2y": timedelta(days=730),
            "5y": timedelta(days=1825),
        }
        start_date = end_date - period_map.get(period, timedelta(days=365))

        # Format dates for Wind API
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        # Get fund NAV history
        fund_nav = wind_client.get_nav_history(fund_code, start_str, end_str)

        # Get fund info to determine benchmark
        fund_info = await fund_service.get_fund_info(fund_code)
        benchmark_str = fund_info.benchmark if fund_info else None

        # Parse benchmark
        benchmark_components = parse_benchmark(benchmark_str)

        # Get benchmark index history if available
        benchmark_history = []
        if benchmark_components.stock_index_code:
            benchmark_history = wind_client.get_index_history(
                benchmark_components.stock_index_code,
                start_str,
                end_str
            )

        # Get market index (CSI 300) history
        market_history = wind_client.get_index_history("000300.SH", start_str, end_str)

        result = {
            "fund_code": fund_code,
            "period": period,
            "fund_nav_history": [
                {"date": n.date, "nav": n.nav, "nav_acc": n.nav_acc}
                for n in fund_nav
            ],
            "benchmark_history": benchmark_history,
            "market_index_history": market_history,
            "benchmark_name": benchmark_components.stock_index_name or "业绩基准",
        }

        # 存入缓存
        cache.set("nav_history", cache_key, result, ttl=3600)

        elapsed = (time.time() - start_time) * 1000
        print(f"[Performance] NAV history (API): {elapsed:.1f}ms")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get NAV history: {str(e)}")


@router.get("/{fund_code}/valuation", response_model=EstimationAPIResponse)
async def get_fund_valuation(fund_code: str):
    """
    Get real-time valuation for a specific fund.

    Returns the latest official real-time estimation data from 天天基金网 (TTJJ).
    This is NOT a calculated valuation - it's the official estimation from the fund platform.

    - **fund_code**: Fund code (e.g., 000001)

    Returns:
        - success: Whether the request was successful
        - message: Response message
        - data: FundEstimation object with latest valuation data
    """
    client = get_estimation_client()
    try:
        estimation = await client.get_fund_estimation(fund_code)

        # If no data available
        if not estimation.data:
            return EstimationAPIResponse(
                success=False,
                message=f"No estimation data available for fund {fund_code}. The market may be closed or data is not yet collected.",
                data=None
            )

        return EstimationAPIResponse(
            success=True,
            message=f"Successfully retrieved latest valuation for {estimation.name or fund_code}",
            data=estimation
        )

    except EstimationAPIError as e:
        return EstimationAPIResponse(
            success=False,
            message=str(e),
            data=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fund valuation: {str(e)}")


class BatchValuationResponse(BaseModel):
    """Batch valuation response model."""
    success: bool
    data: List[EstimationSummary]
    failed_codes: List[str]
    message: str


@router.post("/batch-valuation", response_model=BatchValuationResponse)
async def batch_valuation(fund_codes: List[str]):
    """
    Get real-time valuation for multiple funds.

    Returns the latest official real-time estimation data from 天天基金网 (TTJJ)
    for each fund code in the list.

    - **fund_codes**: List of fund codes (e.g., ["000001", "000002"])

    Returns:
        - success: Whether any valuations were successfully retrieved
        - data: List of EstimationSummary objects for successfully retrieved funds
        - failed_codes: List of fund codes that failed to retrieve
        - message: Response message
    """
    if not fund_codes:
        return BatchValuationResponse(
            success=False,
            data=[],
            failed_codes=[],
            message="No fund codes provided"
        )

    client = get_estimation_client()
    results = []
    failed_codes = []

    for code in fund_codes:
        try:
            estimation = await client.get_fund_estimation(code)
            if estimation.data:
                latest = estimation.data[-1]
                # Get fund info for previous NAV (昨日净值 = 单位净值 nav)
                try:
                    # Use ttjj_client.get_fund_detail_info to get nav
                    import asyncio
                    fund_detail = await asyncio.to_thread(ttjj_client.get_fund_detail_info, code)
                    previous_nav = fund_detail.nav if fund_detail else None
                except Exception:
                    previous_nav = None
                results.append(EstimationSummary(
                    code=estimation.code,
                    name=estimation.name,
                    date=estimation.date,
                    latest_nav=latest.nav,
                    latest_growth=latest.growth,
                    previous_nav=previous_nav,
                    last_time=estimation.last_time or latest.time,
                    data_count=estimation.count
                ))
            else:
                failed_codes.append(code)
        except EstimationAPIError as e:
            print(f"[BatchValuation] EstimationAPIError for {code}: {e}")
            failed_codes.append(code)
        except Exception as e:
            print(f"[BatchValuation] Unexpected error for {code}: {e}")
            import traceback
            traceback.print_exc()
            failed_codes.append(code)

    return BatchValuationResponse(
        success=len(results) > 0,
        data=results,
        failed_codes=failed_codes,
        message=f"Successfully retrieved {len(results)} valuations, {len(failed_codes)} failed"
    )


# ==================== 管理接口 ====================

class CacheStatsResponse(BaseModel):
    """缓存统计信息响应模型。"""
    total_funds: int
    last_update: Optional[str]
    cache_age_hours: Optional[float]


@router.get("/admin/cache-stats", response_model=CacheStatsResponse, tags=["admin"])
async def get_cache_stats():
    """
    获取基金列表缓存统计信息。

    显示缓存的基金总数、最后更新时间等信息。
    """
    try:
        stats = fund_list_cache.get_stats()
        return CacheStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/admin/refresh-cache", tags=["admin"])
async def refresh_cache():
    """
    手动刷新基金列表缓存。

    强制从 AKShare 重新获取最新的基金列表数据。
    """
    try:
        success = fund_list_cache.refresh()
        if success:
            stats = fund_list_cache.get_stats()
            return {
                "success": True,
                "message": "基金列表缓存刷新成功",
                "stats": stats
            }
        else:
            raise HTTPException(status_code=500, detail="缓存刷新失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新缓存失败: {str(e)}")


# ==================== 数据同步管理接口 ====================

from app.services.fund_data_sync_service import fund_data_sync_service


@router.post("/admin/sync-fund-data", tags=["admin"])
async def sync_fund_data(fund_code: Optional[str] = None, limit: Optional[int] = None):
    """
    手动触发基金数据同步。

    - **fund_code**: 指定同步单个基金（可选）
    - **limit**: 限制同步数量，用于测试（可选）

    如果不指定参数，则执行增量同步（只同步未同步过的基金）。
    """
    try:
        if fund_code:
            # 同步单个基金
            async with AsyncSessionLocal() as db:
                success = await fund_data_sync_service.sync_single_fund(fund_code, db)
                return {
                    "success": success,
                    "message": f"基金 {fund_code} 同步{'成功' if success else '失败'}"
                }
        elif limit:
            # 同步前N个基金
            result = await fund_data_sync_service.sync_hot_funds(top_n=limit)
            return {
                "success": True,
                "message": f"已同步 {result.get('success', 0)} 只基金",
                "details": result
            }
        else:
            # 执行增量同步
            result = await fund_data_sync_service.incremental_sync()
            return {
                "success": True,
                "message": f"增量同步完成: 成功 {result.get('success', 0)}, 失败 {result.get('failed', 0)}",
                "details": result
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据同步失败: {str(e)}")


@router.get("/admin/sync-status", tags=["admin"])
async def get_sync_status():
    """
    获取数据同步状态统计。

    返回本地数据库中已同步的基金数量、最新报告期分布等信息。
    """
    from sqlalchemy import func
    from app.db_models import FundHoldingDB, AssetAllocationDB, FundInfoDB
    from sqlalchemy import func, select

    try:
        async with AsyncSessionLocal() as db:
            # 统计已同步的基金数量
            fund_count_result = await db.execute(
                select(func.count(func.distinct(FundInfoDB.fund_code)))
            )
            fund_count = fund_count_result.scalar()

            # 统计持仓数据
            holdings_count_result = await db.execute(
                select(func.count(FundHoldingDB.id))
            )
            holdings_count = holdings_count_result.scalar()

            # 统计资产配置数据
            allocation_count_result = await db.execute(
                select(func.count(AssetAllocationDB.id))
            )
            allocation_count = allocation_count_result.scalar()

            # 获取最新报告期分布
            report_dates_result = await db.execute(
                select(FundHoldingDB.report_date, func.count(FundHoldingDB.id))
                .group_by(FundHoldingDB.report_date)
                .order_by(FundHoldingDB.report_date.desc())
                .limit(5)
            )
            report_dates = [
                {"date": row[0], "count": row[1]}
                for row in report_dates_result.fetchall()
            ]

            return {
                "fund_info_count": fund_count,
                "holdings_count": holdings_count,
                "allocation_count": allocation_count,
                "latest_report_dates": report_dates,
                "status": "healthy"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取同步状态失败: {str(e)}")
