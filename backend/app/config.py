"""
Configuration module for the fund valuation system.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    # App settings
    app_name: str = "Fund Valuation API"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Server settings
    # 默认端口: 50801 (与前端代理配置保持一致)
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "50801"))

    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./fund_valuation.db")

    # Security settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars-long")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Cache settings (in seconds)
    cache_ttl_fund_list: int = 86400  # 1 day
    cache_ttl_fund_holdings: int = 86400  # 1 day
    cache_ttl_stock_price: int = 5  # 5 seconds
    cache_ttl_valuation: int = 10  # 10 seconds

    # 基金估值API服务配置 (fund_estimation_system)
    # 默认端口: 50802 (独立的估值计算服务)
    estimation_api_base_url: str = os.getenv("ESTIMATION_API_BASE_URL", "http://localhost:50802")
    estimation_api_timeout: int = int(os.getenv("ESTIMATION_API_TIMEOUT", "10"))

    # Fund type mapping for index selection
    fund_type_mapping: dict = {
        "白酒": {"keywords": ["白酒", "酒类"], "index": "399987.SZ", "index_name": "中证白酒"},
        "医药": {"keywords": ["医药", "医疗", "生物", "健康", "药"], "index": "399441.SZ", "index_name": "国证生物医药"},
        "新能源": {"keywords": ["新能源", "光伏", "锂电", "储能", "风电"], "index": "399808.SZ", "index_name": "中证新能源"},
        "科技": {"keywords": ["科技", "半导体", "芯片", "TMT", "人工智能", "AI", "计算机", "通信"], "index": "000938.SH", "index_name": "中证科技"},
        "消费": {"keywords": ["消费", "食品饮料", "家电", "零售"], "index": "399997.SZ", "index_name": "中证消费"},
        "银行": {"keywords": ["银行", "金融"], "index": "399986.SZ", "index_name": "中证银行"},
        "军工": {"keywords": ["军工", "国防", "航天", "航空"], "index": "399967.SZ", "index_name": "中证军工"},
        "地产": {"keywords": ["地产", "房地产", "基建", "建筑"], "index": "931775.CSI", "index_name": "中证地产"},
        "券商": {"keywords": ["券商", "证券"], "index": "399975.SZ", "index_name": "中证全指证券公司"},
        "煤炭": {"keywords": ["煤炭", "能源"], "index": "399998.SZ", "index_name": "中证煤炭"},
        "钢铁": {"keywords": ["钢铁", "有色", "金属"], "index": "930653.CSI", "index_name": "中证钢铁"},
        "汽车": {"keywords": ["汽车", "新能源汽车", "电动车"], "index": "399976.SZ", "index_name": "中证新能源汽车"},
        "传媒": {"keywords": ["传媒", "游戏", "影视", "动漫"], "index": "399971.SZ", "index_name": "中证传媒"},
    }

    # Default index for unknown fund types
    default_index: str = "000300.SH"
    default_index_name: str = "沪深300"

    # Market indices
    market_indices: dict = {
        "000300.SH": {"name": "沪深300", "exchange": "sh"},
        "000001.SH": {"name": "上证指数", "exchange": "sh"},
        "399001.SZ": {"name": "深证成指", "exchange": "sz"},
        "399006.SZ": {"name": "创业板指", "exchange": "sz"},
        "399987.SZ": {"name": "中证白酒", "exchange": "sz"},
        "399441.SZ": {"name": "国证生物医药", "exchange": "sz"},
        "399808.SZ": {"name": "中证新能源", "exchange": "sz"},
        "000938.SH": {"name": "中证科技", "exchange": "sh"},
        "399997.SZ": {"name": "中证消费", "exchange": "sz"},
        "399986.SZ": {"name": "中证银行", "exchange": "sz"},
        "399967.SZ": {"name": "中证军工", "exchange": "sz"},
        "931775.CSI": {"name": "中证地产", "exchange": "csi"},
        "399975.SZ": {"name": "中证全指证券公司", "exchange": "sz"},
        "399998.SZ": {"name": "中证煤炭", "exchange": "sz"},
        "930653.CSI": {"name": "中证钢铁", "exchange": "csi"},
        "399976.SZ": {"name": "中证新能源汽车", "exchange": "sz"},
        "399971.SZ": {"name": "中证传媒", "exchange": "sz"},
    }

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
