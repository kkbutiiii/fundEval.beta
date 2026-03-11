/**
 * Hook for managing watchlist funds with localStorage persistence and real-time updates.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import type { FundInfo, EstimationSummary } from '../types';

const WATCHLIST_STORAGE_KEY = 'fund_watchlist_v1';
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
  addToWatchlist: (fund: FundInfo) => void;
  removeFromWatchlist: (fundCode: string) => void;
  currentFundCode: string | null;
  setCurrentFundCode: (code: string) => void;
  isLoading: boolean;
  lastUpdate: Date | null;
  refresh: () => Promise<void>;
}

/**
 * Load watchlist from localStorage
 */
function loadWatchlistFromStorage(): WatchlistFund[] {
  try {
    const stored = localStorage.getItem(WATCHLIST_STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Failed to load watchlist from localStorage:', error);
  }
  return [];
}

/**
 * Save watchlist to localStorage
 */
function saveWatchlistToStorage(watchlist: WatchlistFund[]): void {
  try {
    localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(watchlist));
  } catch (error) {
    console.error('Failed to save watchlist to localStorage:', error);
  }
}

export function useWatchlist(): UseWatchlistReturn {
  const [watchlist, setWatchlist] = useState<WatchlistFund[]>([]);
  const [watchlistWithRealtime, setWatchlistWithRealtime] = useState<WatchlistFundWithRealtime[]>([]);
  const [currentFundCode, setCurrentFundCode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load watchlist from localStorage on mount
  useEffect(() => {
    const stored = loadWatchlistFromStorage();
    setWatchlist(stored);
    // Set first fund as current if exists and no current selected
    if (stored.length > 0 && !currentFundCode) {
      setCurrentFundCode(stored[0].fund_code);
    }
  }, []);

  // Check if a fund is in watchlist
  const isInWatchlist = useCallback((fundCode: string): boolean => {
    return watchlist.some(f => f.fund_code === fundCode);
  }, [watchlist]);

  // Add fund to watchlist
  const addToWatchlist = useCallback((fund: FundInfo) => {
    setWatchlist(prev => {
      if (prev.some(f => f.fund_code === fund.fund_code)) {
        return prev; // Already exists
      }
      const newItem: WatchlistFund = {
        fund_code: fund.fund_code,
        fund_name: fund.fund_name,
        added_at: Date.now(),
      };
      const newWatchlist = [...prev, newItem];
      saveWatchlistToStorage(newWatchlist);
      return newWatchlist;
    });
  }, []);

  // Remove fund from watchlist
  const removeFromWatchlist = useCallback((fundCode: string) => {
    setWatchlist(prev => {
      const newWatchlist = prev.filter(f => f.fund_code !== fundCode);
      saveWatchlistToStorage(newWatchlist);
      return newWatchlist;
    });
    // If current fund is removed, select another one
    if (currentFundCode === fundCode) {
      const remaining = watchlist.filter(f => f.fund_code !== fundCode);
      setCurrentFundCode(remaining.length > 0 ? remaining[0].fund_code : null);
    }
  }, [currentFundCode, watchlist]);

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
          return {
            ...fund,
            fund_name: estimation.name || fund.fund_name,
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
