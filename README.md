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
│   ├── requirements.txt        # Python 依赖
│   └── fund_valuation.db       # 主数据库
├── frontend/                   # fundEval 前端 (端口 50888)
│   ├── src/                    # React 源码
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
| 前端 | http://localhost:50888 | Vite 开发服务器 |
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
  - 基金搜索、详情查看、自选列表
  - 组合管理（支持交易记录、市值曲线、收益率曲线）
  - 净值日期显示
  - 实时估值数据展示

### 最近更新

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

## 技术方案

本项目采用**多进程启动模式**：
- 保留两个后端服务独立运行
- 通过统一 BAT 脚本管理三个服务进程

**优点**:
- 改动最小，风险最低
- 服务职责清晰，互不干扰
- 估值服务频繁写数据库，独立运行更稳定
