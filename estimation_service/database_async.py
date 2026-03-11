# -*- coding: utf-8 -*-
"""
异步基金盘中估值数据库模块
基于aiosqlite实现异步SQLite操作
"""
import aiosqlite
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


class AsyncFundEstimationDB:
    """异步基金估值数据库操作类"""

    def __init__(self, db_path: str = "fund_estimation.db"):
        self.db_path = db_path

    async def get_connection(self):
        """获取异步数据库连接"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn

    async def get_fund_curve(self, fund_code: str, date: int) -> List[tuple]:
        """获取单基金某日的估值曲线"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT estimate_time, estimate_nav, estimate_growth
                FROM fund_estimation
                WHERE fund_code = ? AND estimate_date = ?
                ORDER BY estimate_time
            """, (fund_code, date)) as cursor:
                return await cursor.fetchall()

    async def get_fund_name(self, fund_code: str) -> Optional[str]:
        """获取基金名称"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT fund_name FROM fund_basic WHERE fund_code = ?",
                (fund_code,)
            ) as cursor:
                row = await cursor.fetchone()
                return row['fund_name'] if row else None

    async def get_latest_estimations(self, limit: int = 20,
                                     order_by: str = 'estimate_growth') -> List[aiosqlite.Row]:
        """获取最新一批估值数据"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            # 获取最新的时间点
            async with conn.execute("""
                SELECT estimate_date, estimate_time
                FROM fund_estimation
                ORDER BY estimate_date DESC, estimate_time DESC
                LIMIT 1
            """) as cursor:
                latest = await cursor.fetchone()

            if not latest:
                return []

            latest_date, latest_time = latest

            # 获取该时间点的所有基金估值
            async with conn.execute(f"""
                SELECT e.fund_code, b.fund_name, e.estimate_nav,
                       e.estimate_growth, e.actual_nav
                FROM fund_estimation e
                LEFT JOIN fund_basic b ON e.fund_code = b.fund_code
                WHERE e.estimate_date = ? AND e.estimate_time = ?
                ORDER BY e.{order_by} DESC
                LIMIT ?
            """, (latest_date, latest_time, limit)) as cursor:
                return await cursor.fetchall()

    async def get_fund_list(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """获取基金列表"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            # 查询基金列表
            async with conn.execute("""
                SELECT DISTINCT b.fund_code, b.fund_name, b.fund_type
                FROM fund_basic b
                INNER JOIN fund_estimation e ON b.fund_code = e.fund_code
                ORDER BY b.fund_code
                LIMIT ? OFFSET ?
            """, (limit, offset)) as cursor:
                rows = await cursor.fetchall()

            # 获取总数
            async with conn.execute("""
                SELECT COUNT(DISTINCT fund_code) FROM fund_estimation
            """) as cursor:
                total_row = await cursor.fetchone()
                total = total_row[0] if total_row else 0

            data = [{
                "code": row['fund_code'],
                "name": row['fund_name'],
                "type": row['fund_type']
            } for row in rows]

            return {
                "data": data,
                "count": len(data),
                "total": total,
                "limit": limit,
                "offset": offset
            }

    async def get_statistics(self, date: Optional[int] = None) -> Dict[str, Any]:
        """获取统计信息"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            if date:
                async with conn.execute("""
                    SELECT
                        COUNT(DISTINCT fund_code) as fund_count,
                        COUNT(*) as total_records,
                        MIN(estimate_time) as first_time,
                        MAX(estimate_time) as last_time
                    FROM fund_estimation
                    WHERE estimate_date = ?
                """, (date,)) as cursor:
                    row = await cursor.fetchone()
            else:
                async with conn.execute("""
                    SELECT
                        COUNT(DISTINCT fund_code) as fund_count,
                        COUNT(*) as total_records,
                        COUNT(DISTINCT estimate_date) as days
                    FROM fund_estimation
                """) as cursor:
                    row = await cursor.fetchone()

            return dict(row) if row else {}


if __name__ == "__main__":
    import asyncio

    async def test():
        db = AsyncFundEstimationDB()
        stats = await db.get_statistics()
        print(f"异步数据库测试 - 统计: {stats}")

    asyncio.run(test())
