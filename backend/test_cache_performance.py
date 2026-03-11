"""
测试基金列表缓存性能。
"""
import time
import sys
sys.path.insert(0, 'C:\\Users\\11639\\Documents\\trae_projects\\fundEval\\backend')

from app.utils.fund_list_cache import fund_list_cache


def test_cache_performance():
    """测试缓存性能。"""
    print("=== 基金列表缓存性能测试 ===\n")

    # 1. 测试缓存状态
    print("1. 缓存状态:")
    stats = fund_list_cache.get_stats()
    print(f"   基金总数: {stats['total_funds']}")
    print(f"   最后更新: {stats['last_update']}")
    print(f"   缓存时长: {stats['cache_age_hours']:.6f} 小时\n")

    # 2. 测试搜索速度
    print("2. 搜索速度测试 (100次搜索取平均):")
    test_cases = [
        ('002474', '基金代码搜索'),
        ('中邮睿信', '中文名称搜索'),
        ('华商均衡', '中文名称搜索'),
        ('000001', '热门基金搜索'),
    ]

    for keyword, desc in test_cases:
        # 预热
        fund_list_cache.search_funds(keyword, 20)

        # 正式测试
        times = []
        for _ in range(100):
            start = time.time()
            results = fund_list_cache.search_funds(keyword, 20)
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times) * 1000
        min_time = min(times) * 1000
        max_time = max(times) * 1000

        print(f"   {desc} '{keyword}':")
        print(f"     平均: {avg_time:.3f}ms, 最小: {min_time:.3f}ms, 最大: {max_time:.3f}ms, 结果: {len(results)}个")

    print("\n3. 不同结果数量测试:")
    limits = [5, 10, 20, 50, 100]
    for limit in limits:
        times = []
        for _ in range(100):
            start = time.time()
            results = fund_list_cache.search_funds('中邮', limit)
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = sum(times) / len(times) * 1000
        print(f"   限制 {limit} 个结果: 平均 {avg_time:.3f}ms")

    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_cache_performance()
