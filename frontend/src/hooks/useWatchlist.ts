/**
 * Hook for managing watchlist funds with backend API persistence and real-time updates.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import type { FundInfo, EstimationSummary } from '../types';

const REFRESH_INTERVAL = 30000; // 30 seconds

export interface WatchlistFund {
  fund_code: string;
  fund_name: string;
  added_at: number;  // Timestamp when added
}

export interface WatchlistFundWithRealtime extends WatchlistFund {
  estimated_nav?: number;
  estimated_growth?: number;
  previous_nav?: number;
}

export interface UseWatchlistReturn {
  watchlist: WatchlistFund[];
  watchlistWithRealtime: WatchlistFundWithRealtime[];
  isInWatchlist: (fundCode: string) => boolean;
  addToWatchlist: (fund: FundInfo) => Promise<void>;
  removeFromWatchlist: (fundCode: string) => Promise<void>;
  currentFundCode: string | null;
  setCurrentFundCode: (code: string) => void;
  isLoading: boolean;
  lastUpdate: Date | null;
  refresh: () => Promise<void>;
}

export function useWatchlist(): UseWatchlistReturn {
  const [watchlist, setWatchlist] = useState<WatchlistFund[]>([]);
  const [watchlistWithRealtime, setWatchlistWithRealtime] = useState<WatchlistFundWithRealtime[]>([]);
  const [currentFundCode, setCurrentFundCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const initialFetchDone = useRef(false);

  // Load watchlist from backend API on mount
  const fetchWatchlist = useCallback(async () => {
    try {
      const data = await api.getWatchlist();
      const formatted = data.map(item => ({
        fund_code: item.fund_code,
        fund_name: item.fund_name,
        added_at: new Date(item.added_at).getTime()
      }));
      setWatchlist(formatted);
      // Set first fund as current if exists and no current selected
      if (formatted.length > 0 && !currentFundCode) {
        setCurrentFundCode(formatted[0].fund_code);
      }
    } catch (err) {
      console.error('Failed to fetch watchlist:', err);
    }
  }, [currentFundCode]);

  useEffect(() => {
    if (!initialFetchDone.current) {
      initialFetchDone.current = true;
      fetchWatchlist();
    }
  }, [fetchWatchlist]);

  // Check if a fund is in watchlist
  const isInWatchlist = useCallback((fundCode: string): boolean => {
    return watchlist.some(f => f.fund_code === fundCode);
  }, [watchlist]);

  // Add fund to watchlist
  const addToWatchlist = useCallback(async (fund: FundInfo) => {
    if (watchlist.some(f => f.fund_code === fund.fund_code)) {
      return; // Already exists
    }

    try {
      await api.addToWatchlist(fund.fund_code, fund.fund_name);
      // Refresh watchlist from backend
      await fetchWatchlist();
    } catch (err) {
      console.error('Failed to add to watchlist:', err);
      throw err;
    }
  }, [watchlist, fetchWatchlist]);

  // Remove fund from watchlist
  const removeFromWatchlist = useCallback(async (fundCode: string) => {
    try {
      await api.removeFromWatchlist(fundCode);
      setWatchlist(prev => {
        const newWatchlist = prev.filter(f => f.fund_code !== fundCode);
        // If current fund is removed, select another one
        if (currentFundCode === fundCode) {
          const remaining = newWatchlist;
          setCurrentFundCode(remaining.length > 0 ? remaining[0].fund_code : null);
        }
        return newWatchlist;
      });
    } catch (err) {
      console.error('Failed to remove from watchlist:', err);
      throw err;
    }
  }, [currentFundCode]);

  // Fetch real-time data for all watchlist funds
  const fetchRealtimeData = useCallback(async () => {
    if (watchlist.length === 0) {
      setWatchlistWithRealtime([]);
      return;
    }

    setIsLoading(true);
    try {
      const fundCodes = watchlist.map(f => f.fund_code);
      const results = await api.getBatchValuation(fundCodes);

      // Create a map for quick lookup with normalized fund codes
      const estimationMap = new Map<string, EstimationSummary>();
      for (const result of results) {
        // Normalize fund code as key (trim whitespace, uppercase)
        const normalizedCode = result.code.trim().toUpperCase();
        estimationMap.set(normalizedCode, result);
      }

      // Merge realtime data with watchlist funds
      const mergedFunds: WatchlistFundWithRealtime[] = watchlist.map(fund => {
        // Normalize watchlist fund code for lookup
        const normalizedFundCode = fund.fund_code.trim().toUpperCase();
        const estimation = estimationMap.get(normalizedFundCode);
        if (estimation) {
          // Only use estimation.name if it's different from fund_code (avoid showing code twice)
          const estimationName = estimation.name && estimation.name !== fund.fund_code
            ? estimation.name
            : fund.fund_name;
          return {
            ...fund,
            fund_name: estimationName,
            estimated_nav: estimation.latest_nav,
            estimated_growth: estimation.latest_growth,
            previous_nav: estimation.previous_nav,
          };
        }
        return fund;
      });

      setWatchlistWithRealtime(mergedFunds);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to fetch realtime data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [watchlist]);

  // Initial fetch and when watchlist changes
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
    watchlist,
    watchlistWithRealtime,
    isInWatchlist,
    addToWatchlist,
    removeFromWatchlist,
    currentFundCode,
    setCurrentFundCode,
    isLoading,
    lastUpdate,
    refresh: fetchRealtimeData,
  };
}
