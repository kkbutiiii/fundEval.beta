# -*- coding: utf-8 -*-
"""
天天基金(TTJJ) API测试脚本
用于测试新接口的速度和数据完整性
并与现有Wind/AKShare数据进行对比
"""
import time
import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 设置编码（兼容Windows）
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
sys.path.insert(0, 'C:\\Users\\11639\\Documents\\trae_projects\\fundEval\\backend')

from app.services.ttjj_client import ttjj_client
from app.services.wind_client import wind_client
import akshare as ak


class APITester:
    """API测试器"""

    def __init__(self):
        self.results = []

    def print_header(self, title: str):
        """打印测试标题"""
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)

    def print_result(self, name: str, success: bool, duration: float, data_count: int = 0, details: str = ""):
        """打印测试结果"""
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}")
        print(f"         耗时: {duration:.3f}s")
        if data_count > 0:
            print(f"         数据条数: {data_count}")
        if details:
            print(f"         详情: {details}")

    def test_ttjj_stock_holdings(self, fund_code: str = "002474") -> Dict[str, Any]:
        """测试天天基金股票持仓接口"""
        self.print_header(f"测试天天基金股票持仓接口 - 基金: {fund_code}")

        start_time = time.time()
        try:
            holdings, report_date = ttjj_client.get_stock_holdings(fund_code)
            duration = time.time() - start_time

            success = len(holdings) > 0
            details = f"报告期: {report_date}, 持仓数量: {len(holdings)}"
            if holdings:
                details += f", 第一重仓: {holdings[0].stock_name}({holdings[0].stock_code}) - {holdings[0].ratio}%"

            self.print_result("TTJJ股票持仓", success, duration, len(holdings), details)

            return {
                "source": "TTJJ",
                "type": "stock_holdings",
                "success": success,
                "duration": duration,
                "data_count": len(holdings),
                "report_date": report_date,
                "holdings": holdings[:5]  # 只保存前5条用于对比
            }
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("TTJJ股票持仓", False, duration, details=f"错误: {str(e)}")
            return {
                "source": "TTJJ",
                "type": "stock_holdings",
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    def test_akshare_stock_holdings(self, fund_code: str = "002474") -> Dict[str, Any]:
        """测试AKShare股票持仓接口"""
        print(f"\n  对比测试 - AKShare股票持仓接口...")

        start_time = time.time()
        try:
            df = ak.fund_portfolio_hold_em(symbol=fund_code, date=str(datetime.now().year))
            duration = time.time() - start_time

            if not df.empty and "季度" in df.columns:
                latest_quarter = df["季度"].iloc[0]
                df = df[df["季度"] == latest_quarter]

            success = not df.empty
            details = f"数据条数: {len(df)}"
            if not df.empty:
                first_row = df.iloc[0]
                details += f", 第一重仓: {first_row.get('股票名称', 'N/A')}({first_row.get('股票代码', 'N/A')})"

            self.print_result("AKShare股票持仓", success, duration, len(df), details)

            return {
                "source": "AKShare",
                "type": "stock_holdings",
                "success": success,
                "duration": duration,
                "data_count": len(df)
            }
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("AKShare股票持仓", False, duration, details=f"错误: {str(e)}")
            return {
                "source": "AKShare",
                "type": "stock_holdings",
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    def test_ttjj_bond_holdings(self, fund_code: str = "002474") -> Dict[str, Any]:
        """测试天天基金债券持仓接口"""
        self.print_header(f"测试天天基金债券持仓接口 - 基金: {fund_code}")

        start_time = time.time()
        try:
            regular_bonds, convertible_bonds, report_date = ttjj_client.get_bond_holdings(fund_code)
            duration = time.time() - start_time

            total_bonds = len(regular_bonds) + len(convertible_bonds)
            success = total_bonds > 0
            details = f"报告期: {report_date}, 普通债券: {len(regular_bonds)}, 可转债: {len(convertible_bonds)}"

            if convertible_bonds:
                details += f", 可转债示例: {convertible_bonds[0].bond_name}"

            self.print_result("TTJJ债券持仓", success, duration, total_bonds, details)

            # 显示前3条可转债
            if convertible_bonds:
                print(f"\n         可转债持仓示例:")
                for cb in convertible_bonds[:3]:
                    print(f"           - {cb.bond_name}({cb.bond_code}): {cb.ratio}%")

            return {
                "source": "TTJJ",
                "type": "bond_holdings",
                "success": success,
                "duration": duration,
                "regular_count": len(regular_bonds),
                "convertible_count": len(convertible_bonds),
                "report_date": report_date,
                "convertible_bonds": convertible_bonds[:3]
            }
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("TTJJ债券持仓", False, duration, details=f"错误: {str(e)}")
            return {
                "source": "TTJJ",
                "type": "bond_holdings",
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    def test_wind_bond_holdings(self, fund_code: str = "002474") -> Dict[str, Any]:
        """测试Wind债券持仓接口（对比用）"""
        print(f"\n  对比测试 - Wind债券持仓接口...")

        start_time = time.time()
        try:
            regular, convertibles = wind_client.get_all_holdings(fund_code)
            duration = time.time() - start_time

            total = len(regular) + len(convertibles)
            success = total > 0
            details = f"普通债券: {len(regular)}, 可转债: {len(convertibles)}"

            self.print_result("Wind债券持仓", success, duration, total, details)

            return {
                "source": "Wind",
                "type": "bond_holdings",
                "success": success,
                "duration": duration,
                "regular_count": len(regular),
                "convertible_count": len(convertibles)
            }
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("Wind债券持仓", False, duration, details=f"错误: {str(e)}")
            return {
                "source": "Wind",
                "type": "bond_holdings",
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    def test_ttjj_asset_allocation(self, fund_code: str = "002474") -> Dict[str, Any]:
        """测试天天基金资产配置接口"""
        self.print_header(f"测试天天基金资产配置接口 - 基金: {fund_code}")

        start_time = time.time()
        try:
            allocations = ttjj_client.get_asset_allocation(fund_code, quarters=8)
            duration = time.time() - start_time

            success = len(allocations) > 0
            details = f"数据期数: {len(allocations)}"
            if allocations:
                latest = allocations[0]
                details += f", 最新: {latest.report_date} - 股票{latest.stock_ratio}% 债券{latest.bond_ratio}%"

            self.print_result("TTJJ资产配置", success, duration, len(allocations), details)

            # 显示最近3期
            if allocations:
                print(f"\n         最近3期资产配置:")
                for a in allocations[:3]:
                    print(f"           {a.report_date}: 股票{a.stock_ratio:.2f}% 债券{a.bond_ratio:.2f}% 现金{a.cash_ratio:.2f}% 净资产{a.net_asset:.2f}亿")

            return {
                "source": "TTJJ",
                "type": "asset_allocation",
                "success": success,
                "duration": duration,
                "data_count": len(allocations),
                "latest_allocation": allocations[0] if allocations else None
            }
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("TTJJ资产配置", False, duration, details=f"错误: {str(e)}")
            return {
                "source": "TTJJ",
                "type": "asset_allocation",
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    def test_wind_asset_allocation(self, fund_code: str = "002474") -> Dict[str, Any]:
        """测试Wind资产配置接口（对比用）"""
        print(f"\n  对比测试 - Wind资产配置接口...")

        start_time = time.time()
        try:
            allocations = wind_client.get_asset_allocation_history(fund_code, quarters=8)
            duration = time.time() - start_time

            # 注意：wind_client已经被修改为优先使用TTJJ，所以这里可能实际测试的是TTJJ
            success = len(allocations) > 0
            details = f"数据期数: {len(allocations)}"
            if allocations:
                latest = allocations[0]
                details += f", 最新: {latest.report_date} - 股票{latest.stock_ratio:.2f}%"

            self.print_result("Wind/集成资产配置", success, duration, len(allocations), details)

            return {
                "source": "Wind/Integrated",
                "type": "asset_allocation",
                "success": success,
                "duration": duration,
                "data_count": len(allocations)
            }
        except Exception as e:
            duration = time.time() - start_time
            self.print_result("Wind资产配置", False, duration, details=f"错误: {str(e)}")
            return {
                "source": "Wind",
                "type": "asset_allocation",
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    def run_comparison(self, fund_code: str = "002474"):
        """运行对比测试"""
        self.print_header(f"开始对比测试 - 基金代码: {fund_code}")
        print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        results = []

        # 测试股票持仓
        ttjj_stock = self.test_ttjj_stock_holdings(fund_code)
        ak_stock = self.test_akshare_stock_holdings(fund_code)
        results.extend([ttjj_stock, ak_stock])

        # 测试债券持仓
        ttjj_bond = self.test_ttjj_bond_holdings(fund_code)
        wind_bond = self.test_wind_bond_holdings(fund_code)
        results.extend([ttjj_bond, wind_bond])

        # 测试资产配置
        ttjj_alloc = self.test_ttjj_asset_allocation(fund_code)
        wind_alloc = self.test_wind_asset_allocation(fund_code)
        results.extend([ttjj_alloc, wind_alloc])

        # 打印总结
        self.print_summary(results, fund_code)

        return results

    def print_summary(self, results: List[Dict], fund_code: str):
        """打印测试总结"""
        self.print_header(f"测试总结 - 基金: {fund_code}")

        # 按类型分组
        by_type = {}
        for r in results:
            t = r.get("type", "unknown")
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(r)

        print("\n  按接口类型统计:")
        print("  " + "-" * 76)

        for type_name, type_results in by_type.items():
            print(f"\n  {type_name}:")
            for r in type_results:
                source = r.get("source", "Unknown")
                success = "✓" if r.get("success") else "✗"
                duration = r.get("duration", 0)
                count = r.get("data_count", r.get("regular_count", 0)) + r.get("convertible_count", 0)
                print(f"    {success} {source:20s} 耗时: {duration:6.3f}s  数据: {count:3d}条")

        print("\n  " + "-" * 76)

        # 计算性能提升
        print("\n  性能对比:")
        if "stock_holdings" in by_type:
            stock_results = {r["source"]: r for r in by_type["stock_holdings"]}
            if "TTJJ" in stock_results and "AKShare" in stock_results:
                ttjj_time = stock_results["TTJJ"]["duration"]
                ak_time = stock_results["AKShare"]["duration"]
                improvement = (ak_time - ttjj_time) / ak_time * 100 if ak_time > 0 else 0
                print(f"    股票持仓: TTJJ vs AKShare - {'快' if improvement > 0 else '慢'} {abs(improvement):.1f}%")

        if "bond_holdings" in by_type:
            bond_results = {r["source"]: r for r in by_type["bond_holdings"]}
            if "TTJJ" in bond_results and "Wind" in bond_results:
                ttjj_time = bond_results["TTJJ"]["duration"]
                wind_time = bond_results["Wind"]["duration"]
                improvement = (wind_time - ttjj_time) / wind_time * 100 if wind_time > 0 else 0
                print(f"    债券持仓: TTJJ vs Wind - {'快' if improvement > 0 else '慢'} {abs(improvement):.1f}%")

        # 总体统计
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get("success"))
        total_time = sum(r.get("duration", 0) for r in results)

        print("\n  总体统计:")
        print(f"    总测试数: {total_tests}")
        print(f"    通过数: {passed_tests}")
        print(f"    失败数: {total_tests - passed_tests}")
        print(f"    总耗时: {total_time:.3f}s")
        print(f"    平均耗时: {total_time/total_tests:.3f}s" if total_tests > 0 else "    平均耗时: N/A")


def test_multiple_funds():
    """测试多只基金"""
    tester = APITester()

    # 测试基金列表
    test_funds = [
        "002474",   # 测试基金
        "000001",   # 华夏成长
        "110022",   # 易方达消费行业
        "161725",   # 招商白酒
    ]

    print("\n" + "#" * 80)
    print("#" + " " * 78 + "#")
    print("#" + "  天天基金API测试脚本".center(74) + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)

    all_results = []
    for fund_code in test_funds:
        try:
            results = tester.run_comparison(fund_code)
            all_results.extend(results)
        except Exception as e:
            print(f"\n  测试基金 {fund_code} 时出错: {e}")

    # 最终总结
    tester.print_header("最终总结")
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.get("success"))
    total_time = sum(r.get("duration", 0) for r in all_results)

    print(f"\n  测试基金数量: {len(test_funds)}")
    print(f"  总API调用次数: {total_tests}")
    print(f"  成功次数: {passed_tests}")
    print(f"  失败次数: {total_tests - passed_tests}")
    print(f"  成功率: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "  成功率: N/A")
    print(f"  总耗时: {total_time:.3f}s")
    print(f"  平均每次调用耗时: {total_time/total_tests:.3f}s" if total_tests > 0 else "  平均每次调用耗时: N/A")

    print("\n" + "#" * 80)
    print("#  测试完成")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    test_multiple_funds()
