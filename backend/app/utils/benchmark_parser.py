"""
Benchmark parser for fund performance comparison benchmarks.
Parses benchmark strings like "沪深300指数×80%+中证全债指数×20%"
to extract indices and weights for smart completion.
"""
import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class BenchmarkComponents:
    """Parsed benchmark components."""
    stock_index_code: Optional[str] = None
    stock_index_name: Optional[str] = None
    stock_weight: float = 0.0
    bond_index_code: Optional[str] = None
    bond_index_name: Optional[str] = None
    bond_weight: float = 0.0
    convertible_index_code: Optional[str] = None
    convertible_index_name: Optional[str] = None
    convertible_weight: float = 0.0
    cash_weight: float = 0.0


# Index name to code mapping
INDEX_MAPPING = {
    # Stock indices
    "沪深300": {"code": "000300.SH", "type": "stock"},
    "中证500": {"code": "000905.SH", "type": "stock"},
    "中证800": {"code": "000906.SH", "type": "stock"},
    "上证指数": {"code": "000001.SH", "type": "stock"},
    "深证成指": {"code": "399001.SZ", "type": "stock"},
    "创业板指": {"code": "399006.SZ", "type": "stock"},
    "科创50": {"code": "000688.SH", "type": "stock"},
    "中证1000": {"code": "000852.SH", "type": "stock"},
    "上证50": {"code": "000016.SH", "type": "stock"},
    "深证100": {"code": "399330.SZ", "type": "stock"},
    "中小板指": {"code": "399005.SZ", "type": "stock"},

    # Bond indices
    "中证全债": {"code": "H11001.CSI", "type": "bond"},
    "中债总指数": {"code": "CBA00301.CS", "type": "bond"},
    "中债国债": {"code": "CBA00601.CS", "type": "bond"},
    "中债信用债": {"code": "CBA02701.CS", "type": "bond"},
    "中证国债": {"code": "H11006.CSI", "type": "bond"},
    "中证企业债": {"code": "H11008.CSI", "type": "bond"},

    # 中债综合财富指数系列 (ChinaBond Aggregate Wealth Index)
    "中债综合": {"code": "CBA00101.CS", "type": "bond"},
    "中债综合财富": {"code": "CBA00101.CS", "type": "bond"},
    "中债综合财富指数": {"code": "CBA00101.CS", "type": "bond"},
    "中债综合指数": {"code": "CBA00101.CS", "type": "bond"},

    # Convertible bond indices
    "中证转债": {"code": "000832.SH", "type": "convertible"},
    "上证转债": {"code": "000139.SH", "type": "convertible"},
    "深证转债": {"code": "399307.SZ", "type": "convertible"},

    # International indices
    "标普500": {"code": "SPX.GI", "type": "stock"},
    "纳斯达克100": {"code": "NDX.GI", "type": "stock"},
    "恒生指数": {"code": "HSI.HI", "type": "stock"},
    "恒生国企": {"code": "HSCEI.HI", "type": "stock"},
    "恒生科技": {"code": "HSTECH.HI", "type": "stock"},
}


def normalize_index_name(name: str) -> str:
    """Normalize index name for matching."""
    # Remove common suffixes and prefixes
    name = name.strip()
    name = re.sub(r'(指数|收益率|指数收益率|总指数)$', '', name)
    name = re.sub(r'^中证', '', name)
    return name


def find_index_code(index_name: str) -> Optional[Tuple[str, str]]:
    """
    Find index code and type by name.

    Args:
        index_name: Index name from benchmark string

    Returns:
        Tuple of (code, type) or None if not found
    """
    normalized = normalize_index_name(index_name)

    # Direct match
    for name, info in INDEX_MAPPING.items():
        if name in index_name or index_name in name:
            return info["code"], info["type"]
        if normalized in name or name in normalized:
            return info["code"], info["type"]

    # Fuzzy match for common patterns
    if any(kw in index_name for kw in ["沪深300", "hs300", "HS300"]):
        return INDEX_MAPPING["沪深300"]["code"], "stock"
    if any(kw in index_name for kw in ["中证500", "zz500"]):
        return INDEX_MAPPING["中证500"]["code"], "stock"
    if any(kw in index_name for kw in ["中债综合", "中债财富", "综合财富"]):
        return INDEX_MAPPING["中债综合财富指数"]["code"], "bond"
    if any(kw in index_name for kw in ["中证全债", "债券", "国债"]):
        return INDEX_MAPPING["中证全债"]["code"], "bond"
    if any(kw in index_name for kw in ["中证转债", "可转债", "转债"]):
        return INDEX_MAPPING["中证转债"]["code"], "convertible"
    if any(kw in index_name for kw in ["上证", "沪指"]):
        return INDEX_MAPPING["上证指数"]["code"], "stock"
    if any(kw in index_name for kw in ["恒生"]):
        return INDEX_MAPPING["恒生指数"]["code"], "stock"
    if any(kw in index_name for kw in ["标普", "S&P", "SPX"]):
        return INDEX_MAPPING["标普500"]["code"], "stock"

    return None


def parse_benchmark(benchmark_str: Optional[str]) -> BenchmarkComponents:
    """
    Parse benchmark string into components.

    Args:
        benchmark_str: Benchmark string like "沪深300指数×80%+中证全债指数×20%"

    Returns:
        BenchmarkComponents with parsed indices and weights
    """
    if not benchmark_str:
        return BenchmarkComponents()

    components = BenchmarkComponents()

    # Remove spaces and standardize separators
    benchmark_str = benchmark_str.strip()

    # Pattern to match index name + weight
    # Examples:
    #   沪深300指数×80%
    #   中证全债指数*20%
    #   沪深300指数*80%+中证全债指数*20%

    # Split by + or ＋
    parts = re.split(r'[\+＋]', benchmark_str)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Extract weight
        weight_match = re.search(r'[×\*×xX](\d+(?:\.\d+)?)\s*%', part)
        if weight_match:
            weight = float(weight_match.group(1))
        else:
            weight = 0

        # Extract index name (everything before weight)
        index_part = re.split(r'[×\*×xX]', part)[0].strip()

        # Find index code
        index_info = find_index_code(index_part)

        if index_info:
            code, index_type = index_info
            if index_type == "stock":
                components.stock_index_code = code
                components.stock_index_name = index_part
                components.stock_weight = weight
            elif index_type == "bond":
                components.bond_index_code = code
                components.bond_index_name = index_part
                components.bond_weight = weight
            elif index_type == "convertible":
                components.convertible_index_code = code
                components.convertible_index_name = index_part
                components.convertible_weight = weight

    # Calculate cash weight (remaining)
    total_weight = (components.stock_weight + components.bond_weight +
                   components.convertible_weight)
    components.cash_weight = max(0, 100 - total_weight)

    return components


def get_default_benchmark() -> BenchmarkComponents:
    """Get default benchmark components (CSI 300)."""
    return BenchmarkComponents(
        stock_index_code="000300.SH",
        stock_index_name="沪深300",
        stock_weight=80.0,
        bond_index_code="H11001.CSI",
        bond_index_name="中证全债",
        bond_weight=20.0,
        cash_weight=0.0
    )


def format_benchmark_for_display(components: BenchmarkComponents) -> str:
    """Format benchmark components for display."""
    parts = []

    if components.stock_index_name and components.stock_weight > 0:
        parts.append(f"{components.stock_index_name}×{components.stock_weight}%")

    if components.bond_index_name and components.bond_weight > 0:
        parts.append(f"{components.bond_index_name}×{components.bond_weight}%")

    if components.convertible_index_name and components.convertible_weight > 0:
        parts.append(f"{components.convertible_index_name}×{components.convertible_weight}%")

    if components.cash_weight > 0:
        parts.append(f"现金×{components.cash_weight}%")

    return " + ".join(parts) if parts else "未配置基准"
