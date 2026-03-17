# 基金实时估值系统 - 后端

基于 FastAPI 的基金实时估值后端服务，提供基金数据获取、实时估值计算、资产配置查询等功能。

## 技术栈

- **Web 框架**: FastAPI 0.115.0
- **ASGI 服务器**: Uvicorn
- **ORM**: SQLAlchemy 2.0 + aiosqlite (异步 SQLite)
- **数据验证**: Pydantic 2.x
- **数据源**: 天天基金 API (主要) / AKShare / Wind API / 东方财富 API
- **定时任务**: APScheduler
- **缓存**: 内存缓存 (cachetools) + 数据库缓存 (基金净值缓存、FOF收益曲线缓存)
- **数据库**: SQLite (可扩展至 PostgreSQL/MySQL)

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接和会话管理 ⭐新增
│   ├── db_models/              # SQLAlchemy 数据库模型 ⭐新增
│   │   ├── __init__.py
│   │   ├── user.py             # 用户表模型 ⭐新增
│   │   ├── watchlist.py        # 自选基金表模型 ⭐新增
│   │   ├── portfolio.py        # 组合/持仓表模型
│   │   ├── transaction.py      # 交易记录表模型 ⭐新增
│   │   ├── fund_nav_cache.py   # 基金净值缓存表 ⭐新增
│   │   └── portfolio_return_cache.py # FOF收益曲线缓存表 ⭐新增
│   ├── models/                 # Pydantic 数据模型
│   │   ├── fund.py             # 基金/持仓/资产配置模型
│   │   ├── valuation.py        # 估值结果模型
│   │   ├── portfolio.py        # 组合管理模型 ⭐新增
│   │   └── transaction.py      # 交易记录模型 ⭐新增
│   ├── routers/                # API 路由
│   │   ├── auth.py             # 用户认证接口 ⭐新增
│   │   ├── funds.py            # 基金相关接口
│   │   ├── portfolios.py       # 组合管理接口 ⭐新增
│   │   └── watchlist.py        # 自选基金接口 ⭐新增
│   ├── services/               # 业务逻辑服务
│   │   ├── fund_service.py     # 基金数据获取 (DB优先) ⭐更新
│   │   ├── fund_data_db_service.py  # 基金数据库查询 ⭐新增
│   │   ├── fund_data_sync_service.py # 基金数据同步 ⭐新增
│   │   ├── user_init_service.py # 新用户数据初始化 ⭐新增
│   │   ├── ttjj_client.py      # 天天基金 API 客户端
│   │   ├── portfolio_service.py # 组合管理服务
│   │   ├── stock_service.py    # 股票行情获取
│   │   ├── valuation_engine.py # 估值计算引擎
│   │   └── wind_client.py      # Wind API 客户端
│   └── utils/                  # 工具函数
│       ├── fund_list_cache.py  # 基金列表缓存
│       ├── benchmark_parser.py # 业绩基准解析器
│       └── intraday_cache.py   # 日内估值缓存
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 构建文件
└── README.md                   # 本文档
```

## 安装和运行

### 本地开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python -m app.main
# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 50801
```

服务将在 http://localhost:50801 运行，API 文档地址：http://localhost:50801/docs

### Docker 部署

```bash
# 构建镜像
docker build -t fund-valuation-backend .

# 运行容器
docker run -d -p 50801:50801 --name fund-backend fund-valuation-backend
```

### Docker Compose（推荐）

```bash
# 在项目根目录执行
docker-compose up -d backend
```

## API 端点列表

### 用户认证 ⭐新增

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册（自动初始化默认数据） |
| POST | `/api/v1/auth/login` | 用户登录（返回 JWT Token） |
| POST | `/api/v1/auth/logout` | 用户登出 |
| GET | `/api/v1/auth/me` | 获取当前登录用户信息 |
| POST | `/api/v1/auth/refresh` | 刷新访问令牌 |

#### 新用户初始数据

用户注册成功后，系统会自动初始化以下默认数据：

**1. 自选基金（4只）:**
| 基金代码 | 说明 |
|---------|------|
| 024110 | 默认自选基金 |
| 016699 | 默认自选基金 |
| 011949 | 默认自选基金 |
| 005819 | 默认自选基金 |

**2. 案例组合:**
- **组合名称**: 案例组合#1
- **基金代码**: 008888
- **交易记录**: 16笔历史交易（包含申购/赎回）

**说明:**
- 初始化失败不会影响注册流程
- 基金名称从 `fund_info` 表自动获取，如不存在则使用基金代码
- 案例组合的持仓份额根据交易记录自动计算

#### 认证流程

**1. 注册新用户:**
```bash
curl -X POST "http://localhost:50801/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123"
  }'
```

**2. 用户登录:**
```bash
curl -X POST "http://localhost:50801/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123"
  }'
```

**响应示例:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "testuser",
    "is_admin": false,
    "created_at": "2026-03-17T08:00:00"
  }
}
```

**3. 访问受保护资源:**
```bash
curl "http://localhost:50801/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### 自选基金 ⭐新增

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/watchlist` | 获取用户的自选基金列表 |
| POST | `/api/v1/watchlist` | 添加基金到自选 |
| DELETE | `/api/v1/watchlist/{fund_code}` | 从自选移除基金 |
| GET | `/api/v1/watchlist/valuation` | 获取自选基金的实时估值 |

### 基金搜索

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/funds/search` | 搜索基金（代码/名称/拼音） |
| GET | `/api/v1/funds/all` | 获取全部基金列表 |

### 基金信息

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/funds/{fund_code}/info` | 获取基金详细信息（含收益率、评级等）⭐丰富字段 |
| GET | `/api/v1/funds/{fund_code}/holdings` | 获取基金持仓明细 |
| GET | `/api/v1/funds/{fund_code}/asset-allocation` | 获取资产配置历史 |
| GET | `/api/v1/funds/{fund_code}/nav-history` | 获取净值历史走势 |

### 估值相关

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/funds/{fund_code}/valuation` | 获取实时估值 |
| GET | `/api/v1/funds/{fund_code}/intraday-valuation` | 获取日内估值分时 |
| POST | `/api/v1/funds/batch-valuation` | 批量获取多个基金估值 |

### 组合管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/portfolios` | 获取所有组合列表 |
| POST | `/api/v1/portfolios` | 创建新组合 |
| GET | `/api/v1/portfolios/{id}` | 获取组合详情（含持仓和实时估值） |
| PUT | `/api/v1/portfolios/{id}` | 更新组合名称 |
| DELETE | `/api/v1/portfolios/{id}` | 删除组合 |
| POST | `/api/v1/portfolios/{id}/funds` | 添加基金到组合 |
| PUT | `/api/v1/portfolios/{id}/funds/{code}` | 更新基金份额 |
| DELETE | `/api/v1/portfolios/{id}/funds/{code}` | 从组合移除基金 |
| POST | `/api/v1/portfolios/{id}/funds/batch` | 批量添加基金 |

### 交易记录

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/portfolios/{id}/funds/{code}/transactions` | 创建买入/卖出交易 |
| GET | `/api/v1/portfolios/{id}/transactions` | 获取组合所有交易记录 |
| GET | `/api/v1/portfolios/{id}/funds/{code}/transactions` | 获取指定基金的交易记录 |
| DELETE | `/api/v1/portfolios/{id}/transactions/{tx_id}` | 删除交易记录 |
| GET | `/api/v1/portfolios/{id}/funds/{code}/transaction-summary` | 获取基金交易汇总 |
| GET | `/api/v1/portfolios/{id}/history` | 获取组合历史市值和收益率（支持三种收益率计算）⭐ |

#### 交易记录 API 示例

**创建买入交易（填写份额，自动计算金额）:**
```bash
curl -X POST "http://localhost:50801/api/v1/portfolios/portfolio_xxx/funds/000001/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "buy",
    "transaction_date": "2026-03-10",
    "nav": 1.1080,
    "shares": 1000
  }'
```

**创建买入交易（填写金额，自动计算份额）:**
```bash
curl -X POST "http://localhost:50801/api/v1/portfolios/portfolio_xxx/funds/000001/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "buy",
    "transaction_date": "2026-03-10",
    "nav": 1.1080,
    "amount": 1108.00
  }'
```

**创建卖出交易:**
```bash
curl -X POST "http://localhost:50801/api/v1/portfolios/portfolio_xxx/funds/000001/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "sell",
    "transaction_date": "2026-03-12",
    "nav": 1.1200,
    "shares": 500
  }'
```

**获取历史市值和收益率:**
```bash
# 获取近30天数据（支持：30d, 60d, 6m, ytd）
curl "http://localhost:50801/api/v1/portfolios/portfolio_xxx/history?period=30d"
```

**响应示例:**
```json
{
  "portfolio_id": "portfolio_xxx",
  "period": "30d",
  "data": [
    {
      "date": "2026-02-10",
      "total_value": 15000.00,
      "total_cost": 14500.00,
      "total_profit": 500.00,
      "daily_profit": 120.50,
      "return_rate": 3.45,
      "twr": 3.42,
      "xirr": 45.6,
      "is_estimated": false
    },
    {
      "date": "2026-02-11",
      "total_value": 15120.50,
      "total_cost": 14500.00,
      "total_profit": 620.50,
      "daily_profit": 120.50,
      "return_rate": 4.28,
      "twr": 4.25,
      "xirr": 52.3,
      "is_estimated": false
    }
  ]
}
```

**字段说明:**

| 字段 | 类型 | 说明 |
|------|------|------|
| `date` | string | 日期 (YYYY-MM-DD) |
| `total_value` | float | 总市值（各基金份额 × 当日净值之和） |
| `total_cost` | float | 总成本（累计买入 - 累计卖出） |
| `total_profit` | float | 总收益（总市值 - 总成本） |
| `daily_profit` | float | 当日收益额（当日市值变化 - 当日新增投入） |
| `return_rate` | float | 简单收益率（主指标）= (总市值 - 总成本) / 总成本 × 100% |
| `twr` | float | 时间加权收益率(TWR)，剔除资金进出影响 |
| `xirr` | float | 资金加权收益率(XIRR)，考虑时间价值的年化收益率 |
| `is_estimated` | boolean | 是否使用了估算净值（周末/节假日） |

### FundInfo 模型字段说明

| 字段名 | 类型 | 说明 | 数据来源 |
|--------|------|------|----------|
| `fund_code` | string | 基金代码 | TTJJ |
| `fund_name` | string | 基金名称 | TTJJ |
| `fund_type` | string | 基金类型 | TTJJ |
| `nav` | float | 最新单位净值 | TTJJ pingzhongdata API |
| `nav_date` | date | 净值日期 | TTJJ |
| `total_assets` | float | 基金规模(亿元) | TTJJ HTML页面 |
| `manager` | string | 基金经理 | TTJJ pingzhongdata API |
| `company` | string | 基金公司 | TTJJ pingzhongdata API |
| `benchmark` | string | 业绩比较基准 | 数据库 |
| `nav_change_percent` | float | 日涨跌幅(%) | TTJJ rankhandler API |
| `accumulated_nav` | float | 累计净值 | TTJJ rankhandler API |
| `risk_level` | string | 风险等级 | TTJJ HTML页面 |
| `rating` | int | 基金评级(1-5星) | TTJJ 评级页面 |
| `return_1m` | float | 近1月收益率(%) | TTJJ rankhandler API |
| `return_3m` | float | 近3月收益率(%) | TTJJ rankhandler API |
| `return_6m` | float | 近6月收益率(%) | TTJJ rankhandler API |
| `return_1y` | float | 近1年收益率(%) | TTJJ rankhandler API |
| `return_3y` | float | 近3年收益率(%) | TTJJ rankhandler API |
| `return_ytd` | float | 今年以来收益率(%) | TTJJ rankhandler API |
| `return_since_inception` | float | 成立以来收益率(%) | TTJJ rankhandler API |

### API 使用示例

```bash
# 获取基金基本信息（包含所有新字段）
curl "http://localhost:50801/api/v1/funds/002351/info"
```

**响应示例:**
```json
{
  "fund_code": "002351",
  "fund_name": "易方达裕祥回报债券A",
  "fund_type": "债券型-混合二级",
  "nav": 1.635,
  "nav_date": "2026-03-02",
  "total_assets": 123.45,
  "manager": "王晓晨",
  "company": "易方达基金",
  "benchmark": "中债新综合财富指数收益率×90%+沪深300指数收益率×10%",
  "nav_change_percent": 0.25,
  "accumulated_nav": 1.96,
  "risk_level": "中低风险",
  "rating": 5,
  "return_1m": 1.36,
  "return_3m": 2.57,
  "return_6m": 3.28,
  "return_1y": 7.69,
  "return_3y": 16.77,
  "return_ytd": 1.81,
  "return_since_inception": 100.68
}
```

### 管理接口

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/funds/admin/cache-stats` | 查看缓存统计 |
| POST | `/api/v1/funds/admin/refresh-cache` | 手动刷新基金列表缓存 |
| POST | `/api/v1/funds/admin/sync-fund-data` | 手动触发基金数据同步 ⭐新增 |
| GET | `/api/v1/funds/admin/sync-status` | 查看数据同步状态 ⭐新增 |
| GET | `/health` | 健康检查 |

#### 数据同步接口使用示例

```bash
# 同步单个基金
curl -X POST "http://localhost:50801/api/v1/funds/admin/sync-fund-data?fund_code=002474"

# 批量同步前100只基金
curl -X POST "http://localhost:50801/api/v1/funds/admin/sync-fund-data?limit=100"

# 执行增量同步（只同步未同步过的基金）
curl -X POST "http://localhost:50801/api/v1/funds/admin/sync-fund-data"

# 查看同步状态
curl "http://localhost:50801/api/v1/funds/admin/sync-status"
```

## API 文档

启动服务后，访问以下地址查看交互式 API 文档：

- **Swagger UI**: http://localhost:50801/docs
- **ReDoc**: http://localhost:50801/redoc

## Wind API 集成

后端可选集成 Wind 金融数据终端 API，提供更准确的数据：

### 需要 Wind 的数据

- 资产配置历史（股票/债券/现金比例）
- 债券和可转债持仓明细
- 基金净值历史
- 业绩基准指数数据

### 配置方式

```python
# app/services/wind_client.py
# Wind API 自动检测，如果未安装 WindPy 则回退到 AKShare
```

安装 WindPy（如有 Wind 终端）：

```bash
pip install WindPy
```

## 环境变量配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `DEBUG` | `false` | 调试模式 |
| `PORT` | `8000` | 服务端口 |
| `HOST` | `0.0.0.0` | 绑定地址 |
| `DATABASE_URL` | `sqlite:///./fund_valuation.db` | 数据库连接URL |
| `NO_PROXY` | `*` | 禁用代理（解决东方财富 API 访问问题）|

## 核心功能说明

### 1. 基金列表缓存

- 启动时加载全部基金列表（26,000+）到内存
- 搜索速度提升 600-800 倍（6秒 → 10毫秒）
- 每天凌晨 00:00 自动刷新

### 2. 估值计算引擎

```
基金实时估值 = 前一交易日净值 × (1 + 估算涨跌幅)

估算涨跌幅 = 重仓股贡献 + 股票补全贡献 + 债券补全贡献
```

- 解析业绩比较基准获取股票/债券指数
- 已披露持仓直接计算，未披露部分使用基准指数补全
- 支持股票型基金和债券型基金的混合估值

### 3. 日内估值采样

- 交易日 9:30-15:00 每 30 秒采样一次
- 缓存当日估值历史，支持分时图展示

### 4. 基金数据本地存储与同步 ⭐核心功能

**三层数据读取策略:**

```
用户请求持仓数据
    │
    ├─→ 1. 内存缓存 (TTL 1天) ──→ ~0.2s 响应
    │      未命中 ↓
    ├─→ 2. SQLite 数据库 ────→ ~0.2s 响应
    │      未命中 ↓
    └─→ 3. TTJJ API 获取 ────→ 10-15s 响应
           ↓
    自动保存到数据库 + 内存缓存
```

**数据库表结构:**

```sql
-- 基金基本信息表
CREATE TABLE fund_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code VARCHAR(10) UNIQUE NOT NULL,
    fund_name VARCHAR(200) NOT NULL,
    fund_type VARCHAR(50),
    company VARCHAR(100),
    manager VARCHAR(100),
    benchmark TEXT,
    latest_nav FLOAT,
    nav_date DATETIME
);

-- 基金持仓明细表 (季度更新)
CREATE TABLE fund_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code VARCHAR(10) NOT NULL,
    report_date VARCHAR(8) NOT NULL,  -- YYYYMMDD
    stock_holdings JSON,  -- 股票持仓 [{code, name, weight, shares, market_value}]
    bond_holdings JSON,   -- 债券持仓 [{code, name, weight, market_value, is_convertible}]
    top10_total_weight FLOAT DEFAULT 0,
    total_stock_ratio FLOAT DEFAULT 0,
    total_bond_ratio FLOAT DEFAULT 0,
    UNIQUE(fund_code, report_date)
);

-- 资产配置历史表
CREATE TABLE asset_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code VARCHAR(10) NOT NULL,
    report_date VARCHAR(8) NOT NULL,
    stock_ratio FLOAT DEFAULT 0,
    bond_ratio FLOAT DEFAULT 0,
    cash_ratio FLOAT DEFAULT 0,
    other_ratio FLOAT DEFAULT 0,
    net_asset FLOAT DEFAULT 0,
    UNIQUE(fund_code, report_date)
);
```

**自动同步机制:**

- **定时同步**: 每天凌晨 02:00 执行增量同步
- **首次访问**: 从 TTJJ API 获取并自动保存到数据库
- **增量更新**: 只同步未同步过或报告期过期的基金
- **手动触发**: 通过管理接口手动触发同步任务

**性能提升:**

| 状态 | 响应时间 | 数据来源 |
|------|----------|----------|
| 首次访问 | 10-15s | TTJJ API (自动保存到DB) |
| 后续访问 | **~0.2s** | SQLite 本地数据库 |
| 缓存命中 | **~0.2s** | 内存缓存 |

### 5. 组合管理与FOF收益率计算 ⭐核心功能

#### 数据库表结构

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- 自选基金表
CREATE TABLE watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fund_code VARCHAR(20) NOT NULL,
    fund_name VARCHAR(255) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, fund_code)
);

-- 组合表
CREATE TABLE portfolios (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 持仓表
CREATE TABLE portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id TEXT NOT NULL,
    fund_code TEXT NOT NULL,
    fund_name TEXT NOT NULL,
    shares REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);

-- 交易记录表
CREATE TABLE fund_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id TEXT NOT NULL,
    fund_code VARCHAR(20) NOT NULL,
    fund_name VARCHAR(255) NOT NULL,
    transaction_type VARCHAR(10) NOT NULL,  -- 'buy' 或 'sell'
    transaction_date DATE NOT NULL,          -- 确认日期
    nav FLOAT NOT NULL,                      -- 确认净值
    shares FLOAT NOT NULL,                   -- 份额
    amount FLOAT NOT NULL,                   -- 金额
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);

-- 基金净值缓存表 ⭐新增
CREATE TABLE fund_nav_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    nav DECIMAL(10, 4),
    is_estimated BOOLEAN DEFAULT 0,          -- 是否使用往前查找的净值
    actual_date DATE,                        -- 实际净值日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fund_code, date)
);

-- FOF收益曲线缓存表 ⭐新增
CREATE TABLE portfolio_return_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_value DECIMAL(15, 2),              -- 总市值
    total_cost DECIMAL(15, 2),               -- 总成本
    total_profit DECIMAL(15, 2),             -- 总收益
    daily_profit DECIMAL(15, 2),             -- 当日收益额
    return_rate DECIMAL(10, 4),              -- 简单收益率(%)
    twr DECIMAL(10, 4),                      -- 时间加权收益率(%)
    xirr DECIMAL(10, 4),                     -- 资金加权收益率(%)
    is_estimated BOOLEAN DEFAULT 0,          -- 是否使用了估算净值
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, date)
);
```

#### 三种收益率计算方法

**1. 简单收益率 (Simple Return) - 主指标**
```
简单收益率 = (总市值 - 总成本) / 总成本 × 100%
```
- 最直观的盈亏比例
- 受资金流入流出影响
- FOF管理人主要关注的指标

**2. 时间加权收益率 (TWR - Time-Weighted Return)**
```
TWR = ∏(1 + 区间收益率) - 1
```
- 剔除资金进出影响
- 反映投资能力（选基能力）
- 适合对比不同FOF产品

**3. 资金加权收益率 (XIRR - Money-Weighted Return)**
```
XIRR = 考虑时间价值的年化收益率
```
- 内部收益率(IRR)的扩展
- 考虑资金进出的时间点
- 可与理财产品收益率横向对比

#### 当日收益额计算

```
当日收益额 = 当日总市值 - 昨日总市值 - 当日新增投入 + 当日赎回
```

**特点：**
- 不包含当日买入带来的市值增加
- 不包含当日卖出导致的市值减少
- 真实反映持仓资产的当日盈亏

#### 缓存机制 ⭐性能优化

**双层缓存策略：**

```
获取组合历史数据
    │
    ├─→ 1. 检查 portfolio_return_cache ──→ 直接返回缓存数据
    │      未命中 ↓
    ├─→ 2. 检查 fund_nav_cache ──────────→ 避免重复查询API
    │      未命中 ↓
    └─→ 3. 调用 Wind API 获取净值 ───────→ 计算后保存到缓存
```

**缓存特点：**

| 缓存类型 | 表名 | 用途 | 共享范围 |
|----------|------|------|----------|
| 基金净值缓存 | fund_nav_cache | 缓存每只基金的历史净值 | 全系统共享 |
| FOF收益缓存 | portfolio_return_cache | 缓存组合的每日收益数据 | 每个组合单独 |

**增量更新机制：**
- 只计算缺失日期的数据，不重新计算全部
- 交易录入时自动失效相关日期的缓存
- 支持 `use_cache` 参数控制是否使用缓存

**性能提升：**

| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 30天 × 10只基金 | 300次API调用 | 0-10次API调用 | **30x+** |
| 数据查询 | 实时计算 | 缓存读取 | **10x+** |

#### 周末/节假日处理

**净值缺失处理：**
1. 尝试获取当日净值
2. 如未找到，向前查找最近交易日（最多10天）
3. 使用找到的净值作为估算值
4. 标记 `is_estimated = true`

**前端标注：**
- 当日收益额柱状图：使用估算数据时颜色半透明
- 收益率曲线：使用估算数据时线条变虚线
- Tooltip：显示"(估)"标记

### 6. 组合管理功能特性

**功能特性:**

- 完整的 CRUD 操作（创建/读取/更新/删除）
- 基金持仓管理（添加/移除/修改份额）
- 批量导入基金功能
- 交易记录管理（买入/卖出，支持份额/金额二选一输入）
- 历史市值和收益率曲线（支持 30d/60d/6m/ytd 周期）
- 实时估值统计计算（总市值/加权涨跌幅）
- 数据持久化存储（SQLite，可扩展至 PostgreSQL/MySQL）
- 级联删除（删除组合时自动删除关联持仓和交易记录）

**技术实现:**

- SQLAlchemy 2.0 异步 ORM
- aiosqlite 驱动支持
- FastAPI 依赖注入模式
- 事务管理确保数据一致性

## 性能优化

| 优化项 | 效果 |
|--------|------|
| 基金列表内存缓存 | 搜索速度提升 600-800 倍 |
| 基金数据本地存储 | 持仓查询从 10-15s 降至 ~0.2s (50-75倍提升) |
| 三层数据读取 | 内存缓存 → SQLite → API 自动降级 |
| FOF收益率缓存 | API调用从 300次/请求 降至 0-10次 (30x+提升) |
| 基金净值缓存 | 全系统共享，避免重复查询 |
| 禁用系统代理 | 解决东方财富 API 超时问题 |
| 多级缓存 | 基金信息、持仓、行情、净值数据缓存 |
| 批量 API 调用 | 减少外部请求次数 |
| 增量更新 | 只计算缺失日期，不重新计算全部 |

## 性能基准

### 持仓接口性能对比

| 数据来源 | 响应时间 | 说明 |
|----------|----------|------|
| 内存缓存 | ~0.2s | 最优，重启丢失 |
| SQLite数据库 | ~0.2s | 持久化，推荐 |
| TTJJ API | 10-15s | 首次或数据过期 |

### 典型响应时间

```
GET /api/v1/funds/search          ~0.2s   ✅
GET /api/v1/funds/{code}/holdings ~0.2s   ✅ (已同步基金)
GET /api/v1/funds/{code}/asset-allocation ~0.4s ✅
GET /api/v1/portfolios            ~0.5s   ✅
```

## 注意事项

1. **数据准确性**: 估值结果仅供参考，季报数据有滞后性
2. **API 限制**: 使用免费数据源，频繁调用可能触发限流
3. **代理配置**: 已禁用系统代理以避免东方财富 API 访问问题
4. **内存占用**: 基金列表缓存约占用 20MB 内存

## 相关文档

- [缓存优化方案](./CACHE_OPTIMIZATION.md) - 基金列表缓存优化详情
- [FOF收益率计算说明](#三种收益率计算方法) - FOF基金管理人视角的收益率计算逻辑
- [项目根目录 README](../README.md) - 项目整体说明
