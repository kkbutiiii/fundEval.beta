# FundEval Beta - 前端 API 端口详情文档

## 项目概述

FundEval Beta 是一个基金实时估值系统，采用前后端分离架构。

---

## 服务端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端开发服务器 | 50888 | Vite 开发服务器 |
| 后端 API 服务 | 50801 | FastAPI 主服务 |
| 估值计算服务 | 50802 | 独立估值数据服务 (天天基金网数据) |

### 配置文件位置

- **前端端口配置**: `frontend/vite.config.ts`
- **后端端口配置**: `backend/app/config.py`
- **启动脚本**: `startup.bat`

---

## API 基础配置

### 前端 API 基础 URL

```typescript
// frontend/src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
```

### Vite 代理配置

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:50801',  // 后端 API 服务地址
    changeOrigin: true,
  },
}
```

### 后端 CORS 配置

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 页面与 API 调用映射

### 1. 首页 (Home)

**文件位置**: `frontend/src/pages/Home.tsx`

**路由**: `/`

**调用的 API**:

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `GET` | `/api/v1/funds/all?limit=500` | 获取基金列表 |
| `POST` | `/api/v1/funds/batch-valuation` | 批量获取热门基金估值 |

**详情**:
```typescript
// 获取所有基金
api.getAllFunds(500)

// 批量获取估值
api.getBatchValuation(['000001', '005827', '161725', ...])
```

---

### 2. 基金详情页 (FundDetail)

**文件位置**: `frontend/src/pages/FundDetail.tsx`

**路由**: `/fund/:fundCode`

**调用的 API**:

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `GET` | `/api/v1/funds/{fundCode}/info` | 获取基金基本信息 |
| `GET` | `/api/v1/funds/{fundCode}/holdings` | 获取基金持仓数据 |
| `GET` | `/api/v1/funds/{fundCode}/holdings?refresh=true` | **强制刷新**持仓数据（跳过缓存） |

**强制刷新功能**:
- **用途**: 当持仓数据可能不是最新时，手动强制从 TTJJ API 获取
- **触发方式**: 点击页面右上角"强制刷新"按钮
- **性能影响**: 跳过内存缓存和数据库缓存，耗时约30秒+
- **实现原理**: 后端 `refresh=true` 参数直接调用 TTJJ API，获取后更新缓存

**使用的子组件及其 API**:

#### IntradayValuationChart 组件
**文件位置**: `frontend/src/components/IntradayValuationChart.tsx`

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `GET` | `/api/v1/funds/{fundCode}/intraday-valuation` | 获取日内估值历史 |

**自动刷新**: 30秒间隔（交易时间内）

#### NavHistoryChart 组件
**文件位置**: `frontend/src/components/NavHistoryChart.tsx`

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `GET` | `/api/v1/funds/{fundCode}/nav-history?period={period}` | 获取净值历史 |

**支持周期**: `1m`, `3m`, `6m`, `1y`, `2y`, `5y`

#### AssetAllocationCard 组件
**文件位置**: `frontend/src/components/AssetAllocationCard.tsx`

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `GET` | `/api/v1/funds/{fundCode}/asset-allocation?quarters=8` | 获取资产配置历史 |

---

### 3. 自选监控页 (Watchlist)

**文件位置**: `frontend/src/pages/Watchlist.tsx`

**路由**: `/watchlist`

**调用的 API** (通过 useWatchlist Hook):

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `POST` | `/api/v1/funds/batch-valuation` | 批量获取自选基金实时估值 |

**Hook 文件**: `frontend/src/hooks/useWatchlist.ts`

**自动刷新**: 30秒间隔

---

### 4. 基金组合管理页 (PortfolioManager)

**文件位置**: `frontend/src/pages/PortfolioManager.tsx`

**路由**: `/portfolio`

**调用的 API**:

#### 组合管理 (usePortfolios Hook)
**文件位置**: `frontend/src/hooks/usePortfolios.ts`

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `GET` | `/api/v1/portfolios` | 获取所有组合 |
| `POST` | `/api/v1/portfolios` | 创建新组合 |
| `GET` | `/api/v1/portfolios/{id}` | 获取组合详情 |
| `PUT` | `/api/v1/portfolios/{id}` | 更新组合名称 |
| `DELETE` | `/api/v1/portfolios/{id}` | 删除组合 |
| `POST` | `/api/v1/portfolios/{id}/funds` | 添加基金到组合 |
| `PUT` | `/api/v1/portfolios/{id}/funds/{fundCode}` | 更新基金份额 |
| `DELETE` | `/api/v1/portfolios/{id}/funds/{fundCode}` | 从组合移除基金 |
| `POST` | `/api/v1/portfolios/{id}/funds/batch` | 批量添加基金 |

#### 实时估值 (usePortfolioRealtime Hook)
**文件位置**: `frontend/src/hooks/usePortfolioRealtime.ts`

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `POST` | `/api/v1/funds/batch-valuation` | 批量获取组合基金实时估值 |

**自动刷新**: 30秒间隔

---

## 通用组件 API 调用

### FundSearch 搜索组件

**文件位置**: `frontend/src/components/FundSearch.tsx`

| API 方法 | 端点 | 用途 |
|----------|------|------|
| `GET` | `/api/v1/funds/search?q={keyword}&limit=20` | 搜索基金 |

**防抖**: 300ms

---

## 后端路由汇总

### Funds 路由 (`backend/app/routers/funds.py`)

前缀: `/api/v1/funds`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/search` | 搜索基金 |
| `GET` | `/all` | 获取所有基金 |
| `GET` | `/{fund_code}/info` | 获取基金信息 |
| `GET` | `/{fund_code}/holdings` | 获取基金持仓 (支持 `?refresh=true` 强制刷新) |
| `GET` | `/{fund_code}/asset-allocation` | 获取资产配置历史 |
| `GET` | `/{fund_code}/intraday-valuation` | 获取日内估值 |
| `GET` | `/{fund_code}/nav-history` | 获取净值历史 |
| `GET` | `/{fund_code}/valuation` | 获取实时估值 |
| `POST` | `/batch-valuation` | 批量估值查询 |
| `GET` | `/admin/cache-stats` | 缓存统计 |
| `POST` | `/admin/refresh-cache` | 刷新缓存 |
| `POST` | `/admin/sync-fund-data` | 同步基金数据 |
| `GET` | `/admin/sync-status` | 同步状态 |

### Portfolios 路由 (`backend/app/routers/portfolios.py`)

前缀: `/api/v1/portfolios`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 获取所有组合 |
| `POST` | `/` | 创建组合 |
| `GET` | `/{portfolio_id}` | 获取组合详情 |
| `PUT` | `/{portfolio_id}` | 更新组合 |
| `DELETE` | `/{portfolio_id}` | 删除组合 |
| `POST` | `/{portfolio_id}/funds` | 添加基金 |
| `PUT` | `/{portfolio_id}/funds/{fund_code}` | 更新份额 |
| `DELETE` | `/{portfolio_id}/funds/{fund_code}` | 移除基金 |
| `POST` | `/{portfolio_id}/funds/batch` | 批量添加 |

### 系统端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 根路径信息 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/docs` | Swagger 文档 |

---

## 外部服务调用

### 估值服务 (天天基金网)

**配置**:
```python
# backend/app/config.py
estimation_api_base_url: str = "http://localhost:50802"
```

**调用位置**:
- `backend/app/services/estimation_api_client.py`
- `backend/app/routers/funds.py` (intraday-valuation, valuation, batch-valuation)

---

## 环境变量配置

```bash
# 前端
VITE_API_BASE_URL=/api/v1

# 后端
HOST=0.0.0.0
PORT=50801
DEBUG=true
ESTIMATION_API_BASE_URL=http://localhost:50802
DATABASE_URL=sqlite:///./fund_valuation.db
```

---

## 请求超时配置

| 位置 | 超时时间 | 说明 |
|------|----------|------|
| 前端 axios | 60000ms | `api.ts` 中的全局超时 |
| 估值 API | 10000ms | `ESTIMATION_API_TIMEOUT` |

---

## 自动刷新策略

| 功能 | 刷新间隔 | 触发条件 |
|------|----------|----------|
| 日内估值图表 | 30秒 | 交易时间内且页面可见 |
| 自选列表 | 30秒 | 持续刷新 |
| 组合实时数据 | 30秒 | 持续刷新 |
| 市场状态检查 | 60秒 | 定时检查 |

---

## 缓存策略

| 数据类型 | 缓存时间 | 位置 |
|----------|----------|------|
| 基金详情 | 5分钟 | `funds.py` 内存缓存 |
| 净值历史 | 1小时 | `funds.py` 内存缓存 |
| 基金列表 | 1天 | `fund_list_cache.py` |
| 持仓数据 | 1天 | `cache.py` + 数据库 |
| 股票价格 | 5秒 | `cache.py` |
| 估值数据 | 10秒 | `cache.py` |

### 强制刷新机制

对于**持仓数据**支持强制刷新：
- **正常加载**: 内存缓存 → 数据库缓存 → TTJJ API
- **强制刷新** (`?refresh=true`): 跳过所有缓存，直接调用 TTJJ API
- **刷新后**: 新数据会更新到数据库和内存缓存中
- **适用场景**: 当怀疑缓存数据不是最新时

**实现文件**:
- 后端: `backend/app/services/fund_service.py` - `get_fund_holdings(refresh=True)`
- 路由: `backend/app/routers/funds.py` - `/{fund_code}/holdings?refresh=true`
- 前端: `frontend/src/pages/FundDetail.tsx` - "强制刷新"按钮

---

## 文档生成时间

生成日期: 2026-03-17
