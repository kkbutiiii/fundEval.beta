# FundEval Beta - 统一基金估值平台

## 项目概述

FundEval Beta 是将两个独立运行的基金估值项目合并后的统一平台：
- **fundEval**: 主应用（前端 50888 + 后端 50801）
- **fund_estimation_system**: 估值数据采集服务（50802）

当前问题：需要分别启动两个脚本，占用两个后端端口。

目标：创建一个统一启动脚本，一键启动三个服务，保留 fundEval 原有端口配置。

## 目录结构

```
C:\Users\11639\Documents\trae_projects\0311-FundEval.Beta
├── backend/                    # fundEval 主后端 (端口 50801)
│   ├── app/                    # FastAPI 应用
│   │   ├── db_models/          # 数据库模型
│   │   │   ├── user.py                # 用户表模型 ⭐新增
│   │   │   ├── watchlist.py           # 自选基金表模型 ⭐新增
│   │   │   ├── portfolio.py           # 组合/持仓表模型
│   │   │   ├── fund_nav_cache.py      # 基金净值缓存表
│   │   │   └── portfolio_return_cache.py # FOF收益曲线缓存表
│   │   └── services/           # 业务逻辑
│   │       └── portfolio_service.py   # 组合管理服务（含缓存逻辑）
│   ├── requirements.txt        # Python 依赖
│   └── fund_valuation.db       # 主数据库
├── frontend/                   # fundEval 前端 (端口 50888)
│   ├── src/                    # React 源码
│   │   ├── components/         # 组件目录
│   │   │   └── landing/        # 高端首页组件 ⭐新增
│   │   │       ├── AuthModal.tsx      # 登录/注册弹窗
│   │   │       ├── HeroSection.tsx    # Hero主视觉区
│   │   │       ├── FeatureGrid.tsx    # 功能卡片网格
│   │   │       └── PreviewShowcase.tsx # 功能预览区
│   │   ├── pages/              # 页面目录
│   │   │   ├── LandingPage.tsx        # 首页（公开访问，内置登录弹窗）
│   │   │   ├── FundDetail.tsx         # 基金详情页（玻璃拟态设计）
│   │   │   ├── PortfolioManager.tsx   # 组合管理页（玻璃拟态设计）
│   │   │   ├── Watchlist.tsx          # 自选监控页（玻璃拟态设计）
│   │   │   └── Register.tsx           # 注册页
│   │   ├── components/         # 组件目录
│   │   │   ├── landing/        # 高端首页组件
│   │   │   │   ├── AuthModal.tsx      # 登录/注册弹窗
│   │   │   │   ├── HeroSection.tsx    # Hero主视觉区
│   │   │   │   ├── FeatureGrid.tsx    # 功能卡片网格
│   │   │   │   └── PreviewShowcase.tsx # 功能预览区
│   │   │   └── dashboard/      # 统一仪表盘组件 ⭐新增
│   │   │       ├── DashboardLayout.tsx   # 统一布局组件
│   │   │       ├── DashboardSidebar.tsx  # 新式侧边栏
│   │   │       ├── GlassCard.tsx         # 毛玻璃卡片
│   │   │       └── CompactFundTable.tsx  # 紧凑基金表格
│   │   └── styles/             # 样式目录
│   │       ├── landing.css            # 高端首页样式
│   │       └── unified-dashboard.css  # 统一仪表盘样式 ⭐新增
│   │   ├── pages/archive/      # 归档页面（备份）
│   │   │   ├── Home.tsx.bak           # 原首页（已归档）
│   │   │   └── Login.tsx.bak          # 原登录页（已归档）
│   │   └── styles/             # 样式目录 ⭐新增
│   │       └── landing.css            # 高端首页样式
│   ├── package.json            # Node.js 依赖
│   └── vite.config.ts          # Vite 配置
├── estimation_service/         # 估值数据采集服务 (端口 50802)
│   ├── api_async.py            # FastAPI 服务入口
│   ├── collector.py            # 数据采集器
│   ├── scheduler.py            # 定时调度器
│   ├── database_async.py       # 异步数据库操作
│   ├── run_all.py              # 统一启动脚本
│   ├── fund_estimation.db      # 估值数据库 (1.5GB)
│   └── requirements.txt        # Python 依赖
├── fund_valuation.db           # fundEval 数据库
├── startup.bat                 # 智能启动脚本（推荐）
├── startup_tabs.bat            # Windows Terminal 多标签模式
├── startup_multiwindow.bat     # 多窗口模式
└── README.md                   # 项目说明
```

## 系统要求

- **Windows 10/11**
- **Python 3.8+**
- **Node.js 16+**
- **Windows Terminal** (可选，用于多标签模式)

## 快速启动

### 方式一：智能启动脚本（推荐）

双击运行 `startup.bat`，自动检测并选择最佳启动方式：

```batch
startup.bat
```

- 如果安装了 Windows Terminal → 使用多标签模式
- 否则 → 使用多窗口模式

### 方式二：Windows Terminal 多标签模式

适合喜欢在一个窗口中管理所有服务的用户：

```batch
startup_tabs.bat
```

启动后使用 `Ctrl+Tab` 切换标签页。

### 方式三：多窗口模式

兼容性最好的传统方式：

```batch
startup_multiwindow.bat
```

### 方式四：手动启动

如果需要单独控制各个服务：

```batch
:: 1. 启动估值服务
cd estimation_service
python run_all.py

:: 2. 启动主后端（新窗口）
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 50801 --reload

:: 3. 启动前端（新窗口）
cd frontend
npm run dev -- --port 50888
```

## 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 首页 (LandingPage) | http://localhost:50888/ | 浅色科技风设计，公开访问，内置登录弹窗 |
| 注册页 | http://localhost:50888/register | 用户注册页面 |
| 基金详情 | http://localhost:50888/fund/:code | 基金详情页（玻璃拟态设计，需登录） |
| 组合管理 | http://localhost:50888/portfolio | 组合管理页（玻璃拟态设计，需登录） |
| 自选监控 | http://localhost:50888/watchlist | 自选监控页（玻璃拟态设计，需登录） |
| 主后端 API | http://localhost:50801/docs | FastAPI 文档 |
| 估值服务 API | http://localhost:50802/docs | FastAPI 文档 |
| API 详情文档 | [front-api-details.md](./front-api-details.md) | 前端页面与 API 端口映射文档 |

## 端口配置

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端 | 50888 | Vite 开发服务器 |
| 主后端 | 50801 | FastAPI 主服务 |
| 估值服务 | 50802 | 独立估值数据采集服务 |

## 依赖安装

### Python 依赖

主后端依赖：
```batch
cd backend
pip install -r requirements.txt
```

估值服务依赖：
```batch
cd estimation_service
pip install -r requirements.txt
```

### Node.js 依赖

```batch
cd frontend
npm install
```

## 项目说明

### fundEval 主应用
- **前端**: React + TypeScript + Vite + Ant Design + ECharts
- **后端**: FastAPI + SQLAlchemy + SQLite
- **功能**:
  - LandingPage 首页（浅色科技风，毛玻璃效果，公开访问）
  - 用户认证（注册/登录/JWT Token，弹窗式登录）
  - 基金搜索、详情查看、自选列表
  - 组合管理（支持交易记录、市值曲线、收益率曲线）
  - 净值日期显示
  - 实时估值数据展示

### 最近更新

#### 2026-03-18 V2界面正式替换老UI ⭐重要更新

**玻璃拟态设计界面成为主版本**：

- **路由更新**: V2页面正式替换原有老UI页面
  - `/watchlist` → WatchlistV2（玻璃拟态自选监控）
  - `/portfolio` → PortfolioManagerV2（玻璃拟态组合管理）
  - `/fund/:code` → FundDetailV2（玻璃拟态基金详情）
- **移除旧路由**: 不再提供 `/watchlist-v2`、`/portfolio-v2`、`/fund-v2/:code` 访问路径
- **代码变更**: `App.tsx` 路由配置更新，直接导入V2组件作为主版本

#### 2026-03-18 首页预览图表优化

**LandingPage 功能预览区图表全面升级**:

- **组合跟踪预览** (`PreviewShowcase.tsx`):
  - 饼图替换为收益率走势图（TWR），更直观展示组合收益功能
  - 双Y轴设计：左侧收益率(%)，右侧当日收益(元)
  - 收益率曲线（红涨绿跌）+ 当日收益柱状图 + 零线参考
  - 拟合真实 TWR 数据走势（1/17-3/18，含多次涨跌波动）
  - 移除统计摘要，图表区域更大

- **实时估值预览**:
  - 数据点从 10 个增加到 50 个（每 5 分钟一个点）
  - 模拟真实基金估值的阶梯状平台期特征
  - 增加盘中冲高回落、探底回升等波动形态

- **净值分析预览**:
  - 数据点从 7 个增加到 91 个（每天一个点，约 3 个月数据）
  - 净值范围 1.85 ~ 2.48，涨幅约 35%
  - 拟合真实基金走势：多波上涨 + 深度回调 + 震荡整理
  - 移除数据点圆圈标记，改为纯线条

#### 2026-03-18 V2 页面 Bug 修复

**修复自选监控和组合管理页面的交互问题**:

- **图表卡片样式修复**: V2 页面图表组件移除内部边框，融入外层毛玻璃容器
  - `PortfolioValueChart.tsx` - 总资产走势 Card
  - `PortfolioReturnChart.tsx` - 收益率走势 Card
  - `IntradayValuationChart.tsx` - 实时估值 Card
  - `NavHistoryChart.tsx` - 历史净值走势 Card
  - 统一添加 `bordered={false}` 和 `background: 'transparent'`

- **自选监控页面优化**: `WatchlistV2.tsx`
  - 移除基金详情卡片的固定高度限制
  - 卡片高度改为自适应内容，消除双滚动条问题

- **组合管理分页修复**: `CompactFundTable.tsx`
  - 修复分页下拉菜单被遮挡问题（使用 `ConfigProvider` 设置 `getPopupContainer`）
  - 修复切换分页条数无响应问题（添加受控分页状态 `pagination`）

#### 2026-03-18 前端页面美化统一计划 ⭐重要更新

**统一 Dashboard 浅色科技风格，提升用户体验**:

- **玻璃拟态设计页面**（已正式替换老UI）:
  - 采用毛玻璃效果卡片（`backdrop-filter: blur(10px)`）
  - 渐变主色：`linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)`
  - 浅色背景：`linear-gradient(180deg, #f0f7ff 0%, #ffffff 100%)`

- **统一设计系统**:
  - 毛玻璃效果卡片（`backdrop-filter: blur(10px)`）
  - 渐变主色：`linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)`
  - 浅色背景：`linear-gradient(180deg, #f0f7ff 0%, #ffffff 100%)`
  - 统一导航栏：Logo + 华福资管 + 用户下拉菜单

- **新式侧边栏**:
  - 毛玻璃背景替代深蓝灰色（`#304156`）
  - 选中状态：渐变左侧指示条 + 淡蓝背景
  - Hover 效果：轻微上浮 + 阴影增强

- **紧凑布局优化**（金融监控场景）:
  - 表格行高减小到 40px
  - 卡片 padding 16px
  - 字体大小 12-14px
  - 一屏显示更多基金信息

- **新增组件**:
  - `DashboardLayout` - 统一布局组件
  - `DashboardSidebar` - 新式侧边栏
  - `GlassCard` - 毛玻璃卡片
  - `CompactFundTable` - 紧凑基金表格

- **样式文件**:
  - `unified-dashboard.css` - 统一 CSS 变量和组件样式

#### 2026-03-18 删除页面底部组件

**LandingPage 页面底部简化**:

- **删除统计区域**: 移除 Stats Section（10000+基金、99%准确率、3秒更新、24/7服务）
- **删除页脚区域**: 移除 Footer（华福资管标题、描述、版权信息、相关链接）
- **样式清理**: 同步删除 `landing.css` 中对应的 `.stats-section`、`.landing-footer` 等样式
- **页面结构**: 现在页面底部直接结束于 Preview Showcase 区域，更加简洁

#### 2026-03-18 首页导航栏优化

**头部区域全面升级**:

- **Logo 替换**: 左上角使用华福资管 logo 图片替代原有渐变图标
- **用户下拉菜单**: 右上角用户标签改为下拉菜单，包含：
  - 用户信息展示（禁用状态）
  - 修改密码功能（弹窗表单，支持密码验证）
  - 退出登录功能
- **移除按钮**: 删除"进入系统"按钮，简化导航栏
- **技术实现**: `AuthContext` 新增 `changePassword` 方法，调用后端 `POST /auth/change-password`

#### 2026-03-18 LandingPage 正式成为首页 ⭐重要更新

**LandingPage 已替换原有的 Home 首页和 Login 登录页**:

- **首页地址**: `/` 现在显示 LandingPage（公开访问，无需登录）
- **登录方式**: 通过顶部导航栏的"登录"按钮或点击需登录功能时弹出 AuthModal
- **移除路由**: `/login` 和 `/landing` 路由已移除
- **受保护路由**: `/fund/:fundCode`、`/portfolio`、`/watchlist` 仍需登录
- **自动跳转**: 未登录访问受保护路由时，自动重定向到首页并弹出登录框
- **归档文件**: 原 `Home.tsx` 和 `Login.tsx` 已归档为 `.bak` 文件

#### 2026-03-17 高端首页设计（Landing Page）

**全新高端首页，浅色科技风格设计**:

- **公开访问**: 路径对所有用户可见，无需登录
- **毛玻璃效果**: 使用 `backdrop-filter` 实现半透明玻璃态卡片
- **动态背景**: 网格动画 + 渐变光晕装饰
- **功能预览**: 集成 ECharts 图表展示功能预览（实时估值、净值走势、资产配置）
- **登录弹窗**: 点击需登录功能时弹出 AuthModal，支持登录/注册标签切换

**技术实现**:
- 组件目录 `frontend/src/components/landing/`
- 样式文件 `frontend/src/styles/landing.css`
- 使用 CSS 变量实现主题色统一管理
- 响应式布局，适配移动端和桌面端

**布局优化**:
- 删除"核心功能"标题和副标题，功能卡片直接跟随统计数据
- 大幅压缩各区块间距（Hero→Stats→Features 间距减少 75%）
- 更新统计数据：支持基金 20000+，准确率 90%+
- 优化副标题文案，突出日内估值和组合管理功能

#### 2026-03-17 PortfolioSummaryCard 组件增强

- **功能**: 优化组合管理页面 Summary 组件信息展示
- **日期显示**: 在"最新总市值"和"最新涨跌幅"旁添加净值日期标签（如 03-16）
- **估算标识**: 在"估算总市值"和"估算涨跌幅"旁添加"估"标签，明确标识估算数据
- **历史总收益**: 新增历史总收益统计项，与收益率走势卡片数据保持一致
- **布局调整**: 从4列布局调整为5列，桌面端响应式优化

#### 2026-03-17 用户认证系统

- **功能**: 新增完整的用户认证系统
- **后端**: JWT Token 认证、用户注册/登录/登出 API
- **前端**: 登录页、注册页、受保护路由
- **数据库**: users 表、watchlists 表（用户自选）
- **修复**: WatchlistDB SQLAlchemy relationship 缺失问题

#### 2026-03-17 基金详情页强制刷新功能
- **功能**: 基金详情页"刷新"按钮升级为"强制刷新"
- **效果**: 点击后跳过所有缓存（内存缓存、数据库缓存），直接从 TTJJ API 获取最新持仓数据
- **适用场景**: 当发现持仓数据可能不是最新时，手动强制同步
- **性能提示**: 强制刷新耗时较长（约30秒+），请耐心等待
- **技术实现**:
  - 后端路由 `GET /api/v1/funds/{fund_code}/holdings` 新增 `refresh` 查询参数
  - 后端服务 `fund_service.get_fund_holdings()` 支持强制刷新模式
  - 前端 API `api.getFundHoldings()` 新增 `refresh` 参数
  - 前端页面按钮添加 tooltip 提示用户此操作耗时较长

#### 2026-03-12 组合管理功能增强
- **估算市值优化**: 当估算净值未更新时，自动使用最新净值计算，避免显示为0，并在UI显示"昨"标识提示用户
- **交易记录功能**: 完整的买入/卖出交易管理
  - 买入/卖出弹窗，支持份额和金额二选一输入（自动计算另一项）
  - 每笔交易记录确认日期、净值、份额、金额
  - 基金详情抽屉展示持仓信息和完整交易历史
  - 交易汇总统计（净投入、当前份额等）
- **市值和收益率曲线**: 历史数据可视化
  - 总资产走势图（总市值 vs 总成本）
  - 收益率走势图（含零线参考）
  - 支持时间周期选择：近30天、近60天、近半年、今年以来
  - 显示关键统计数据：当前值、区间涨跌、最高/最低值

#### 2026-03-13 组合管理核心Bug修复
- **双倍持仓问题**: 修复添加基金时导致持仓份额双倍计算的问题
- **卖出校验修复**: 修复卖出份额校验逻辑，防止重复计算持仓
- **持仓明细刷新**: 基金详情抽屉添加刷新按钮，支持手动刷新交易记录
- **日期净值自动获取**: 添加基金时选择日期后自动获取该日期的历史净值
- **删除交易保护**: 删除买入交易时检查是否会导致负持仓，防止数据不一致
- **交易日验证**: 选择非交易日时显示警告提示

#### 2026-03-13 FOF图表逻辑优化（重要）
从FOF基金管理人视角重构收益率计算和图表展示：

**收益率计算逻辑修正**:
- **简单收益率**（主指标）: (总市值 - 总成本) / 总成本 × 100%
- **时间加权收益率(TWR)**: 剔除资金进出影响，反映投资能力
- **资金加权收益率(XIRR)**: 考虑时间价值的年化收益率

**图表双Y轴展示**:
- **收益率走势卡片**:
  - 左轴：收益率曲线（红涨绿跌）
  - 右轴：当日收益额柱状图（红涨绿跌，半透明=估算数据）
- **总资产走势卡片**:
  - 左轴：总市值/总成本曲线
  - 右轴：总收益曲线（红盈绿亏，虚线=估算数据）

**周末/节假日处理**:
- 自动向前查找最近交易日净值
- 估算数据标记（半透明颜色、Tooltip提示"估"）

**性能优化**:
- 新增基金净值缓存表（`fund_nav_cache`）
- 新增FOF收益曲线缓存表（`portfolio_return_cache`）
- 交易录入时自动失效缓存，确保数据一致性

**页面底部说明**:
- 添加收益率计算说明
- 添加图表数据说明

#### 2026-03-12 Bug修复
- **图表不显示问题**: 修复 echarts 异步加载导致图表显示"暂无历史数据"的问题
- **主表格份额不更新**: 修复买入/卖出交易后主表格份额未实时刷新的问题
- **总成本计算逻辑**: 修复 NAV 数据缺失时总成本计算不准确的问题

#### 前期更新
- **Portfolio 页面**: 添加净值日期显示，在"最新净值"和"最新涨跌"列标题显示日期标识
- **API 文档**: 添加前端页面与 API 端口映射文档 [front-api-details.md](./front-api-details.md)

### fund_estimation_system 估值服务
- **框架**: FastAPI + Uvicorn
- **数据源**: AKShare
- **采集频率**: 交易日 9:30-11:30, 13:00-15:00，每 2 分钟一次
- **数据库**: SQLite (约 1.5GB，包含历史估值数据)
- **API 端点**:
  - `GET /api/health` - 健康检查
  - `GET /api/v1/fund/estimation` - 获取基金估值
  - `GET /api/v1/fund/latest` - 获取最新估值列表
  - `GET /api/v1/fund/list` - 获取基金列表
  - `GET /api/v1/system/stats` - 系统统计

## 故障排除

### 服务启动失败

1. **检查端口占用**
   ```batch
   netstat -ano | findstr "50801 50802 50888"
   ```
   如果端口被占用，结束占用进程或修改脚本中的端口。

2. **检查 Python/Node.js 是否安装**
   ```batch
   python --version
   node --version
   npm --version
   ```

3. **检查依赖是否安装**
   - 确保运行了 `pip install -r requirements.txt`
   - 确保运行了 `npm install`

### Windows Terminal 模式无法使用

如果 `startup_tabs.bat` 提示找不到 Windows Terminal：

1. 从 Microsoft Store 安装 Windows Terminal
2. 或改用 `startup_multiwindow.bat`

### 中文显示乱码

所有批处理文件使用英文显示，避免编码问题。

## 注意事项

1. **端口占用**: 确保 50801、50802、50888 端口未被其他程序占用
2. **数据库文件**: `fund_estimation.db` 约 1.5GB，复制和启动可能需要较长时间
3. **Node 依赖**: 首次使用前端需要运行 `npm install`
4. **Python 依赖**: 需要安装两个项目的 Python 依赖

## 停止服务

- **多窗口模式**: 直接关闭各个服务的命令行窗口
- **多标签模式**: 关闭 Windows Terminal 窗口
- **估值服务**: 支持按 `Ctrl+C` 优雅退出

## FOF收益率计算说明

作为FOF基金管理人，平台提供三种收益率计算方式：

| 收益率类型 | 计算公式 | 用途 | 特点 |
|------------|----------|------|------|
| **简单收益率** | (总市值 - 总成本) / 总成本 × 100% | 日常监控盈亏 | 直观易懂，受资金流入流出影响 |
| **时间加权(TWR)** | ∏(1 + 区间收益率) - 1 | 评估投资能力 | 剔除资金进出影响，公平对比 |
| **资金加权(XIRR)** | 年化IRR | 与理财产品对比 | 考虑时间价值，适合长期对比 |

### 当日收益额计算

```
当日收益额 = 当日总市值 - 昨日总市值 - 当日新增投入 + 当日赎回
```

- 买入不影响当日收益额（只是资产形态转换）
- 卖出不影响当日收益额（只是资产形态转换）
- 真正影响当日收益额的是基金净值涨跌

### 估算数据说明

当遇到周末/节假日或净值未更新时：
- **系统行为**: 自动向前查找最近交易日净值
- **图表标识**: 半透明颜色、虚线、Tooltip标注"估"
- **数据质量**: 估算数据仅供参考，实际以官方净值为准

## 技术方案

本项目采用**多进程启动模式**：
- 保留两个后端服务独立运行
- 通过统一 BAT 脚本管理三个服务进程

**优点**:
- 改动最小，风险最低
- 服务职责清晰，互不干扰
- 估值服务频繁写数据库，独立运行更稳定

### 缓存机制

为提升性能，系统实现了两级缓存：

1. **基金净值缓存** (`fund_nav_cache`)
   - 缓存每只基金的历史净值
   - 全系统共享，避免重复查询

2. **FOF收益曲线缓存** (`portfolio_return_cache`)
   - 缓存每个组合的每日收益数据
   - 交易录入时自动失效并重新计算

**缓存失效策略**:
- 录入新交易时，从交易日期开始清空缓存
- 删除交易时，从交易日期开始清空缓存
- 确保历史数据的一致性
