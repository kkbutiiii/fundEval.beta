-- Create Fund NAV Cache Table
CREATE TABLE IF NOT EXISTS fund_nav_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    nav DECIMAL(10, 4),
    is_estimated BOOLEAN DEFAULT 0,
    actual_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fund_code, date)
);

CREATE INDEX IF NOT EXISTS idx_fund_nav_code ON fund_nav_cache(fund_code);
CREATE INDEX IF NOT EXISTS idx_fund_nav_date ON fund_nav_cache(date);

-- Create Portfolio Return Cache Table
CREATE TABLE IF NOT EXISTS portfolio_return_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_value DECIMAL(15, 2),
    total_cost DECIMAL(15, 2),
    total_profit DECIMAL(15, 2),
    daily_profit DECIMAL(15, 2),
    return_rate DECIMAL(10, 4),
    twr DECIMAL(10, 4),
    xirr DECIMAL(10, 4),
    -- TWR calculation: Fund-of-Funds perspective
    fund_shares DECIMAL(20, 8),     -- 母基金份额（仅在资金进出时变化）
    fund_nav DECIMAL(15, 6),        -- 母基金净值
    -- Cache version for invalidation
    calculation_version INTEGER DEFAULT 1,  -- 缓存版本，算法更新时递增
    is_estimated BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, date)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_return_id ON portfolio_return_cache(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_return_date ON portfolio_return_cache(date);
