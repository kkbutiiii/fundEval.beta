#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基金估值系统统一启动脚本
同时启动数据采集调度器和FastAPI服务

使用方法:
    python run_all.py             # 默认启动（采集间隔2分钟）
    python run_all.py --interval 5  # 指定采集间隔为5分钟
    python run_all.py --port 8080   # 指定API服务端口
"""
import sys
import os
import time
import threading
import signal
import argparse
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from api_async import app, DB_PATH
from scheduler import FundEstimationScheduler
from database import FundEstimationDB
from collector import FundEstimationCollector


# 全局变量用于协调关闭
scheduler_instance = None
scheduler_thread = None
shutdown_event = threading.Event()


def run_initial_collection(db_path):
    """
    启动时立即执行一次采集
    忽略交易时间限制
    """
    print("\n" + "=" * 60)
    print("启动时立即采集")
    print("=" * 60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在执行启动采集...")

    try:
        db = FundEstimationDB(db_path)
        collector = FundEstimationCollector(db)
        count = collector.collect_once(save_basic=True)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动采集完成: {count} 条记录")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 启动采集失败: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 60 + "\n")


# 全局变量用于协调关闭
scheduler_instance = None
scheduler_thread = None
shutdown_event = threading.Event()


def run_scheduler(interval_minutes=2, db_path="fund_estimation.db"):
    """
    在后台线程中运行调度器

    Args:
        interval_minutes: 采集间隔（分钟）
        db_path: 数据库文件路径
    """
    global scheduler_instance

    # 创建调度器实例
    scheduler_instance = FundEstimationScheduler(
        interval_minutes=interval_minutes,
        db_path=db_path
    )

    # 覆盖调度器的stop方法，使其响应shutdown_event
    original_stop = scheduler_instance.stop

    def patched_stop():
        scheduler_instance.is_running = False
        original_stop()

    scheduler_instance.stop = patched_stop

    # 启动调度器（阻塞方法）
    try:
        scheduler_instance.run()
    except Exception as e:
        print(f"\n[调度器] 发生错误: {e}")
        import traceback
        traceback.print_exc()


def signal_handler(signum, frame):
    """处理信号，优雅关闭服务"""
    print("\n\n[主程序] 收到停止信号，正在关闭服务...")

    # 停止调度器
    if scheduler_instance:
        print("[主程序] 停止调度器...")
        scheduler_instance.stop()

    # 设置关闭事件
    shutdown_event.set()

    print("[主程序] 服务已停止")
    sys.exit(0)


def main():
    """主函数：启动调度器和API服务"""
    global scheduler_thread

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='基金估值系统统一启动脚本')
    parser.add_argument(
        '--interval',
        type=int,
        default=2,
        help='采集间隔（分钟），默认2分钟'
    )
    parser.add_argument(
        '--db',
        type=str,
        default='fund_estimation.db',
        help='数据库文件路径，默认fund_estimation.db'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='API服务监听地址，默认0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=50802,
        help='API服务端口，默认50802'
    )

    args = parser.parse_args()

    # 设置数据库路径的绝对路径
    if not os.path.isabs(args.db):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.db)
    else:
        db_path = args.db

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 打印启动信息
    print("\n" + "=" * 70)
    print(" ".center(70))
    print("基金估值系统统一启动".center(70))
    print(" ".center(70))
    print("=" * 70)
    print()
    print("【服务配置】")
    print(f"  数据采集间隔: {args.interval} 分钟")
    print(f"  数据库路径: {db_path}")
    print(f"  API服务地址: http://{args.host}:{args.port}")
    print()
    print("【启动顺序】")
    print("  1. 启动时立即采集（后台线程）")
    print("  2. 启动数据采集调度器（后台线程）")
    print("  3. 启动FastAPI服务（主线程）")
    print()
    print("【停止方法】")
    print("  按 Ctrl+C 停止所有服务")
    print()
    print("=" * 70)
    print()

    # 等待一下让用户看到启动信息
    time.sleep(1)

    # 启动立即采集线程（后台执行，不阻塞）
    print("[主程序] 正在启动立即采集...")
    initial_collection_thread = threading.Thread(
        target=run_initial_collection,
        args=(db_path,),
        daemon=True,
        name="InitialCollectionThread"
    )
    initial_collection_thread.start()

    # 启动调度器线程
    print("[主程序] 正在启动数据采集调度器...")
    scheduler_thread = threading.Thread(
        target=run_scheduler,
        args=(args.interval, db_path),
        daemon=True,  # 设置为守护线程，主线程退出时自动结束
        name="SchedulerThread"
    )
    scheduler_thread.start()

    # 等待一下确保调度器启动
    time.sleep(1)

    print("[主程序] 调度器已启动（后台线程）")
    print("[主程序] 正在启动FastAPI服务...")
    print()

    # 打印API服务访问信息
    print("=" * 70)
    print("API服务访问信息".center(70))
    print("=" * 70)
    print(f"  访问地址: http://localhost:{args.port}")
    print(f"  API文档: http://localhost:{args.port}/docs")
    print(f"  健康检查: http://localhost:{args.port}/api/health")
    print()
    print("API端点:")
    print(f"  - 健康检查: GET /api/health")
    print(f"  - 基金估值: GET /api/v1/fund/estimation?code=002474&date=20250302")
    print(f"  - 最新估值: GET /api/v1/fund/latest?limit=20")
    print(f"  - 基金列表: GET /api/v1/fund/list?limit=100")
    print(f"  - 系统统计: GET /api/v1/system/stats")
    print(f"  - 手动采集: POST /api/v1/admin/collect")
    print(f"  - 采集状态: GET /api/v1/admin/collect/status")
    print("=" * 70)
    print()

    # 启动API服务（主线程，阻塞）
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )
    except KeyboardInterrupt:
        # 用户按Ctrl+C，由signal_handler处理
        pass
    finally:
        # 确保调度器停止
        if scheduler_instance:
            scheduler_instance.stop()


if __name__ == "__main__":
    main()
