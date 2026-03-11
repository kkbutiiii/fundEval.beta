"""
基金列表缓存管理模块。
提供内存缓存、本地文件缓存和定时刷新功能。

优化策略：
1. 启动时优先从本地文件加载缓存（毫秒级响应）
2. 后台异步从AKShare更新数据
3. 更新完成后替换内存和本地缓存
4. 确保用户第一秒搜索到的数据就很快，后续数据自动更新
"""
import os
import json
import time
import threading
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app.models import FundInfo

# 本地缓存文件路径
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'fund_list_cache.json')
CACHE_METADATA_FILE = os.path.join(CACHE_DIR, 'fund_list_metadata.json')


class FundListCache:
    """
    基金列表缓存管理器。

    特性：
    - 启动时自动加载基金列表到内存
    - 支持手动刷新
    - 定时每天凌晨自动刷新
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._fund_list_df: Optional[pd.DataFrame] = None
        self._fund_list_dict: List[Dict] = []
        self._last_update: Optional[datetime] = None
        self._update_lock = threading.Lock()
        self._initialized = True
        self._is_updating = False  # 标记是否正在后台更新

        # 确保缓存目录存在
        os.makedirs(CACHE_DIR, exist_ok=True)

        # 启动时优先从本地文件加载（毫秒级），然后后台更新
        self._load_from_local_file()

        # 启动后台线程异步更新数据
        self._start_background_update()

    def _load_from_local_file(self) -> bool:
        """
        从本地文件加载基金列表缓存。
        启动时优先调用，实现毫秒级响应。

        Returns:
            bool: 是否成功加载
        """
        try:
            if not os.path.exists(CACHE_FILE):
                print(f"[{datetime.now()}] 本地缓存文件不存在，将从AKShare加载...")
                return self._load_fund_list()

            print(f"[{datetime.now()}] 正在从本地文件加载基金列表...")
            start_time = time.time()

            # 读取基金列表数据
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                fund_list = json.load(f)

            # 读取元数据
            metadata = {}
            if os.path.exists(CACHE_METADATA_FILE):
                with open(CACHE_METADATA_FILE, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            # 转换为DataFrame
            df = pd.DataFrame(fund_list)

            with self._update_lock:
                self._fund_list_df = df
                self._fund_list_dict = fund_list
                self._last_update = datetime.fromisoformat(metadata.get('last_update')) if metadata.get('last_update') else None

            elapsed = time.time() - start_time
            cache_age = (datetime.now() - self._last_update).total_seconds() / 3600 if self._last_update else None
            print(f"[{datetime.now()}] 本地缓存加载完成: {len(fund_list)} 只基金, 耗时 {elapsed:.3f}s, 缓存年龄: {cache_age:.1f}小时" if cache_age else f"[{datetime.now()}] 本地缓存加载完成: {len(fund_list)} 只基金, 耗时 {elapsed:.3f}s")
            return True

        except Exception as e:
            print(f"[{datetime.now()}] 从本地文件加载失败: {e}，将尝试从AKShare加载")
            return self._load_fund_list()

    def _save_to_local_file(self) -> bool:
        """
        保存基金列表到本地文件。

        Returns:
            bool: 是否成功保存
        """
        try:
            with self._update_lock:
                if not self._fund_list_dict:
                    return False

                # 保存基金列表
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._fund_list_dict, f, ensure_ascii=False, indent=2)

                # 保存元数据
                metadata = {
                    'last_update': self._last_update.isoformat() if self._last_update else None,
                    'total_funds': len(self._fund_list_dict)
                }
                with open(CACHE_METADATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

            print(f"[{datetime.now()}] 基金列表已保存到本地文件")
            return True
        except Exception as e:
            print(f"[{datetime.now()}] 保存本地文件失败: {e}")
            return False

    def _start_background_update(self):
        """
        启动后台线程异步更新基金列表。
        确保启动速度快，同时数据保持最新。
        """
        def update_task():
            try:
                self._is_updating = True
                print(f"[{datetime.now()}] 后台线程开始更新基金列表...")

                # 从AKShare加载最新数据
                success = self._load_fund_list()

                if success:
                    # 保存到本地文件
                    self._save_to_local_file()
                    print(f"[{datetime.now()}] 后台更新完成，内存和本地缓存已同步")
                else:
                    print(f"[{datetime.now()}] 后台更新失败，保留现有缓存")

            except Exception as e:
                print(f"[{datetime.now()}] 后台更新异常: {e}")
            finally:
                self._is_updating = False

        # 如果本地缓存较旧（超过24小时），立即启动后台更新
        cache_age_hours = (datetime.now() - self._last_update).total_seconds() / 3600 if self._last_update else float('inf')

        if cache_age_hours > 24 or not self._fund_list_dict:
            print(f"[{datetime.now()}] 缓存较旧({cache_age_hours:.1f}小时)，启动后台更新...")
            update_thread = threading.Thread(target=update_task, daemon=True)
            update_thread.start()
        else:
            print(f"[{datetime.now()}] 缓存较新({cache_age_hours:.1f}小时)，后台更新已跳过")

    def _load_fund_list(self) -> bool:
        """
        从 AKShare 加载基金列表。

        Returns:
            bool: 是否成功加载
        """
        try:
            print(f"[{datetime.now()}] 正在加载基金列表...")
            start_time = time.time()

            # 获取基金列表
            df = ak.fund_name_em()

            # 转换为字典列表便于快速搜索
            fund_list = []
            for _, row in df.iterrows():
                fund_list.append({
                    'fund_code': str(row["基金代码"]).zfill(6),
                    'fund_name': row["基金简称"],
                    'fund_type': row.get("基金类型", None),
                    'pinyin': row.get("拼音缩写", ""),
                    'pinyin_full': row.get("拼音全拼", "")
                })

            with self._update_lock:
                self._fund_list_df = df
                self._fund_list_dict = fund_list
                self._last_update = datetime.now()

            elapsed = time.time() - start_time
            print(f"[{datetime.now()}] 基金列表加载完成: {len(fund_list)} 只基金, 耗时 {elapsed:.2f}s")
            return True

        except Exception as e:
            print(f"[{datetime.now()}] 加载基金列表失败: {e}")
            return False

    def refresh(self) -> bool:
        """
        手动刷新基金列表。
        刷新后会自动保存到本地文件。

        Returns:
            bool: 是否成功刷新
        """
        success = self._load_fund_list()
        if success:
            self._save_to_local_file()
        return success

    def is_updating(self) -> bool:
        """
        检查是否正在后台更新。

        Returns:
            bool: 是否正在更新
        """
        return self._is_updating

    def get_cache_status(self) -> Dict:
        """
        获取缓存状态信息。

        Returns:
            Dict: 缓存状态
        """
        cache_age_hours = (datetime.now() - self._last_update).total_seconds() / 3600 if self._last_update else None

        # 检查本地文件是否存在
        local_cache_exists = os.path.exists(CACHE_FILE)
        local_cache_size = 0
        if local_cache_exists:
            local_cache_size = os.path.getsize(CACHE_FILE)

        return {
            'memory_cached_funds': len(self._fund_list_dict),
            'local_cache_exists': local_cache_exists,
            'local_cache_size_bytes': local_cache_size,
            'last_update': self._last_update.isoformat() if self._last_update else None,
            'cache_age_hours': cache_age_hours,
            'is_updating': self._is_updating
        }

    def get_fund_list(self) -> List[Dict]:
        """
        获取基金列表（字典形式）。

        Returns:
            List[Dict]: 基金列表
        """
        with self._update_lock:
            return self._fund_list_dict.copy()

    def get_fund_list_df(self) -> Optional[pd.DataFrame]:
        """
        获取基金列表（DataFrame形式）。

        Returns:
            Optional[pd.DataFrame]: 基金列表
        """
        with self._update_lock:
            return self._fund_list_df.copy() if self._fund_list_df is not None else None

    def search_funds(self, keyword: str, limit: int = 20) -> List[FundInfo]:
        """
        在内存中搜索基金。

        Args:
            keyword: 搜索关键词
            limit: 最大返回数量

        Returns:
            List[FundInfo]: 搜索结果
        """
        if not self._fund_list_dict:
            return []

        keyword_lower = keyword.lower()
        results = []

        for fund in self._fund_list_dict:
            # 搜索基金代码、名称、拼音
            if (keyword_lower in fund['fund_code'].lower() or
                keyword_lower in fund['fund_name'].lower() or
                keyword_lower in fund.get('pinyin', '').lower() or
                keyword_lower in fund.get('pinyin_full', '').lower()):
                results.append(FundInfo(
                    fund_code=fund['fund_code'],
                    fund_name=fund['fund_name'],
                    fund_type=fund['fund_type']
                ))
                if len(results) >= limit:
                    break

        return results

    def get_last_update_time(self) -> Optional[datetime]:
        """
        获取最后更新时间。

        Returns:
            Optional[datetime]: 最后更新时间
        """
        return self._last_update

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息（向后兼容）。

        Returns:
            Dict: 统计信息
        """
        return self.get_cache_status()


# 全局缓存实例
fund_list_cache = FundListCache()


def start_scheduler():
    """
    启动定时任务调度器，每天凌晨自动刷新基金列表。
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BackgroundScheduler()

    # 每天凌晨 00:00 刷新
    scheduler.add_job(
        fund_list_cache.refresh,
        trigger=CronTrigger(hour=0, minute=0),
        id='refresh_fund_list',
        name='刷新基金列表缓存',
        replace_existing=True
    )

    scheduler.start()
    print(f"[{datetime.now()}] 定时任务已启动: 每天 00:00 刷新基金列表")
    return scheduler
