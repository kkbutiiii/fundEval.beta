/**
 * Hook for real-time portfolio fund valuation updates.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import type { FundPortfolio, PortfolioFund, EstimationSummary, FundInfo } from '../types';

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

      // Fetch both batch valuation and fund info in parallel
      const [results, fundInfos] = await Promise.all([
        api.getBatchValuation(fundCodes),
        Promise.all(
          portfolio.funds.map(fund =>
            api.getFundInfo(fund.fund_code).catch(() => null)
          )
        ),
      ]);

      // Create maps for quick lookup
      const estimationMap = new Map<string, EstimationSummary>();
      for (const result of results) {
        estimationMap.set(result.code, result);
      }

      const fundInfoMap = new Map<string, FundInfo>();
      for (const info of fundInfos) {
        if (info) {
          fundInfoMap.set(info.fund_code, info);
        }
      }

      // Merge realtime data with portfolio funds
      const mergedFunds: PortfolioFund[] = portfolio.funds.map(fund => {
        const estimation = estimationMap.get(fund.fund_code);
        const fundInfo = fundInfoMap.get(fund.fund_code);

        if (estimation || fundInfo) {
          // Use FundInfo for latest_nav/latest_growth, fallback to estimation
          const latestNav = fundInfo?.nav ?? estimation?.latest_nav ?? fund.latest_nav;
          const latestGrowth = fundInfo?.nav_change_percent ?? estimation?.latest_growth ?? fund.latest_growth;

          return {
            ...fund,
            fund_name: fundInfo?.fund_name ?? estimation?.name ?? fund.fund_name,
            estimated_nav: estimation?.latest_nav,
            estimated_growth: estimation?.latest_growth,
            // Use FundInfo nav data for latest values
            latest_nav: latestNav,
            latest_growth: latestGrowth,
            nav_date: fundInfo?.nav_date,
            // Calculate values
            estimated_value: fund.shares * (estimation?.latest_nav || 0),
            latest_value: fund.shares * (latestNav || 0),
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

  // Clear data immediately when portfolio changes, then fetch new data
  useEffect(() => {
    // Clear previous data immediately to avoid showing stale data
    setFundsWithRealtime([]);
    setLastUpdate(null);
    fetchRealtimeData();
  }, [fetchRealtimeData, portfolio?.id]);

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
