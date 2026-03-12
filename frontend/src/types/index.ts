/**
 * TypeScript type definitions for the fund valuation system.
 */

export interface FundInfo {
  fund_code: string;
  fund_name: string;
  fund_type?: string;
  nav?: number;
  nav_date?: string;
  total_assets?: number;
  manager?: string;
  company?: string;
  benchmark?: string;
  // 扩展字段 (来自 TTJJ)
  nav_change_percent?: number;        // 日涨跌幅
  accumulated_nav?: number;           // 累计净值
  risk_level?: string;                // 风险等级 (如: 中高风险)
  rating?: number;                    // 基金评级 (1-5星)
  // 业绩表现
  return_1m?: number;                 // 近1月收益率
  return_3m?: number;                 // 近3月收益率
  return_6m?: number;                 // 近6月收益率
  return_1y?: number;                 // 近1年收益率
  return_3y?: number;                 // 近3年收益率
  return_ytd?: number;                // 今年以来收益率
  return_since_inception?: number;    // 成立以来收益率
  inception_date?: string;            // 成立日期
}

export interface FundHolding {
  stock_code: string;
  stock_name: string;
  weight: number;
  shares?: number;
  market_value?: number;
  change_percent?: number;
  contribution?: number;
}

export interface Fund {
  fund_code: string;
  fund_name: string;
  fund_type?: string;
  nav?: number;
  nav_date?: string;
  previous_nav?: number;
  total_stock_ratio: number;
  top10_holdings: FundHolding[];
  top10_total_weight: number;
  report_date?: string;
  // Bond-related fields
  total_bond_ratio?: number;
  bond_holdings?: BondHolding[];
  bond_total_weight?: number;
  convertible_holdings?: ConvertibleHolding[];
  convertible_total_weight?: number;
}

export interface HoldingContribution {
  stock_code: string;
  stock_name: string;
  weight: number;
  change_percent: number;
  contribution: number;
}

export interface ValuationResult {
  fund_code: string;
  fund_name?: string;
  latest_nav?: number;
  nav_date?: string;
  estimated_nav: number;
  estimated_change_percent: number;
  top10_contribution: number;
  top10_weight: number;
  remaining_contribution: number;
  remaining_weight: number;
  holdings_details: HoldingContribution[];
  completion_method: string;
  completion_index?: string;
  completion_index_change?: number;
  calculation_time: string;
  report_date?: string;
  data_source: string;
  disclaimer: string;
}

export interface SearchResponse {
  funds: FundInfo[];
  total: number;
}

export interface ValuationResponse {
  success: boolean;
  data?: ValuationResult;
  message: string;
}

// Asset Allocation Types
export interface AssetAllocation {
  report_date: string;
  stock_ratio: number;
  bond_ratio: number;
  cash_ratio: number;
  other_ratio: number;
  net_asset?: number;
}

export interface AssetAllocationHistory {
  fund_code: string;
  allocations: AssetAllocation[];
}

// Bond Holdings Types
export interface BondHolding {
  bond_code: string;
  bond_name: string;
  weight: number;
  market_value?: number;
  change_percent?: number;  // 实时涨跌幅
}

export interface ConvertibleHolding {
  bond_code: string;
  bond_name: string;
  weight: number;
  market_value?: number;
  change_percent?: number;  // 实时涨跌幅
  conversion_premium?: number;
}

// Enhanced Fund with bond holdings
export interface FundWithBonds extends Fund {
  total_bond_ratio: number;
  bond_holdings: BondHolding[];
  bond_total_weight: number;
  convertible_holdings: ConvertibleHolding[];
  convertible_total_weight: number;
}

// NAV History Types
export interface NavHistoryPoint {
  date: string;
  nav: number;
  nav_acc?: number;
}

export interface NavHistoryData {
  fund_code: string;
  fund_nav_history: NavHistoryPoint[];
  benchmark_history: NavHistoryPoint[];
  market_index_history: NavHistoryPoint[];
}

// Intraday Valuation Types
export interface IntradayValuationPoint {
  time: string;
  estimated_change_percent: number;
  estimated_nav: number;
}

export interface IntradayValuationData {
  fund_code: string;
  valuation_history: IntradayValuationPoint[];
  west_estimate?: number;
  sample_count?: number;
  last_update?: string;
}

// =============================================================================
// External Estimation API Types (from fund_estimation_system / 天天基金)
// =============================================================================

/** Single estimation data point from TTJJ API */
export interface EstimationDataPoint {
  time: string;
  nav: number;
  growth: number;
}

/** Fund estimation response from external API */
export interface FundEstimation {
  code: string;
  name?: string;
  date: number;
  data: EstimationDataPoint[];
  count: number;
  first_time?: string;
  last_time?: string;
}

/** Generic response wrapper for estimation API */
export interface EstimationAPIResponse {
  success: boolean;
  message: string;
  data?: FundEstimation;
}

/** Summary of a single fund's latest estimation */
export interface EstimationSummary {
  code: string;
  name?: string;
  date: number;
  latest_nav?: number;
  latest_growth?: number;
  previous_nav?: number;
  last_time?: string;
  data_count: number;
}

// =============================================================================
// Portfolio Management Types
// =============================================================================

/** Single fund holding in a portfolio */
export interface PortfolioFund {
  fund_code: string;
  fund_name: string;
  shares: number;              // Holdings shares (user input)
  // Fields from API
  estimated_nav?: number;      // Estimated NAV
  estimated_growth?: number;   // Estimated change percent (%)
  latest_nav?: number;         // Latest NAV (yesterday close)
  latest_growth?: number;      // Latest change percent (%)
  // Time fields
  estimation_time?: string;    // Estimation time (e.g., "03/11 15:30")
  nav_date?: string;           // NAV date (e.g., "03/10")
  // Calculated fields
  estimated_value?: number;    // Estimated value = shares * estimated_nav
  latest_value?: number;       // Latest value = shares * latest_nav
  // Flag to indicate if estimated_value uses latest_nav as fallback
  is_estimated_fallback?: boolean;  // True when estimated_nav is missing and latest_nav is used
}

/** Fund portfolio */
export interface FundPortfolio {
  id: string;                  // Unique portfolio ID
  name: string;                // Portfolio name
  funds: PortfolioFund[];      // Fund list
  created_at: number;          // Creation timestamp
  updated_at: number;          // Update timestamp
}

/** Portfolio summary statistics */
export interface PortfolioSummary {
  total_estimated_value: number;    // Total estimated value
  total_latest_value: number;       // Total latest value
  total_estimated_growth: number;   // Total estimated growth (weighted)
  total_latest_growth: number;      // Total latest growth (weighted)
  fund_count: number;               // Number of funds
}

// =============================================================================
// Fund Transaction Types
// =============================================================================

/** Single buy/sell transaction for a fund */
export interface FundTransaction {
  id: number;
  portfolio_id: string;
  fund_code: string;
  fund_name: string;
  transaction_type: 'buy' | 'sell';
  transaction_date: string;  // YYYY-MM-DD
  nav: number;              // Confirmation NAV
  shares: number;           // Number of shares
  amount: number;           // Transaction amount
  created_at: string;
}

/** Request to create a new transaction */
export interface CreateTransactionRequest {
  transaction_type: 'buy' | 'sell';
  transaction_date: string;  // YYYY-MM-DD
  nav: number;
  shares?: number;           // Either shares or amount must be provided
  amount?: number;
}

/** Summary of transactions for a fund */
export interface TransactionSummary {
  fund_code: string;
  fund_name: string;
  total_bought_shares: number;
  total_sold_shares: number;
  current_shares: number;
  total_bought_amount: number;
  total_sold_amount: number;
  net_investment: number;
}

// =============================================================================
// Portfolio History Types
// =============================================================================

/** Single data point for portfolio history */
export interface PortfolioHistoryPoint {
  date: string;           // YYYY-MM-DD
  total_value: number;    // Total market value
  total_cost: number;     // Total cost basis
  return_rate: number;    // Return rate in percentage
}

/** Portfolio history response */
export interface PortfolioHistory {
  portfolio_id: string;
  period: string;
  data: PortfolioHistoryPoint[];
}
