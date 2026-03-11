# -*- coding: utf-8 -*-
"""
基金估值数据采集调度器
每2分钟采集一次
"""
import time
from datetime import datetime, time as dt_time, timedelta
from database import FundEstimationDB
from collector import FundEstimationCollector


class FundEstimationScheduler:
    """基金估值采集调度器"""

    def __init__(self, interval_minutes=2, db_path="fund_estimation.db"):
        """
        Args:
            interval_minutes: 采集间隔（分钟）
            db_path: 数据库路径
        """
        self.interval = interval_minutes
        self.db = FundEstimationDB(db_path)
        self.collector = FundEstimationCollector(self.db)
        self.is_running = False
        self.collection_count = 0

    def is_trading_time(self):
        """
        检查当前是否为交易时间

        交易时间：
        - 上午：9:30 - 11:30
        - 下午：13:00 - 15:00
        - 工作日：周一到周五
        """
        now = datetime.now()

        # 检查是否为工作日（0=周一, 6=周日）
        if now.weekday() >= 5:  # 周六或周日
            return False

        current_time = now.time()

        # 上午交易时间 9:30 - 11:30
        morning_start = dt_time(9, 30)
        morning_end = dt_time(11, 30)

        # 下午交易时间 13:00 - 15:00
        afternoon_start = dt_time(13, 0)
        afternoon_end = dt_time(15, 0)

        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end

        return is_morning or is_afternoon

    def is_trading_day(self):
        """
        判断是否为交易日（工作日）

        目前仅处理周末，法定节假日需后续通过配置文件或API处理

        返回:
            bool: 是否为交易日
        """
        now = datetime.now()
        # 检查是否为工作日（0=周一, 6=周日）
        return now.weekday() < 5  # 周一到周五为交易日

    def get_next_trading_start(self):
        """
        计算到下一个交易时段开始的时间（秒）

        返回:
            int: 等待秒数
        """
        now = datetime.now()
        current_time = now.time()

        # 上午开盘前 -> 等待到9:30
        if current_time < dt_time(9, 30):
            target = datetime.combine(now.date(), dt_time(9, 30))
            return int((target - now).total_seconds())

        # 上午收盘后、下午开盘前 -> 等待到13:00
        elif dt_time(11, 30) <= current_time < dt_time(13, 0):
            target = datetime.combine(now.date(), dt_time(13, 0))
            return int((target - now).total_seconds())

        # 下午收盘后 -> 等待到次日9:30
        elif current_time >= dt_time(15, 0):
            next_day = now + timedelta(days=1)
            # 如果次日是周末，继续找下一个工作日
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            target = datetime.combine(next_day.date(), dt_time(9, 30))
            return int((target - now).total_seconds())

        # 在交易时间内
        return 0

    def collect_job(self):
        """定时任务：执行数据采集"""
        now = datetime.now()
        print(f"\n{'='*60}")
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 执行定时采集任务")
        print(f"{'='*60}")

        # 检查是否在交易时间
        if not self.is_trading_time():
            print("当前非交易时间，跳过采集")
            # 如果过了15:00，可以执行一些清理工作
            if now.time() > dt_time(15, 0) and now.time() < dt_time(15, 5):
                self.after_trading_tasks()
            return

        # 执行采集
        try:
            count = self.collector.collect_once(save_basic=(self.collection_count == 0))
            self.collection_count += 1

            # 每10次采集打印一次统计
            if self.collection_count % 10 == 0:
                self.print_statistics()

        except Exception as e:
            print(f"采集失败: {e}")
            import traceback
            traceback.print_exc()

    def after_trading_tasks(self):
        """收盘后的任务"""
        print("\n交易结束，执行收盘后任务...")

        # 打印今日统计
        today = int(datetime.now().strftime('%Y%m%d'))
        stats = self.db.get_statistics(date=today)
        print(f"\n今日采集统计:")
        print(f"  基金数量: {stats.get('fund_count', 0)}")
        print(f"  总记录数: {stats.get('total_records', 0)}")
        print(f"  首次采集: {stats.get('first_time', 'N/A')}")
        print(f"  最后采集: {stats.get('last_time', 'N/A')}")

    def print_statistics(self):
        """打印统计信息"""
        stats = self.collector.get_stats()
        db_stats = self.db.get_statistics()

        print(f"\n{'='*60}")
        print("采集统计")
        print(f"{'='*60}")
        print(f"本次运行采集次数: {stats['total_collections']}")
        print(f"本次运行采集记录: {stats['total_records']}")
        print(f"数据库总记录数: {db_stats.get('total_records', 0)}")
        print(f"监控基金数量: {db_stats.get('fund_count', 0)}")
        print(f"错误次数: {stats['errors']}")
        print(f"{'='*60}\n")

    def run(self):
        """启动调度器"""
        print(f"\n{'='*60}")
        print("基金估值数据采集调度器启动")
        print(f"{'='*60}")
        print(f"采集间隔: {self.interval} 分钟")
        print(f"数据库: {self.db.db_path}")
        print(f"交易时间: 9:30-11:30, 13:00-15:00 (工作日)")
        print(f"{'='*60}\n")

        # 检查是否在交易时间
        if self.is_trading_time():
            print("当前为交易时间，立即执行首次采集...")
            self.collect_job()
        else:
            wait_seconds = self.get_next_trading_start()
            next_time = datetime.now() + timedelta(seconds=wait_seconds)
            print(f"当前非交易时间，等待到 {next_time.strftime('%Y-%m-%d %H:%M:%S')} 开始采集...")
            time.sleep(wait_seconds)
            self.collect_job()

        # 运行循环
        self.is_running = True
        print(f"\n调度器运行中，每 {self.interval} 分钟采集一次...")
        print("按 Ctrl+C 停止\n")

        try:
            while self.is_running:
                if self.is_trading_time():
                    # 在交易时间内，执行采集
                    self.collect_job()

                    # 计算下一次采集时间
                    next_run = time.time() + self.interval * 60

                    # 等待到下一次采集，但要检查是否跨午休或收盘
                    while time.time() < next_run and self.is_running:
                        if not self.is_trading_time():
                            # 交易时间结束，跳出等待
                            break
                        time.sleep(1)
                else:
                    # 非交易时间，等待到下一个交易时段
                    wait_seconds = self.get_next_trading_start()
                    if wait_seconds > 0:
                        next_time = datetime.now() + timedelta(seconds=wait_seconds)
                        print(f"\n交易时段结束，下次采集时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        time.sleep(wait_seconds)

        except KeyboardInterrupt:
            print("\n\n收到停止信号，正在关闭...")
            self.stop()

    def stop(self):
        """停止调度器"""
        self.is_running = False
        print("调度器已停止")
        self.print_statistics()

    def run_once(self):
        """仅运行一次（用于测试）"""
        print("执行单次采集...")
        self.collect_job()
        print("完成")


if __name__ == "__main__":
    import sys

    # 创建调度器（2分钟间隔）
    scheduler = FundEstimationScheduler(interval_minutes=2)

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 单次运行模式
        scheduler.run_once()
    else:
        # 持续运行模式
        scheduler.run()
