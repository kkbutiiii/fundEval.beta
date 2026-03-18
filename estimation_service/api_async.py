# -*- coding: utf-8 -*-
"""
异步基金估值API服务
基于FastAPI框架提供高性能HTTP API接口
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Optional, List
import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database_async import AsyncFundEstimationDB

# 导入采集器和数据库（用于手动触发）
from database import FundEstimationDB
from collector import FundEstimationCollector

app = FastAPI(
    title="基金估值API服务",
    description="基于FastAPI的异步基金估值数据服务",
    version="2.0.0"
)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fund_estimation.db")
db = AsyncFundEstimationDB(DB_PATH)


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {
        "status": "ok",
        "time": datetime.now().isoformat(),
        "service": "fund-estimation-api-async"
    }


@app.get("/api/v1/fund/estimation")
async def get_fund_estimation(
    code: str = Query(..., description="基金代码，必填"),
    date: Optional[str] = Query(None, description="日期 (YYYYMMDD格式，默认为今日)")
):
    """获取基金日内估值序列"""
    # 参数校验
    if not code:
        raise HTTPException(status_code=400, detail="基金代码不能为空")

    # 处理日期参数
    if date:
        try:
            date_int = int(date)
            if len(date) != 8 or date_int < 20000101 or date_int > 20991231:
                raise HTTPException(status_code=400, detail="日期格式错误，应为YYYYMMDD")
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为YYYYMMDD")
    else:
        # 检查当前时间，如果还没到9:30，返回昨天的数据
        now = datetime.now()
        current_time = now.hour * 100 + now.minute  # 转换为HHMM格式
        
        if current_time < 930:  # 9:30之前
            # 返回昨天的日期
            yesterday = now - timedelta(days=1)
            date_int = int(yesterday.strftime('%Y%m%d'))
        else:
            date_int = int(now.strftime('%Y%m%d'))

    # 异步查询估值数据
    curve = await db.get_fund_curve(code, date_int)

    if not curve:
        return JSONResponse(
            status_code=404,
            content={
                "code": code,
                "date": date_int,
                "data": [],
                "count": 0,
                "message": "未找到数据"
            }
        )

    # 异步获取基金名称
    fund_name = await db.get_fund_name(code)

    # 格式化数据
    data = []
    for item in curve:
        time_val = str(item[0]).zfill(6)
        time_formatted = f"{time_val[:2]}:{time_val[2:4]}:{time_val[4:]}"
        data.append({
            "time": time_formatted,
            "nav": item[1],
            "growth": item[2]
        })

    return {
        "code": code,
        "name": fund_name,
        "date": date_int,
        "data": data,
        "count": len(data),
        "first_time": data[0]["time"] if data else None,
        "last_time": data[-1]["time"] if data else None
    }


@app.get("/api/v1/fund/latest")
async def get_latest_estimations(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制 (默认20，最大100)"),
    order_by: str = Query("estimate_growth", description="排序字段 (默认estimate_growth)")
):
    """获取最新估值（所有基金）"""
    # 只允许特定的排序字段，防止SQL注入
    allowed_order_fields = ['estimate_growth', 'estimate_nav', 'actual_nav', 'fund_code']
    if order_by not in allowed_order_fields:
        order_by = 'estimate_growth'

    # 异步查询
    results = await db.get_latest_estimations(limit=limit, order_by=order_by)

    if not results:
        return {
            "data": [],
            "count": 0,
            "message": "暂无数据"
        }

    # 格式化数据
    data = []
    for row in results:
        data.append({
            "code": row['fund_code'],
            "name": row['fund_name'],
            "nav": row['estimate_nav'],
            "growth": row['estimate_growth'],
            "actual_nav": row['actual_nav']
        })

    return {
        "data": data,
        "count": len(data),
        "order_by": order_by
    }


@app.get("/api/v1/fund/list")
async def get_fund_list(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制 (默认100，最大1000)"),
    offset: int = Query(0, ge=0, description="偏移量 (默认0)")
):
    """获取基金列表"""
    return await db.get_fund_list(limit=limit, offset=offset)


@app.get("/api/v1/system/stats")
async def get_system_stats():
    """获取系统统计信息"""
    # 获取总体统计
    stats = await db.get_statistics()

    # 获取今日统计
    today = int(datetime.now().strftime('%Y%m%d'))
    today_stats = await db.get_statistics(date=today)

    return {
        "total": {
            "fund_count": stats.get('fund_count', 0),
            "total_records": stats.get('total_records', 0),
            "days": stats.get('days', 0)
        },
        "today": {
            "date": today,
            "fund_count": today_stats.get('fund_count', 0),
            "total_records": today_stats.get('total_records', 0),
            "first_time": str(today_stats.get('first_time', '')).zfill(6) if today_stats.get('first_time') else None,
            "last_time": str(today_stats.get('last_time', '')).zfill(6) if today_stats.get('last_time') else None
        },
        "server_time": datetime.now().isoformat()
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """处理404错误"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "接口不存在",
            "path": str(request.url.path),
            "method": request.method
        }
    )


# 创建线程池用于执行同步采集任务
executor = ThreadPoolExecutor(max_workers=1)


async def run_collector_task():
    """在后台线程中运行采集任务"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_collect_job)


def sync_collect_job():
    """同步执行采集任务"""
    from datetime import datetime
    db_path = DB_PATH.replace('\\', '/')
    db = FundEstimationDB(db_path)
    collector = FundEstimationCollector(db)

    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 手动触发采集任务")
    print(f"{'='*60}")

    try:
        count = collector.collect_once(save_basic=True)
        return {"status": "success", "collected": count}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/admin/collect")
async def manual_collect():
    """
    手动触发基金估值采集

    该接口会立即执行一次全量基金估值采集，忽略交易时间限制
    """
    try:
        # 在后台线程中执行采集任务
        asyncio.create_task(run_collector_task())

        return {
            "status": "started",
            "message": "采集任务已在后台启动",
            "time": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动采集任务失败: {str(e)}")


@app.get("/api/v1/admin/collect/status")
async def get_collect_status():
    """获取采集任务状态"""
    # 获取今日统计
    today = int(datetime.now().strftime('%Y%m%d'))
    today_stats = await db.get_statistics(date=today)

    return {
        "today": {
            "date": today,
            "fund_count": today_stats.get('fund_count', 0),
            "total_records": today_stats.get('total_records', 0),
            "first_time": str(today_stats.get('first_time', '')).zfill(6) if today_stats.get('first_time') else None,
            "last_time": str(today_stats.get('last_time', '')).zfill(6) if today_stats.get('last_time') else None
        },
        "server_time": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    print(f"基金估值API服务启动 (异步模式)...")
    print(f"数据库路径: {DB_PATH}")
    print(f"访问地址: http://localhost:50802")
    print(f"API文档: http://localhost:50802/docs")
    print(f"API端点:")
    print(f"  - 健康检查: GET /api/health")
    print(f"  - 基金估值: GET /api/v1/fund/estimation?code=002474&date=20250302")
    print(f"  - 最新估值: GET /api/v1/fund/latest?limit=20")
    print(f"  - 基金列表: GET /api/v1/fund/list?limit=100")
    print(f"  - 系统统计: GET /api/v1/system/stats")
    print(f"  - 手动采集: POST /api/v1/admin/collect")
    print(f"  - 采集状态: GET /api/v1/admin/collect/status")

    uvicorn.run(app, host="0.0.0.0", port=50802)
