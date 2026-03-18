# Changelog

## 2026-03-19

### UI优化：页眉导航改造

#### 修改内容

1. **新增页面快捷导航**
   - 在页眉添加"基金组合管理"和"自选监控"两个导航链接
   - 当前所在页面的导航文字加粗显示（font-weight: 700）
   - 使用 React Router 的 Link 组件实现客户端导航

2. **新增基金搜索框**
   - 在页眉集成基金搜索功能
   - 支持按基金代码或名称搜索
   - 选择搜索结果后跳转到基金详情页面
   - 使用防抖技术优化搜索性能（300ms）

3. **响应式布局优化**
   - 移动端适配：搜索框宽度调整为 200px
   - 移动端隐藏品牌标题，节省空间
   - 导航链接字号和间距适配小屏幕

4. **样式优化**
   - 搜索框采用圆角设计（border-radius: 20px）
   - 玻璃态背景效果，与整体设计风格一致
   - 滚动时搜索框背景色自动调整

#### 相关文件

- `frontend/src/components/dashboard/DashboardLayout.tsx`
- `frontend/src/styles/unified-dashboard.css`

---


### UI优化：份额显示精度统一与添加基金交互改进

#### 修改内容

1. **份额显示精度统一为2位小数**
   - `PortfolioFundTable.tsx`: 当前份额列从4位改为2位小数
   - `FundDetailDrawer.tsx`: 当前份额显示从4位改为2位小数
   - `TransactionHistory.tsx`: 份额列和当前份额汇总从4位改为2位小数
   - 确认净值保持4位小数不变（净值需要更高精度）

2. **交易弹窗交互优化（添加基金/买入/卖出）**
   - 默认确认日期从"今天"改为"昨天"（基金交易T+1确认）
   - 选择日期时自动填充该日期的净值
   - 如果所选日期没有净值数据（非交易日），显示警告提示
   - 添加基金弹窗：选择基金时也会根据已选日期自动填充净值

#### 相关文件

- `frontend/src/components/portfolio/PortfolioFundTable.tsx`
- `frontend/src/components/portfolio/FundDetailDrawer.tsx`
- `frontend/src/components/portfolio/TransactionHistory.tsx`
- `frontend/src/components/portfolio/AddFundModal.tsx`
- `frontend/src/components/portfolio/TransactionModal.tsx`

---

### 修复：延长净值历史查询时间范围

#### 修改内容

1. **AddFundModal.tsx**
   - 两处查询范围从 `'3m'` 改为 `'1y'`
   - 支持查询1年内的历史净值数据

2. **TransactionModal.tsx**
   - 查询范围从 `'3m'` 改为 `'1y'`
   - 支持买入/卖出时选择更久远的交易日期

#### 问题修复

- 解决选择6个月前的日期时提示"不是交易日"的问题
- 原因为3个月缓存无法覆盖用户的早期交易记录

#### 相关文件

- `frontend/src/components/portfolio/AddFundModal.tsx`
- `frontend/src/components/portfolio/TransactionModal.tsx`

---

### 前端图表组件重构：改为受控组件模式

#### 修改内容

1. **PortfolioValueChart 组件重构**
   - 从自管理数据改为受控组件模式
   - 通过 props 接收 `data`, `loading`, `period`, `onPeriodChange`, `onRefresh`
   - 数据获取逻辑上移至父组件，便于统一管理和缓存

2. **PortfolioReturnChart 组件重构**
   - 从自管理数据改为受控组件模式
   - 通过 props 接收 `data`, `loading`, `period`, `calculationMethod`, `onPeriodChange`, `onCalculationMethodChange`, `onRefresh`
   - 移除内部状态管理，统一由父组件控制

3. **布局优化**
   - 调整图表 grid 布局，右侧边距从 12% 改为 3%，保持左右对称

#### 相关文件

- `frontend/src/components/portfolio/PortfolioValueChart.tsx`
- `frontend/src/components/portfolio/PortfolioReturnChart.tsx`

---

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
