/**
 * Hook for real-time portfolio fund valuation updates.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import type { FundPortfolio, PortfolioFund, EstimationSummary } from '../types';

const REFRESH_INTERVAL = 30000; // 30 seconds

export interface UsePortfolioRealtimeReturn {
  fundsWithRealtime: PortfolioFund[];
  isLoading: boolean;
  lastUpdate: Date | null;
  error: string | null;
  refresh: () => Promise<void>;
}

export function usePortfolioRealtime(
  portfolio: FundPortfolio | null
): UsePortfolioRealtimeReturn {
  const [fundsWithRealtime, setFundsWithRealtime] = useState<PortfolioFund[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchRealtimeData = useCallback(async () => {
    if (!portfolio || portfolio.funds.length === 0) {
      setFundsWithRealtime([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const fundCodes = portfolio.funds.map(f => f.fund_code);
      const results = await api.getBatchValuation(fundCodes);

      // Create a map for quick lookup
      const estimationMap = new Map<string, EstimationSummary>();
      for (const result of results) {
        estimationMap.set(result.code, result);
      }

      // Merge realtime data with portfolio funds
      const mergedFunds: PortfolioFund[] = portfolio.funds.map(fund => {
        const estimation = estimationMap.get(fund.fund_code);
        if (estimation) {
          return {
            ...fund,
            fund_name: estimation.name || fund.fund_name,
            estimated_nav: estimation.latest_nav,
            estimated_growth: estimation.latest_growth,
            // For latest_nav and latest_growth, we'll use the same data
            // In a real scenario, these might come from a different endpoint
            latest_nav: estimation.latest_nav,
            latest_growth: estimation.latest_growth,
            // Calculate values
            estimated_value: fund.shares * (estimation.latest_nav || 0),
            latest_value: fund.shares * (estimation.latest_nav || 0),
          };
        }
        return {
          ...fund,
          estimated_value: fund.shares * (fund.estimated_nav || 0),
          latest_value: fund.shares * (fund.latest_nav || 0),
        };
      });

      setFundsWithRealtime(mergedFunds);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch realtime data');
      console.error('Failed to fetch realtime data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [portfolio]);

  // Initial fetch and when portfolio changes
  useEffect(() => {
    fetchRealtimeData();
  }, [fetchRealtimeData]);

  // Set up interval for auto-refresh
  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = setInterval(() => {
      fetchRealtimeData();
    }, REFRESH_INTERVAL);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchRealtimeData]);

  return {
    fundsWithRealtime,
    isLoading,
    lastUpdate,
    error,
    refresh: fetchRealtimeData,
  };
}
