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
    is_estimated BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, date)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_return_id ON portfolio_return_cache(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_return_date ON portfolio_return_cache(date);
