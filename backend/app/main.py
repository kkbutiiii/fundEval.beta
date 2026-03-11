"""
Fund Valuation API - FastAPI main application.
"""
import os

# 禁用代理，避免 AKShare 访问东方财富时超时
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import funds_router, portfolios_router
from app.database import init_db, close_db
from app.utils.fund_list_cache import fund_list_cache, start_scheduler
from app.utils.intraday_cache import intraday_cache
from app.services.valuation_engine import valuation_engine
from app.services.fund_data_sync_service import run_daily_sync, run_full_sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name}")
    print(f"Debug mode: {settings.debug}")

    # Initialize database
    print("Initializing database...")
    await init_db()
    print("Database initialized")

    # 启动时确保基金列表已加载
    if fund_list_cache.get_last_update_time() is None:
        fund_list_cache.refresh()

    # 启动定时任务调度器（每天凌晨刷新基金列表）
    scheduler = start_scheduler()

    # 添加日内估值采样任务（每30秒）
    # 使用内存缓存存储最近访问过的基金的估值数据
    valuation_cache: dict = {}

    def sample_intraday_valuations():
        """Sample valuations for tracked funds."""
        import asyncio

        # Only sample funds that have been recently accessed
        for fund_code in list(valuation_cache.keys()):
            try:
                # Run async calculation in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    valuation_engine.calculate_valuation(fund_code)
                )
                loop.close()

                if result:
                    intraday_cache.add_sample(
                        fund_code,
                        result.estimated_nav,
                        result.estimated_change_percent
                    )
            except Exception as e:
                print(f"Error sampling valuation for {fund_code}: {e}")

        # Clean up old entries (not accessed in last hour)
        intraday_cache.cleanup_old_data(max_age_minutes=300)

    # Add intraday sampling job (only during trading hours 9:30-15:00)
    intraday_trigger = IntervalTrigger(seconds=30)
    scheduler.add_job(
        sample_intraday_valuations,
        trigger=intraday_trigger,
        id='intraday_sampling',
        replace_existing=True
    )

    # 添加基金数据定时同步任务
    # 每天凌晨 2:00 执行增量同步
    from apscheduler.triggers.cron import CronTrigger
    scheduler.add_job(
        lambda: asyncio.create_task(run_daily_sync()),
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_fund_sync',
        name='每日基金数据增量同步',
        replace_existing=True
    )
    print("[Scheduler] Daily fund data sync scheduled at 02:00")

    # Store reference to valuation cache for router access
    app.state.valuation_tracking = valuation_cache

    yield

    # Shutdown
    print("Shutting down...")
    scheduler.shutdown()
    await close_db()
    print("Database connections closed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Real-time fund valuation API based on quarterly holdings data",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(funds_router)
    app.include_router(portfolios_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Fund Valuation API",
            "version": "0.1.0",
            "docs_url": "/docs",
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
