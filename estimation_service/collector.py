# -*- coding: utf-8 -*-
"""
基金估值数据采集器
"""
import akshare as ak
import pandas as pd
from datetime import datetime
import time
import traceback


class FundEstimationCollector:
    """基金估值数据采集器"""

    def __init__(self, db):
        """
        Args:
            db: FundEstimationDB 实例
        """
        self.db = db
        self.stats = {
            'total_collections': 0,
            'total_records': 0,
            'errors': 0,
            'start_time': None
        }

    def fetch_estimation_data(self, symbol='全部'):
        """
        从AKShare获取估值数据

        Args:
            symbol: 基金类型筛选

        Returns:
            DataFrame: 估值数据
        """
        try:
            df = ak.fund_value_estimation_em(symbol=symbol)
            return df
        except Exception as e:
            print(f"获取估值数据失败: {e}")
            traceback.print_exc()
            return None

    def fetch_all_estimation_data(self):
        """
        获取所有类型基金的估值数据（解决20000只限制问题）
        混合策略：先获取"全部"20000条，再用分类获取补充可能的遗漏
        """
        all_types = ['股票型', '混合型', '债券型', '指数型', 'QDII', 'ETF联接', 'LOF']
        all_rows = []
        seen_codes = set()

        # 第一步：获取"全部"20000条（这是最主要的数据源）
        print("  正在获取全部基金数据...")
        try:
            df_all = ak.fund_value_estimation_em(symbol='全部')
            if df_all is not None and not df_all.empty:
                for _, row in df_all.iterrows():
                    code = row['基金代码']
                    if code not in seen_codes:
                        seen_codes.add(code)
                        all_rows.append(row)
                print(f"  从 [全部] 获取 {len(df_all)} 条，累计 {len(seen_codes)} 条")
        except Exception as e:
            print(f"  获取 [全部] 失败: {e}")

        # 第二步：用分类获取补充（某些基金可能在分类中但不在前20000）
        print("  正在用分类数据补充...")
        for fund_type in all_types:
            try:
                df = ak.fund_value_estimation_em(symbol=fund_type)
                if df is not None and not df.empty:
                    added = 0
                    for _, row in df.iterrows():
                        code = row['基金代码']
                        if code not in seen_codes:
                            seen_codes.add(code)
                            all_rows.append(row)
                            added += 1
                    print(f"  从 [{fund_type}] 补充 {added} 条，累计 {len(seen_codes)} 条")
            except Exception as e:
                print(f"  获取 [{fund_type}] 失败: {e}")

        if all_rows:
            return pd.DataFrame(all_rows)
        return None

    def parse_estimation_row(self, row, columns, now):
        """
        解析单行估值数据

        Args:
            row: DataFrame的行数据
            columns: 列名列表
            now: 当前时间

        Returns:
            tuple: 解析后的数据，用于批量插入
        """
        # 提取动态列名
        estimate_value_col = [c for c in columns if '估算数据-估算值' in c][0]
        estimate_growth_col = [c for c in columns if '估算数据-估算增长率' in c][0]
        actual_nav_col = [c for c in columns if '公布数据-单位净值' in c][0]
        actual_growth_col = [c for c in columns if '公布数据-日增长率' in c][0]
        deviation_col = '估算偏差' if '估算偏差' in columns else None

        fund_code = row['基金代码']
        fund_name = row['基金名称']

        # 解析数值
        estimate_nav = self._parse_float(row[estimate_value_col])
        estimate_growth = self._parse_percent(row[estimate_growth_col])
        actual_nav = self._parse_float(row[actual_nav_col])
        actual_growth = self._parse_percent(row[actual_growth_col])
        deviation = self._parse_percent(row[deviation_col]) if deviation_col else None

        # 日期时间格式
        estimate_date = int(now.strftime('%Y%m%d'))
        estimate_time = int(now.strftime('%H%M%S'))

        return (
            fund_code, estimate_date, estimate_time,
            estimate_nav, estimate_growth, actual_nav, actual_growth, deviation
        ), fund_name

    def _parse_float(self, value):
        """解析浮点数"""
        if pd.isna(value) or value == '---' or value == '':
            return None
        try:
            return float(str(value).replace('%', ''))
        except:
            return None

    def _parse_percent(self, value):
        """解析百分比"""
        if pd.isna(value) or value == '---' or value == '':
            return None
        try:
            return float(str(value).replace('%', ''))
        except:
            return None

    def collect_once(self, save_basic=True):
        """
        执行一次数据采集

        Args:
            save_basic: 是否保存基金基础信息

        Returns:
            int: 采集到的记录数
        """
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始采集...")

        # 获取数据（使用新的方法解决20000只限制）
        df = self.fetch_all_estimation_data()
        if df is None or df.empty:
            print("未获取到数据")
            self.stats['errors'] += 1
            return 0

        now = datetime.now()
        columns = df.columns.tolist()

        # 准备批量插入数据
        data_list = []
        fund_basic_list = []

        # 样本基金日志记录（用于诊断抖动问题）
        sample_codes = ['002474', '000001', '110022', '000828', '002207']
        sample_logs = []

        for _, row in df.iterrows():
            try:
                parsed_data, fund_name = self.parse_estimation_row(row, columns, now)

                # 记录样本基金的原始数据（用于抖动诊断）
                fund_code = row['基金代码']
                if fund_code in sample_codes:
                    estimate_value_col = [c for c in columns if '估算数据-估算值' in c][0] if [c for c in columns if '估算数据-估算值' in c] else None
                    estimate_growth_col = [c for c in columns if '估算数据-估算增长率' in c][0] if [c for c in columns if '估算数据-估算增长率' in c] else None
                    sample_logs.append({
                        'code': fund_code,
                        'name': fund_name,
                        'nav': row.get(estimate_value_col) if estimate_value_col else None,
                        'growth': row.get(estimate_growth_col) if estimate_growth_col else None
                    })

                data_list.append(parsed_data)

                if save_basic:
                    fund_basic_list.append({
                        'fund_code': parsed_data[0],
                        'fund_name': fund_name,
                        'fund_type': None  # 可以在后续补充
                    })

            except Exception as e:
                print(f"解析数据失败: {e}")
                continue

        # 打印样本基金原始数据（用于抖动诊断）
        if sample_logs:
            print("\n[样本基金原始数据 - 用于诊断抖动]")
            for log in sample_logs:
                print(f"  {log['code']} {log['name']}: "
                      f"估算值={log['nav']}, 增长率={log['growth']}")
            print()

        # 批量保存估值数据
        if data_list:
            try:
                self.db.save_estimation_batch(data_list)
                print(f"已保存 {len(data_list)} 条估值数据")
            except Exception as e:
                print(f"保存估值数据失败: {e}")
                traceback.print_exc()
                self.stats['errors'] += 1
                return 0

        # 保存基金基础信息（第一批数据时保存）
        if save_basic and fund_basic_list:
            try:
                for fund in fund_basic_list[:100]:  # 只保存前100个作为示例
                    self.db.save_fund_basic(
                        fund['fund_code'],
                        fund['fund_name'],
                        fund['fund_type']
                    )
                print(f"已保存 {len(fund_basic_list[:100])} 条基金基础信息")
            except Exception as e:
                print(f"保存基础信息失败: {e}")

        # 更新统计
        self.stats['total_collections'] += 1
        self.stats['total_records'] += len(data_list)

        print(f"本次采集完成: {len(data_list)} 条记录")
        return len(data_list)

    def get_stats(self):
        """获取采集统计信息"""
        return self.stats.copy()


if __name__ == "__main__":
    from database import FundEstimationDB

    # 测试采集器
    db = FundEstimationDB()
    collector = FundEstimationCollector(db)

    # 执行一次采集
    count = collector.collect_once(save_basic=True)

    # 查询统计
    db_stats = db.get_statistics()
    print(f"\n数据库统计: {db_stats}")

    # 查询最新数据
    latest = db.get_latest_estimations(limit=10)
    print(f"\n最新估值TOP10:")
    for item in latest:
        print(f"  {item['fund_code']} {item['fund_name']}: {item['estimate_growth']}%")
