# 组合管理页面前端测试计划

## 测试环境要求
- 后端服务运行在 http://localhost:50801
- 前端服务运行在 http://localhost:5173

## 测试场景

### 1. 添加基金功能（首次买入）
**测试步骤：**
1. 打开组合管理页面
2. 选择一个组合（或创建新组合）
3. 点击"添加基金"按钮
4. 在搜索框输入基金代码（如：000001）
5. 选择搜索结果中的基金
6. 填写确认日期（默认为今天）
7. 填写确认净值
8. 填写买入份额，验证金额自动计算
9. 或填写买入金额，验证份额自动计算
10. 点击"添加"按钮

**预期结果：**
- 弹窗关闭
- 基金出现在主表格中
- 交易记录中显示首笔买入记录
- 提示"基金添加成功（已记录首次买入交易）"

### 2. 买入交易功能
**测试步骤：**
1. 在主表格中选择一个基金
2. 点击"买入"按钮
3. 填写确认日期、净值、份额/金额
4. 点击确认

**预期结果：**
- 交易成功提示
- 主表格份额更新
- 交易记录中显示新记录
- 图表数据更新

### 3. 卖出交易功能
**测试步骤：**
1. 在主表格中选择一个有持仓的基金
2. 点击"卖出"按钮
3. 填写卖出份额（不超过持仓）
4. 点击确认

**预期结果：**
- 交易成功提示
- 主表格份额减少
- 交易记录中显示卖出记录
- 图表数据更新

### 4. 基金详情抽屉
**测试步骤：**
1. 点击基金代码或名称
2. 查看抽屉中的信息
3. 验证当前份额、净投入显示正确
4. 查看交易记录列表

**预期结果：**
- 抽屉正常打开
- 显示正确的持仓信息
- 交易记录列表完整

### 5. 总资产走势图
**测试步骤：**
1. 查看图表是否正确渲染
2. 切换时间周期（30d/60d/6m/ytd）
3. 查看统计数据（当前资产、区间涨跌等）

**预期结果：**
- 图表正常显示，不显示"暂无历史数据"
- 时间切换正常
- 统计数据正确

### 6. 收益率走势图
**测试步骤：**
1. 查看收益率图表是否正确渲染
2. 验证收益率基于净值变化而非资产变化
3. 切换时间周期

**预期结果：**
- 图表正常显示
- 收益率计算正确（不受申购赎回影响）
- 零线显示正常

### 7. 性能测试
**测试步骤：**
1. 添加多个基金（10+只）
2. 为每只基金添加多笔交易
3. 观察页面响应速度
4. 查看图表渲染性能

**预期结果：**
- 页面加载时间 < 3秒
- 交易操作响应 < 1秒
- 图表渲染流畅

### 8. 错误处理
**测试步骤：**
1. 尝试添加已存在的基金
2. 尝试卖出超过持仓的份额
3. 网络断开时操作
4. 填写无效的日期/净值

**预期结果：**
- 显示适当的错误提示
- 不会崩溃
- 数据保持一致

## 自动化测试脚本（Playwright）

```python
# test_portfolio.py
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def page(page: Page):
    page.goto("http://localhost:5173/portfolio")
    yield page

def test_add_fund_with_first_buy(page: Page):
    """测试添加基金作为首次买入"""
    # 等待页面加载
    page.wait_for_selector("text=组合管理")

    # 点击添加基金
    page.click("text=添加基金")

    # 搜索基金
    page.fill("input[placeholder*='搜索']", "000001")
    page.wait_for_timeout(1000)

    # 选择基金
    page.click("text=华夏成长混合")

    # 填写交易信息
    page.fill("input[placeholder*='净值']", "1.1080")
    page.fill("input[placeholder*='份额']", "1000")

    # 验证金额自动计算
    amount_input = page.locator("input[placeholder*='金额']")
    expect(amount_input).to_have_value("1108")

    # 提交
    page.click("button:has-text('添加')")

    # 验证成功提示
    expect(page.locator("text=基金添加成功")).to_be_visible()

def test_buy_transaction(page: Page):
    """测试买入交易"""
    # 等待表格加载
    page.wait_for_selector("table")

    # 点击买入按钮
    page.click("button:has-text('买入')")

    # 填写交易信息
    page.fill("input[placeholder*='净值']", "1.1200")
    page.fill("input[placeholder*='份额']", "500")

    # 提交
    page.click("button:has-text('确认买入')")

    # 验证成功
    expect(page.locator("text=买入成功")).to_be_visible()

def test_charts_render(page: Page):
    """测试图表渲染"""
    page.wait_for_timeout(2000)

    # 验证图表存在
    expect(page.locator("text=总资产走势")).to_be_visible()
    expect(page.locator("text=收益率走势")).to_be_visible()

    # 验证不为空状态
    expect(page.locator("text=暂无历史数据")).not_to_be_visible()
```

## 手动测试清单

- [ ] 添加新基金时显示"首次买入"弹窗
- [ ] 份额/金额自动计算正确
- [ ] 交易后主表格份额实时更新
- [ ] 交易记录完整显示
- [ ] 总资产走势图正常显示
- [ ] 收益率走势图正常显示
- [ ] 收益率不受申购赎回影响
- [ ] 图表时间周期切换正常
- [ ] 基金详情抽屉正常打开
- [ ] 批量导入功能正常

## 已知问题跟踪

| 问题 | 状态 | 备注 |
|------|------|------|
| 图表 echarts 异步加载 | ✅ 已修复 | 使用状态管理 |
| 主表格份额不更新 | ✅ 已修复 | 同时刷新组合和实时数据 |
| 总成本计算不准确 | ✅ 已修复 | 成本计算独立于 NAV |
