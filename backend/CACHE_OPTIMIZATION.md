# FOF图表缓存优化方案

本文档介绍系统中的多级缓存策略，包括基金列表缓存和FOF收益率缓存。

---

# 一、基金列表缓存优化

## 优化目标
解决基金搜索 API 响应慢的问题（原 6-8 秒 → 目标 < 100ms）

## 优化方案

### 1. 架构改进
- **原方案**: 每次搜索都调用 `ak.fund_name_em()` 从东方财富获取完整基金列表
- **新方案**: 启动时加载基金列表到内存，搜索时直接内存过滤

### 2. 核心组件

#### FundListCache（基金列表缓存管理器）
文件: `app/utils/fund_list_cache.py`

特性：
- 单例模式，全局共享缓存
- 启动时自动加载基金列表
- 支持拼音搜索（基金代码、名称、拼音缩写、全拼）
- 线程安全（使用锁保护）

#### 定时刷新机制
使用 APScheduler 实现：
- 每天凌晨 00:00 自动刷新基金列表
- 支持手动刷新（管理接口）

### 3. 性能对比

| 指标 | 优化前 | 优化后 | 提升倍数 |
|------|--------|--------|----------|
| 首次搜索 | 6-8 秒 | 9.7 秒（一次性） | - |
| 后续搜索 | 6-8 秒 | 10-13 毫秒 | **600-800x** |
| 限制5个结果 | 6-8 秒 | 0.12 毫秒 | **50000x** |
| 内存占用 | 低 | ~20MB（26k条基金） | - |

### 4. API 变更

#### 新增管理接口

**获取缓存统计信息**
```
GET /api/v1/funds/admin/cache-stats
```
响应：
```json
{
  "total_funds": 26135,
  "last_update": "2026-02-26T13:15:58.846598",
  "cache_age_hours": 0.5
}
```

**手动刷新缓存**
```
POST /api/v1/funds/admin/refresh-cache
```
响应：
```json
{
  "success": true,
  "message": "基金列表缓存刷新成功",
  "stats": { ... }
}
```

### 5. 代码改动

#### 修改文件
1. `requirements.txt` - 添加 `apscheduler==3.11.0`
2. `app/utils/fund_list_cache.py` - 新增（缓存管理器）
3. `app/services/fund_service.py` - 使用新缓存
4. `app/main.py` - 启动时加载缓存和定时任务
5. `app/routers/funds.py` - 添加管理接口

### 6. 部署说明

#### 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 重启服务
```bash
# 停止现有服务
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# 启动服务
python -m app.main
```

### 7. 监控和维护

#### 日志输出
```
[2026-02-26 13:07:02] 正在加载基金列表...
[2026-02-26 13:07:10] 基金列表加载完成: 26135 只基金, 耗时 8.43s
[2026-02-26 13:07:10] 定时任务已启动: 每天 00:00 刷新基金列表
```

#### 健康检查
- 缓存状态: `GET /api/v1/funds/admin/cache-stats`
- 服务健康: `GET /health`

### 8. 注意事项

1. **内存占用**: 缓存约占用 20MB 内存（26,000 只基金）
2. **数据新鲜度**: 基金列表每天凌晨自动更新，新上市基金次日可见
3. **故障恢复**: 服务重启会自动重新加载缓存
4. **手动刷新**: 如需立即更新，可调用 `POST /api/v1/funds/admin/refresh-cache`

## 总结
通过内存缓存和定时刷新机制，基金搜索速度从 6-8 秒提升到 10 毫秒以内，提升了 600 倍以上，显著改善用户体验。

---

# 二、FOF收益率缓存优化

## 优化目标

解决组合历史收益率计算的性能问题：
- **优化前**: 每次请求都实时计算，30天 × 10只基金 = 300次API调用
- **优化后**: 使用双层缓存，增量更新，仅需 0-10次API调用

## 架构设计

### 双层缓存策略

```
获取组合历史数据
    │
    ├─→ 1. 检查 portfolio_return_cache ──→ 直接返回缓存数据
    │      缓存命中 ✅
    │      未命中 ↓
    ├─→ 2. 检查 fund_nav_cache ──────────→ 避免重复查询API
    │      部分命中 ↓
    └─→ 3. 调用 Wind API 获取净值 ───────→ 计算后保存到缓存
```

### 缓存表结构

#### 1. 基金净值缓存表 (fund_nav_cache)

```sql
CREATE TABLE fund_nav_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    nav DECIMAL(10, 4),                    -- 单位净值
    is_estimated BOOLEAN DEFAULT 0,        -- 是否使用往前查找的净值
    actual_date DATE,                      -- 实际净值日期（用于估算）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fund_code, date)
);
```

**特点：**
- 全系统共享缓存
- 避免同一基金在不同组合中重复查询
- 自动处理周末/节假日净值缺失

#### 2. FOF收益曲线缓存表 (portfolio_return_cache)

```sql
CREATE TABLE portfolio_return_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_value DECIMAL(15, 2),            -- 总市值
    total_cost DECIMAL(15, 2),             -- 总成本
    total_profit DECIMAL(15, 2),           -- 总收益
    daily_profit DECIMAL(15, 2),           -- 当日收益额
    return_rate DECIMAL(10, 4),            -- 简单收益率(%)
    twr DECIMAL(10, 4),                    -- 时间加权收益率(%)
    xirr DECIMAL(10, 4),                   -- 资金加权收益率(%)
    is_estimated BOOLEAN DEFAULT 0,        -- 是否使用了估算净值
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, date)
);
```

**特点：**
- 每个组合单独缓存
- 缓存已计算好的每日收益数据
- 支持三种收益率指标

## 核心实现

### 1. 增量更新机制

```python
async def get_portfolio_history(db, portfolio_id, period='30d', use_cache=True):
    # 1. 获取缓存数据
    cached_data = await get_cached_portfolio_returns(portfolio_id, start_date, end_date)

    # 2. 找出缺失日期
    cached_dates = {item['date'] for item in cached_data}
    missing_dates = [d for d in all_dates if d not in cached_dates]

    # 3. 只计算缺失日期
    if missing_dates:
        new_data = await calculate_for_dates(portfolio_id, missing_dates)
        await save_to_cache(portfolio_id, new_data)

    # 4. 合并返回
    return cached_data + new_data
```

### 2. 基金净值获取（带缓存）

```python
async def _get_nav_for_date_safe(db, fund_code, date):
    # 1. 优先从缓存获取
    cached = await _get_cached_nav(db, fund_code, date)
    if cached:
        return cached

    # 2. 从 Wind API 获取
    nav = await wind_client.get_nav(fund_code, date)

    # 3. 保存到缓存
    await _save_nav_to_cache(db, fund_code, date, nav)
    return nav
```

### 3. 缓存失效机制

```python
async def invalidate_portfolio_cache(db, portfolio_id, from_date=None):
    """当录入新交易时，从交易日期开始失效缓存"""
    await delete(PortfolioReturnCacheDB).where(
        PortfolioReturnCacheDB.portfolio_id == portfolio_id,
        PortfolioReturnCacheDB.date >= from_date
    )
```

**失效场景：**
- 录入新交易时自动失效
- 删除交易时自动失效
- 支持手动刷新

### 4. 周末/节假日处理

```python
async def _get_nav_for_date_safe(db, fund_code, date):
    # 尝试获取当日净值
    nav = await get_nav(fund_code, date)
    if nav:
        return {'nav': nav, 'is_estimated': False}

    # 向前查找最近交易日（最多10天）
    for i in range(1, 10):
        prev_date = date - timedelta(days=i)
        nav = await get_nav(fund_code, prev_date)
        if nav:
            return {
                'nav': nav,
                'is_estimated': True,
                'actual_date': prev_date
            }
```

**处理逻辑：**
- 周末/节假日使用最近交易日净值
- 标记 `is_estimated = true`
- 前端用半透明/虚线标注估算数据

## 性能对比

### 缓存命中率测试

| 场景 | 缓存命中 | API调用 | 响应时间 |
|------|----------|---------|----------|
| 首次加载 | 0% | 30-300次 | 15-30s |
| 重复查询 | 100% | 0次 | ~50ms |
| 新增1天 | 97% | 10次 | ~500ms |
| 切换周期(30d→60d) | 50% | 30次 | ~2s |

### 优化效果

| 指标 | 优化前 | 优化后 | 提升倍数 |
|------|--------|--------|----------|
| API调用次数 | 300次/请求 | 0-10次/请求 | **30x+** |
| 数据查询 | 实时计算 | 缓存读取 | **10x+** |
| 周末数据 | 断点/缺失 | 自动估算 | 连续显示 |
| 多组合共享 | 重复查询 | 共享净值缓存 | 节省N倍 |

## 代码位置

| 文件 | 说明 |
|------|------|
| `app/services/portfolio_service.py` | 主服务，集成缓存逻辑 |
| `app/db_models/fund_nav_cache.py` | 基金净值缓存模型 |
| `app/db_models/portfolio_return_cache.py` | FOF收益曲线缓存模型 |

## 监控和维护

### 日志输出

```
[Cache Hit] Portfolio portfolio_xxx: 30 days cached
[Cache Miss] Portfolio portfolio_xxx: 1 days need calculation
[Cache Saved] Portfolio portfolio_xxx: 1 days saved to cache
[NAV Fallback] 000001 on 2026-03-15: using NAV from 2026-03-14
```

### 缓存统计接口

```bash
# 查看基金净值缓存统计
curl "http://localhost:50801/api/v1/funds/admin/cache-stats"

# 手动刷新（会触发重新计算）
curl -X POST "http://localhost:50801/api/v1/portfolios/portfolio_xxx/refresh-history"
```

## 注意事项

1. **缓存一致性**: 交易录入时会自动失效相关缓存
2. **数据新鲜度**: 每天收盘后更新当日数据
3. **存储空间**: 每只基金每年约占用 365 × 记录大小
4. **故障恢复**: 缓存失效时会自动重新计算

## 总结

通过双层缓存策略（基金净值缓存 + FOF收益曲线缓存）：
- API调用次数减少 **30倍以上**
- 响应时间从秒级降至 **毫秒级**
- 支持增量更新，节省计算资源
- 自动处理周末/节假日数据缺失
