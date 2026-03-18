# Changelog

## 2026-03-19

### 组合管理页面 - 收益率走势图最后一天计算逻辑修订（第2版）

#### 修改内容

1. **新增辅助函数 `get_estimation_date_label`**
   - 与前端逻辑保持一致
   - 根据估值时间判断应该显示的估值日期
   - 时间 < 09:30 → 昨天
   - 时间 >= 09:30 → 今天

2. **扩展 `PortfolioSummary` 模型**
   - 新增 `estimation_date`: 计算后的估值日期（YYYY-MM-DD格式）
   - 新增 `estimation_raw_date`: 估值服务返回的原始日期（YYYYMMDD格式）
   - 新增 `estimation_time`: 估值时间（HH:MM格式）

3. **更新 `get_portfolio_with_values` 方法**
   - 提取估值元数据并计算 `estimation_date`
   - 传递给 `PortfolioSummary`

4. **修订触发条件逻辑**
   - 新逻辑：
     - `nav_date` 是昨天 **且** `estimation_date` 是今天 → 添加估算（盘中，净值未更新）
     - `nav_date` 是今天 → 跳过估算（官方净值已更新）
     - `nav_date` 是昨天 **且** `estimation_date` 也是昨天 → 跳过估算（开盘前，属于昨天数据）

#### 验证场景

| 时间 | nav_date | estimation_date | 操作 |
|------|----------|-----------------|------|
| 03/19 08:00 (<09:30) | 03/18 | 03/18 | 跳过（昨天数据） |
| 03/19 10:00 (>=09:30) | 03/18 | 03/19 | 添加估算（盘中） |
| 03/19 15:00 (NAV已更新) | 03/19 | - | 跳过（使用官方净值） |

#### 相关文件

- `backend/app/services/portfolio_service.py`
- `backend/app/models/portfolio.py`

---

## 2026-03-18

### 组合管理页面 - 收益率走势图最后一天计算逻辑修订

#### 修改内容

1. **TWR收益率计算**
   - 原逻辑：`twr = round(simple_return, 4)` （使用简单收益率作为近似）
   - 新逻辑：`twr = ((1 + last_twr/100) * (1 + today_return) - 1) * 100`
     - `last_twr`: 前一天的TWR收益率
     - `today_return`: 今日估算收益率 = `(estimated_value - latest_value) / latest_value`

2. **触发条件**
   - 检查基金最新净值日期，判断是否需要添加估算数据
   - 如果所有基金的 `latest_nav_date` 都是昨天（或更早），则需要估算
   - 如果有基金的 `latest_nav_date` 是今天，则说明估值已更新，跳过估算

#### 相关文件

- `backend/app/services/portfolio_service.py`
