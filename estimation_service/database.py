# -*- coding: utf-8 -*-
"""
基金盘中估值数据库模块
"""
import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager


class FundEstimationDB:
    """基金估值数据库操作类"""

    def __init__(self, db_path="fund_estimation.db"):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 基金基础信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fund_basic (
                    fund_code TEXT PRIMARY KEY,
                    fund_name TEXT NOT NULL,
                    fund_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 估值数据主表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fund_estimation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_code TEXT NOT NULL,
                    estimate_date INTEGER NOT NULL,
                    estimate_time INTEGER NOT NULL,
                    estimate_nav REAL,
                    estimate_growth REAL,
                    actual_nav REAL,
                    actual_growth REAL,
                    deviation REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fund_date_time
                ON fund_estimation(fund_code, estimate_date, estimate_time)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date_time
                ON fund_estimation(estimate_date, estimate_time)
            """)

            conn.commit()
            print(f"数据库初始化完成: {self.db_path}")

    def save_fund_basic(self, fund_code, fund_name, fund_type=None):
        """保存或更新基金基础信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fund_basic (fund_code, fund_name, fund_type, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(fund_code) DO UPDATE SET
                    fund_name = excluded.fund_name,
                    fund_type = excluded.fund_type,
                    updated_at = excluded.updated_at
            """, (fund_code, fund_name, fund_type, datetime.now()))
            conn.commit()

    def save_estimation(self, fund_code, estimate_date, estimate_time,
                        estimate_nav, estimate_growth, actual_nav=None,
                        actual_growth=None, deviation=None):
        """
        保存单条估值数据

        Args:
            fund_code: 基金代码
            estimate_date: 日期 (YYYYMMDD格式)
            estimate_time: 时间 (HHMMSS格式)
            estimate_nav: 估算净值
            estimate_growth: 估算增长率
            actual_nav: 实际净值
            actual_growth: 实际增长率
            deviation: 估算偏差
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fund_estimation
                (fund_code, estimate_date, estimate_time, estimate_nav,
                 estimate_growth, actual_nav, actual_growth, deviation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fund_code, estimate_date, estimate_time, estimate_nav,
                  estimate_growth, actual_nav, actual_growth, deviation))
            conn.commit()

    def save_estimation_batch(self, data_list):
        """
        批量保存估值数据（性能更好）

        Args:
            data_list: 列表，每个元素是字典包含所有字段
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO fund_estimation
                (fund_code, estimate_date, estimate_time, estimate_nav,
                 estimate_growth, actual_nav, actual_growth, deviation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data_list)
            conn.commit()

    def get_fund_curve(self, fund_code, date):
        """
        获取单基金某日的估值曲线

        Returns:
            list: [(time, nav, growth), ...]
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT estimate_time, estimate_nav, estimate_growth
                FROM fund_estimation
                WHERE fund_code = ? AND estimate_date = ?
                ORDER BY estimate_time
            """, (fund_code, date))
            return cursor.fetchall()

    def get_latest_estimations(self, limit=20, order_by='estimate_growth'):
        """
        获取最新一批估值数据（按增长率排序）

        Returns:
            list: 包含最新估值的基金列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 获取最新的时间点
            cursor.execute("""
                SELECT estimate_date, estimate_time
                FROM fund_estimation
                ORDER BY estimate_date DESC, estimate_time DESC
                LIMIT 1
            """)
            latest = cursor.fetchone()

            if not latest:
                return []

            latest_date, latest_time = latest

            # 获取该时间点的所有基金估值
            cursor.execute(f"""
                SELECT e.fund_code, b.fund_name, e.estimate_nav,
                       e.estimate_growth, e.actual_nav
                FROM fund_estimation e
                LEFT JOIN fund_basic b ON e.fund_code = b.fund_code
                WHERE e.estimate_date = ? AND e.estimate_time = ?
                ORDER BY e.{order_by} DESC
                LIMIT ?
            """, (latest_date, latest_time, limit))

            return cursor.fetchall()

    def get_statistics(self, date=None):
        """
        获取统计信息

        Returns:
            dict: 统计信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if date:
                # 指定日期的统计
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT fund_code) as fund_count,
                        COUNT(*) as total_records,
                        MIN(estimate_time) as first_time,
                        MAX(estimate_time) as last_time
                    FROM fund_estimation
                    WHERE estimate_date = ?
                """, (date,))
            else:
                # 总体统计
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT fund_code) as fund_count,
                        COUNT(*) as total_records,
                        COUNT(DISTINCT estimate_date) as days
                    FROM fund_estimation
                """)

            row = cursor.fetchone()
            return dict(row) if row else {}

    def cleanup_old_data(self, keep_days=30):
        """清理旧数据"""
        from datetime import timedelta

        cutoff_date = (datetime.now() - timedelta(days=keep_days)).strftime('%Y%m%d')

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM fund_estimation
                WHERE estimate_date < ?
            """, (cutoff_date,))
            deleted = cursor.rowcount
            conn.commit()
            print(f"已清理 {deleted} 条 {cutoff_date} 之前的数据")
            return deleted


if __name__ == "__main__":
    # 测试数据库
    db = FundEstimationDB()

    # 测试保存
    db.save_fund_basic("002474", "中邮睿信增强债券A", "债券型")

    # 测试查询
    stats = db.get_statistics()
    print(f"数据库统计: {stats}")

    print("数据库测试完成")
