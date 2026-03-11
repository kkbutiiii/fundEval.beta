# 基金实时估值系统 - 前端

基于 React + TypeScript + Ant Design 的基金实时估值前端应用，提供基金搜索、实时估值展示、历史走势分析等功能。

## 技术栈

- **框架**: React 18.3
- **语言**: TypeScript 5.6
- **构建工具**: Vite 5.4
- **UI 组件库**: Ant Design 5.21
- **图表库**: ECharts 5.5 + echarts-for-react
- **路由**: React Router DOM 6.26
- **HTTP 客户端**: Axios
- **日期处理**: Dayjs

## 项目结构

```
frontend/
├── src/
│   ├── components/              # React 组件
│   │   ├── FundSearch.tsx       # 基金搜索组件（自动完成）
│   │   ├── ValuationDisplay.tsx # 估值结果展示卡片
│   │   ├── AssetAllocationCard.tsx      # 资产配置历史图表
│   │   ├── NavHistoryChart.tsx          # 净值历史走势图
│   │   ├── IntradayValuationChart.tsx   # 日内估值分时图
│   │   ├── BondHoldingsTable.tsx        # 债券持仓表格
│   │   └── ConvertibleHoldingsTable.tsx # 可转债持仓表格
│   ├── pages/                   # 页面组件
│   │   ├── Home.tsx             # 首页（搜索/热门基金）
│   │   └── FundDetail.tsx       # 基金详情页
│   ├── services/                # API 服务
│   │   └── api.ts               # 后端 API 客户端
│   ├── types/                   # TypeScript 类型定义
│   │   └── index.ts             # 全站类型定义
│   ├── App.tsx                  # 应用主组件
│   ├── main.tsx                 # 入口文件
│   └── index.css                # 全局样式
├── index.html                   # HTML 模板
├── package.json                 # 依赖配置
├── tsconfig.json                # TypeScript 配置
├── vite.config.ts               # Vite 配置
└── README.md                    # 本文档
```

## 开发指南

### 安装依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 启动开发服务器

```bash
npm run dev
```

服务将在 http://localhost:50888 运行

### 构建生产版本

```bash
npm run build
```

构建输出位于 `dist/` 目录

### 预览生产构建

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
```

## 组件说明

### FundSearch.tsx

基金搜索组件，支持模糊搜索和自动完成。

**Props**:
- `onSelect`: (fund: Fund) => void - 选中基金回调
- `placeholder?`: string - 占位符文本

**特性**:
- 支持基金代码、名称、拼音搜索
- 防抖处理（300ms）
- 最多显示 10 条结果

### ValuationDisplay.tsx

估值结果展示卡片，显示实时估值、涨跌幅、贡献度分析。

**Props**:
- `valuation`: ValuationResult - 估值结果数据
- `loading?`: boolean - 加载状态

### IntradayValuationChart.tsx

日内估值分时图，展示当日估值变化曲线。

**Props**:
- `data`: IntradayValuationData - 日内估值数据
- `loading?`: boolean - 加载状态

**特性**:
- 标记 11:30 和 13:00 午间休市
- 支持缩放
- 显示 Wind 估值对比线

### NavHistoryChart.tsx

净值历史走势图，展示基金净值与基准指数的对比。

**Props**:
- `data`: NavHistoryData - 净值历史数据
- `loading?`: boolean - 加载状态

**特性**:
- 支持 1月/3月/6月/1年/2年/5年 切换
- 多线对比（基金净值、业绩基准、沪深300）

### AssetAllocationCard.tsx

资产配置历史卡片，展示最近 8 个季度的资产配置变化。

**Props**:
- `data`: AssetAllocationHistory - 资产配置数据
- `loading?`: boolean - 加载状态

**图表类型**: 堆叠柱状图 + 净资产折线

### BondHoldingsTable.tsx / ConvertibleHoldingsTable.tsx

债券和可转债持仓表格。

**Props**:
- `holdings`: BondHolding[] / ConvertibleHolding[] - 持仓数据
- `loading?`: boolean - 加载状态

## 页面说明

### Home.tsx（首页）

- 基金搜索框（居中）
- 热门基金列表（实时估值标签）
- 功能特性介绍

### FundDetail.tsx（基金详情页）

路由: `/fund/:fundCode`

包含模块:
1. 基金基本信息头部
2. 实时估值卡片
3. 日内估值分时图
4. 净值历史走势图
5. 资产配置历史
6. 持仓明细标签页（股票/债券/可转债）
7. 自动刷新（每 30 秒）

## API 服务

所有 API 调用封装在 `src/services/api.ts`：

```typescript
// 搜索基金
searchFunds(keyword: string): Promise<Fund[]>

// 获取基金信息
getFundInfo(fundCode: string): Promise<FundInfo>

// 获取基金持仓
getFundHoldings(fundCode: string): Promise<Fund>

// 获取实时估值
getFundValuation(fundCode: string): Promise<ValuationResult>

// 获取资产配置历史
getAssetAllocation(fundCode: string, quarters?: number): Promise<AssetAllocationHistory>

// 获取净值历史
getNavHistory(fundCode: string, period?: string): Promise<NavHistoryData>

// 获取日内估值
getIntradayValuation(fundCode: string): Promise<IntradayValuationData>
```

## 类型定义

所有 TypeScript 类型定义在 `src/types/index.ts`：

- `FundInfo` - 基金基本信息
- `FundHolding` - 股票持仓
- `BondHolding` - 债券持仓
- `ConvertibleHolding` - 可转债持仓
- `AssetAllocation` - 资产配置数据
- `ValuationResult` - 估值结果
- `NavHistoryData` - 净值历史
- `IntradayValuationData` - 日内估值

## 开发规范

### 代码风格

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- Props 使用接口定义
- 异步操作使用 async/await

### 组件开发模板

```typescript
import React from 'react';
import { Card, Spin } from 'antd';

interface MyComponentProps {
  data: SomeData;
  loading?: boolean;
}

const MyComponent: React.FC<MyComponentProps> = ({ data, loading }) => {
  if (loading) {
    return <Card><Spin /></Card>;
  }

  return (
    <Card title="组件标题">
      {/* 组件内容 */}
    </Card>
  );
};

export default MyComponent;
```

## 代理配置

开发时 API 代理配置在 `vite.config.ts`：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:50801',
      changeOrigin: true
    }
  }
}
```

## 构建部署

### Docker 构建

```bash
# 构建前端镜像
docker build -t fund-valuation-frontend .

# 运行容器
docker run -d -p 80:80 --name fund-frontend fund-valuation-frontend
```

### Docker Compose

```bash
# 在项目根目录执行
docker-compose up -d frontend
```

## 注意事项

1. **API 地址**: 开发时通过 Vite 代理访问后端，生产环境通过 Nginx 反向代理
2. **类型安全**: 所有 API 响应都需要定义 TypeScript 接口
3. **错误处理**: API 调用需要处理网络错误和超时
4. **性能优化**: 大列表使用虚拟滚动，图表按需加载

## 相关文档

- [项目根目录 README](../README.md) - 项目整体说明
- [后端文档](../backend/README.md) - 后端 API 文档
