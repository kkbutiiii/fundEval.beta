"""
基金数据持久化存储模型
存储基金基本信息、持仓、资产配置等季度更新数据
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, DateTime, Integer, Text, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.database import Base


class FundInfoDB(Base):
    """基金基本信息表 - 季度更新"""
    __tablename__ = "fund_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(10), nullable=False, index=True, unique=True)
    fund_name = Column(String(200), nullable=False)
    fund_type = Column(String(50))
    company = Column(String(100))
    manager = Column(String(100))
    benchmark = Column(Text)

    # 最新净值信息（每日更新）
    latest_nav = Column(Float)
    nav_date = Column(DateTime)

    # 数据时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    holdings = relationship("FundHoldingDB", back_populates="fund_info", lazy="dynamic")
    asset_allocations = relationship("AssetAllocationDB", back_populates="fund_info", lazy="dynamic")

    __table_args__ = (
        Index('idx_fund_code', 'fund_code'),
    )


class FundHoldingDB(Base):
    """基金持仓明细表 - 季度更新"""
    __tablename__ = "fund_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(10), ForeignKey("fund_info.fund_code"), nullable=False, index=True)

    # 报告期
    report_date = Column(String(8), nullable=False, index=True)  # YYYYMMDD格式

    # 股票持仓（前10大重仓）
    stock_holdings = Column(JSON, default=list)  # [{stock_code, stock_name, weight, shares, market_value}]

    # 债券持仓
    bond_holdings = Column(JSON, default=list)  # [{bond_code, bond_name, weight, market_value, is_convertible}]

    # 持仓统计
    top10_total_weight = Column(Float, default=0)
    total_stock_ratio = Column(Float, default=0)
    total_bond_ratio = Column(Float, default=0)
    bond_total_weight = Column(Float, default=0)
    convertible_total_weight = Column(Float, default=0)

    # 原始HTML或API响应（用于调试）
    raw_data = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    fund_info = relationship("FundInfoDB", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint('fund_code', 'report_date', name='uix_fund_holdings'),
        Index('idx_fund_report', 'fund_code', 'report_date'),
    )


class AssetAllocationDB(Base):
    """基金资产配置历史表 - 季度更新"""
    __tablename__ = "asset_allocations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(10), ForeignKey("fund_info.fund_code"), nullable=False, index=True)

    # 报告期
    report_date = Column(String(8), nullable=False, index=True)  # YYYYMMDD格式

    # 资产配置比例
    stock_ratio = Column(Float, default=0)  # 股票占净比(%)
    bond_ratio = Column(Float, default=0)   # 债券占净比(%)
    cash_ratio = Column(Float, default=0)   # 现金占净比(%)
    other_ratio = Column(Float, default=0)  # 其他占净比(%)
    net_asset = Column(Float, default=0)    # 净资产(亿元)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    fund_info = relationship("FundInfoDB", back_populates="asset_allocations")

    __table_args__ = (
        UniqueConstraint('fund_code', 'report_date', name='uix_fund_allocation'),
        Index('idx_allocation_fund_report', 'fund_code', 'report_date'),
    )


class FundDataSyncLog(Base):
    """基金数据同步日志表"""
    __tablename__ = "fund_data_sync_log"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 同步类型
    sync_type = Column(String(20), nullable=False, index=True)  # 'full', 'incremental', 'quarterly'

    # 同步状态
    status = Column(String(20), nullable=False)  # 'running', 'completed', 'failed'

    # 同步范围
    start_fund_code = Column(String(10))
    end_fund_code = Column(String(10))
    total_funds = Column(Integer, default=0)
    processed_funds = Column(Integer, default=0)
    failed_funds = Column(Integer, default=0)

    # 同步详情
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)

    # 数据时间戳（用于判断是否需要更新）
    data_report_date = Column(String(8))  # 同步的数据报告期

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_sync_log_type_time', 'sync_type', 'created_at'),
    )
