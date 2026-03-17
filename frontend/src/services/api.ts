/**
 * API service for communicating with the backend.
 */
import axios, { AxiosInstance } from 'axios';
import type {
  FundInfo, Fund, SearchResponse,
  AssetAllocationHistory, NavHistoryData, IntradayValuationData,
  FundEstimation, EstimationAPIResponse, EstimationSummary,
  FundPortfolio, PortfolioFund, PortfolioSummary,
  FundTransaction, CreateTransactionRequest, TransactionSummary,
  PortfolioHistory
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        console.error('API Error:', error);

        // Handle 401 Unauthorized
        if (error.response?.status === 401) {
          // Clear auth tokens and redirect to login
          localStorage.removeItem('auth_tokens');
          localStorage.removeItem('auth_user');
          window.location.href = '/login';
        }

        return Promise.reject(error);
      }
    );

    // Add request interceptor to add Authorization header
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  /**
   * Search funds by keyword.
   */
  async searchFunds(keyword: string, limit: number = 20): Promise<FundInfo[]> {
    const response = await this.client.get<SearchResponse>('/funds/search', {
      params: { q: keyword, limit },
    });
    return response.data.funds;
  }

  /**
   * Get all funds.
   */
  async getAllFunds(limit: number = 100): Promise<FundInfo[]> {
    const response = await this.client.get<FundInfo[]>('/funds/all', {
      params: { limit },
    });
    return response.data;
  }

  /**
   * Get fund information.
   */
  async getFundInfo(fundCode: string): Promise<FundInfo> {
    const response = await this.client.get<FundInfo>(`/funds/${fundCode}/info`);
    return response.data;
  }

  /**
   * Get fund holdings.
   * @param fundCode - Fund code
   * @param refresh - Force refresh data from API, skip cache (default: false)
   */
  async getFundHoldings(fundCode: string, refresh: boolean = false): Promise<Fund> {
    const response = await this.client.get<Fund>(`/funds/${fundCode}/holdings`, {
      params: refresh ? { refresh: true } : undefined
    });
    return response.data;
  }

  /**
   * Get fund valuation (new format from TTJJ estimation API).
   */
  async getFundValuation(fundCode: string): Promise<EstimationAPIResponse> {
    const response = await this.client.get<EstimationAPIResponse>(`/funds/${fundCode}/valuation`);
    return response.data;
  }

  /**
   * Get batch valuation for multiple funds (new format).
   */
  async getBatchValuation(fundCodes: string[]): Promise<EstimationSummary[]> {
    const response = await this.client.post<{ success: boolean; data: EstimationSummary[]; failed_codes: string[]; message: string }>('/funds/batch-valuation', fundCodes);
    return response.data.data || [];
  }

  /**
   * Get asset allocation history.
   */
  async getAssetAllocation(fundCode: string, quarters: number = 8): Promise<AssetAllocationHistory> {
    const response = await this.client.get<AssetAllocationHistory>(`/funds/${fundCode}/asset-allocation`, {
      params: { quarters },
    });
    return response.data;
  }

  /**
   * Get NAV history.
   */
  async getNavHistory(fundCode: string, period: string = '1y'): Promise<NavHistoryData> {
    const response = await this.client.get<NavHistoryData>(`/funds/${fundCode}/nav-history`, {
      params: { period },
    });
    return response.data;
  }

  /**
   * Get intraday valuation history.
   * Converts FundEstimation from backend to IntradayValuationData for frontend.
   */
  async getIntradayValuation(fundCode: string): Promise<IntradayValuationData> {
    const response = await this.client.get<FundEstimation>(`/funds/${fundCode}/intraday-valuation`);
    const estimation = response.data;

    // Convert FundEstimation to IntradayValuationData
    const lastPoint = estimation.data[estimation.data.length - 1];
    return {
      fund_code: estimation.code,
      valuation_history: estimation.data.map(item => ({
        time: item.time,
        estimated_nav: item.nav,
        estimated_change_percent: item.growth
      })),
      west_estimate: undefined, // TTJJ API doesn't provide Wind estimate
      sample_count: estimation.count,
      last_update: estimation.last_time || lastPoint?.time
    };
  }

  // =============================================================================
  // Portfolio API Methods
  // =============================================================================

  /**
   * Get all portfolios.
   */
  async getPortfolios(): Promise<FundPortfolio[]> {
    const response = await this.client.get<{ portfolios: FundPortfolio[]; total: number }>('/portfolios');
    return response.data.portfolios;
  }

  /**
   * Create a new portfolio.
   */
  async createPortfolio(name: string): Promise<FundPortfolio> {
    const response = await this.client.post<FundPortfolio>('/portfolios', { name });
    return response.data;
  }

  /**
   * Get a portfolio by ID.
   */
  async getPortfolio(id: string): Promise<FundPortfolio & { summary?: PortfolioSummary }> {
    const response = await this.client.get<FundPortfolio & { summary?: PortfolioSummary }>(`/portfolios/${id}`);
    return response.data;
  }

  /**
   * Update a portfolio name.
   */
  async updatePortfolio(id: string, name: string): Promise<FundPortfolio> {
    const response = await this.client.put<FundPortfolio>(`/portfolios/${id}`, { name });
    return response.data;
  }

  /**
   * Delete a portfolio.
   */
  async deletePortfolio(id: string): Promise<void> {
    await this.client.delete(`/portfolios/${id}`);
  }

  /**
   * Add a fund to a portfolio.
   */
  async addFundToPortfolio(
    portfolioId: string,
    fund: { fund_code: string; fund_name: string; shares: number }
  ): Promise<FundPortfolio> {
    const response = await this.client.post<FundPortfolio>(`/portfolios/${portfolioId}/funds`, fund);
    return response.data;
  }

  /**
   * Update fund shares in a portfolio.
   */
  async updateFundShares(
    portfolioId: string,
    fundCode: string,
    shares: number
  ): Promise<FundPortfolio> {
    const response = await this.client.put<FundPortfolio>(
      `/portfolios/${portfolioId}/funds/${fundCode}`,
      { shares }
    );
    return response.data;
  }

  /**
   * Remove a fund from a portfolio.
   */
  async removeFundFromPortfolio(portfolioId: string, fundCode: string): Promise<FundPortfolio> {
    const response = await this.client.delete<FundPortfolio>(
      `/portfolios/${portfolioId}/funds/${fundCode}`
    );
    return response.data;
  }

  /**
   * Batch add funds to a portfolio.
   */
  async batchAddFunds(
    portfolioId: string,
    funds: { fund_code: string; fund_name: string; shares: number }[]
  ): Promise<{ success: boolean; added_count: number; skipped_count: number; message: string }> {
    const response = await this.client.post<{ success: boolean; added_count: number; skipped_count: number; message: string }>(
      `/portfolios/${portfolioId}/funds/batch`,
      { funds }
    );
    return response.data;
  }

  // =============================================================================
  // Transaction API Methods
  // =============================================================================

  /**
   * Create a buy/sell transaction for a fund in a portfolio.
   */
  async createTransaction(
    portfolioId: string,
    fundCode: string,
    data: CreateTransactionRequest
  ): Promise<FundTransaction> {
    const response = await this.client.post<FundTransaction>(
      `/portfolios/${portfolioId}/funds/${fundCode}/transactions`,
      data
    );
    return response.data;
  }

  /**
   * Get all transactions for a portfolio.
   */
  async getPortfolioTransactions(portfolioId: string): Promise<FundTransaction[]> {
    const response = await this.client.get<{ transactions: FundTransaction[]; total: number }>(
      `/portfolios/${portfolioId}/transactions`
    );
    return response.data.transactions;
  }

  /**
   * Get transactions for a specific fund in a portfolio.
   */
  async getFundTransactions(portfolioId: string, fundCode: string): Promise<FundTransaction[]> {
    const response = await this.client.get<{ transactions: FundTransaction[]; total: number }>(
      `/portfolios/${portfolioId}/funds/${fundCode}/transactions`
    );
    return response.data.transactions;
  }

  /**
   * Delete a transaction.
   */
  async deleteTransaction(portfolioId: string, transactionId: number): Promise<void> {
    await this.client.delete(`/portfolios/${portfolioId}/transactions/${transactionId}`);
  }

  /**
   * Get transaction summary for a fund.
   */
  async getTransactionSummary(portfolioId: string, fundCode: string): Promise<TransactionSummary> {
    const response = await this.client.get<TransactionSummary>(
      `/portfolios/${portfolioId}/funds/${fundCode}/transaction-summary`
    );
    return response.data;
  }

  /**
   * Get portfolio historical value and return data.
   */
  async getPortfolioHistory(portfolioId: string, period: string = '30d', calculationMethod: string = 'twr'): Promise<PortfolioHistory> {
    const response = await this.client.get<PortfolioHistory>(
      `/portfolios/${portfolioId}/history`,
      { params: { period, calculation_method: calculationMethod } }
    );
    return response.data;
  }

  /**
   * Manually refresh portfolio cache.
   * Clears all cached historical data and forces recalculation.
   */
  async refreshPortfolioCache(portfolioId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post<{ success: boolean; message: string }>(
      `/portfolios/${portfolioId}/refresh-cache`
    );
    return response.data;
  }

  // =============================================================================
  // Auth Helper Methods
  // =============================================================================

  /**
   * Get access token from localStorage.
   */
  private getAccessToken(): string | null {
    const storedTokens = localStorage.getItem('auth_tokens');
    if (!storedTokens) return null;
    try {
      const tokens = JSON.parse(storedTokens);
      return tokens.access_token;
    } catch {
      return null;
    }
  }

  // =============================================================================
  // Watchlist API Methods
  // =============================================================================

  /**
   * Get user's watchlist.
   */
  async getWatchlist(): Promise<{ fund_code: string; fund_name: string; added_at: string }[]> {
    const response = await this.client.get<{ watchlist: { fund_code: string; fund_name: string; added_at: string }[]; total: number }>('/watchlists');
    return response.data.watchlist;
  }

  /**
   * Add a fund to watchlist.
   */
  async addToWatchlist(fundCode: string, fundName: string): Promise<{ fund_code: string; fund_name: string; added_at: string }> {
    const response = await this.client.post<{ fund_code: string; fund_name: string; added_at: string }>('/watchlists', {
      fund_code: fundCode,
      fund_name: fundName
    });
    return response.data;
  }

  /**
   * Remove a fund from watchlist.
   */
  async removeFromWatchlist(fundCode: string): Promise<void> {
    await this.client.delete(`/watchlists/${fundCode}`);
  }

  /**
   * Check if a fund is in watchlist.
   */
  async checkWatchlist(fundCode: string): Promise<boolean> {
    try {
      await this.client.get(`/watchlists/${fundCode}`);
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Helper function to convert FundEstimation to a simplified ValuationResult-like object
 * for displaying basic estimation information without holdings contribution details.
 */
export function convertEstimationToValuationDisplay(estimation: FundEstimation): {
  fund_code: string;
  fund_name?: string;
  estimated_nav: number;
  estimated_change_percent: number;
  last_time?: string;
  data_count: number;
  date: number;
} | null {
  if (!estimation.data || estimation.data.length === 0) {
    return null;
  }

  const latest = estimation.data[estimation.data.length - 1];
  return {
    fund_code: estimation.code,
    fund_name: estimation.name,
    estimated_nav: latest.nav,
    estimated_change_percent: latest.growth,
    last_time: estimation.last_time || latest.time,
    data_count: estimation.count,
    date: estimation.date
  };
}

export const api = new ApiService();
export default api;
