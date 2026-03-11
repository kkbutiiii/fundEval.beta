/**
 * Hook for managing portfolio data with backend API persistence.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import type { FundPortfolio, PortfolioFund } from '../types';

export interface UsePortfoliosReturn {
  portfolios: FundPortfolio[];
  currentPortfolio: FundPortfolio | null;
  setCurrentPortfolio: (portfolio: FundPortfolio | null) => void;
  createPortfolio: (name: string) => Promise<FundPortfolio>;
  updatePortfolio: (portfolio: FundPortfolio) => Promise<void>;
  deletePortfolio: (id: string) => Promise<void>;
  addFundToPortfolio: (portfolioId: string, fund: PortfolioFund) => Promise<void>;
  removeFundFromPortfolio: (portfolioId: string, fundCode: string) => Promise<void>;
  updateFundShares: (portfolioId: string, fundCode: string, shares: number) => Promise<void>;
  batchAddFunds: (portfolioId: string, funds: PortfolioFund[]) => Promise<void>;
  refresh: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

export function usePortfolios(): UsePortfoliosReturn {
  const [portfolios, setPortfolios] = useState<FundPortfolio[]>([]);
  const [currentPortfolio, setCurrentPortfolioState] = useState<FundPortfolio | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Use ref to track current portfolio ID for async operations
  const currentPortfolioRef = useRef(currentPortfolio);
  currentPortfolioRef.current = currentPortfolio;

  // Load portfolios from API on mount
  useEffect(() => {
    if (!initialized) {
      refresh();
      setInitialized(true);
    }
  }, [initialized]);

  // Refresh portfolios from API
  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPortfolios();
      setPortfolios(data);

      // Update current portfolio if it exists in the new data
      if (currentPortfolioRef.current) {
        const updated = data.find(p => p.id === currentPortfolioRef.current?.id);
        if (updated) {
          setCurrentPortfolioState(updated);
        } else if (data.length > 0) {
          setCurrentPortfolioState(data[0]);
        } else {
          setCurrentPortfolioState(null);
        }
      } else if (data.length > 0) {
        setCurrentPortfolioState(data[0]);
      }
    } catch (err) {
      setError('Failed to load portfolios');
      console.error('Failed to load portfolios:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const setCurrentPortfolio = useCallback((portfolio: FundPortfolio | null) => {
    setCurrentPortfolioState(portfolio);
  }, []);

  const createPortfolio = useCallback(async (name: string): Promise<FundPortfolio> => {
    setLoading(true);
    setError(null);
    try {
      const newPortfolio = await api.createPortfolio(name);
      setPortfolios(prev => [...prev, newPortfolio]);
      setCurrentPortfolioState(newPortfolio);
      return newPortfolio;
    } catch (err) {
      setError('Failed to create portfolio');
      console.error('Failed to create portfolio:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updatePortfolio = useCallback(async (portfolio: FundPortfolio) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await api.updatePortfolio(portfolio.id, portfolio.name);
      setPortfolios(prev =>
        prev.map(p => (p.id === updated.id ? updated : p))
      );
      if (currentPortfolioRef.current?.id === updated.id) {
        setCurrentPortfolioState(updated);
      }
    } catch (err) {
      setError('Failed to update portfolio');
      console.error('Failed to update portfolio:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deletePortfolio = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await api.deletePortfolio(id);
      setPortfolios(prev => prev.filter(p => p.id !== id));
      if (currentPortfolioRef.current?.id === id) {
        const remaining = portfolios.filter(p => p.id !== id);
        setCurrentPortfolioState(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (err) {
      setError('Failed to delete portfolio');
      console.error('Failed to delete portfolio:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [portfolios]);

  const addFundToPortfolio = useCallback(async (portfolioId: string, fund: PortfolioFund) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await api.addFundToPortfolio(portfolioId, {
        fund_code: fund.fund_code,
        fund_name: fund.fund_name,
        shares: fund.shares,
      });
      setPortfolios(prev =>
        prev.map(p => (p.id === portfolioId ? updated : p))
      );
      if (currentPortfolioRef.current?.id === portfolioId) {
        setCurrentPortfolioState(updated);
      }
    } catch (err) {
      setError('Failed to add fund to portfolio');
      console.error('Failed to add fund to portfolio:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const removeFundFromPortfolio = useCallback(async (portfolioId: string, fundCode: string) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await api.removeFundFromPortfolio(portfolioId, fundCode);
      setPortfolios(prev =>
        prev.map(p => (p.id === portfolioId ? updated : p))
      );
      if (currentPortfolioRef.current?.id === portfolioId) {
        setCurrentPortfolioState(updated);
      }
    } catch (err) {
      setError('Failed to remove fund from portfolio');
      console.error('Failed to remove fund from portfolio:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateFundShares = useCallback(async (portfolioId: string, fundCode: string, shares: number) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await api.updateFundShares(portfolioId, fundCode, shares);
      setPortfolios(prev =>
        prev.map(p => (p.id === portfolioId ? updated : p))
      );
      if (currentPortfolioRef.current?.id === portfolioId) {
        setCurrentPortfolioState(updated);
      }
    } catch (err) {
      setError('Failed to update fund shares');
      console.error('Failed to update fund shares:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const batchAddFunds = useCallback(async (portfolioId: string, funds: PortfolioFund[]) => {
    setLoading(true);
    setError(null);
    try {
      await api.batchAddFunds(
        portfolioId,
        funds.map(f => ({
          fund_code: f.fund_code,
          fund_name: f.fund_name,
          shares: f.shares,
        }))
      );
      // Refresh to get updated portfolio
      const updated = await api.getPortfolio(portfolioId);
      setPortfolios(prev =>
        prev.map(p => (p.id === portfolioId ? updated : p))
      );
      if (currentPortfolioRef.current?.id === portfolioId) {
        setCurrentPortfolioState(updated);
      }
    } catch (err) {
      setError('Failed to batch add funds');
      console.error('Failed to batch add funds:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    portfolios,
    currentPortfolio,
    setCurrentPortfolio,
    createPortfolio,
    updatePortfolio,
    deletePortfolio,
    addFundToPortfolio,
    removeFundFromPortfolio,
    updateFundShares,
    batchAddFunds,
    refresh,
    loading,
    error,
  };
}
