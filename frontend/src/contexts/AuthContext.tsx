/**
 * Authentication context for managing user authentication state.
 */
import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

export interface User {
  id: number;
  username: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const TOKEN_STORAGE_KEY = 'auth_tokens';
const USER_STORAGE_KEY = 'auth_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load auth state from localStorage on mount
  useEffect(() => {
    const storedTokens = localStorage.getItem(TOKEN_STORAGE_KEY);
    const storedUser = localStorage.getItem(USER_STORAGE_KEY);

    if (storedTokens && storedUser) {
      try {
        const tokens: AuthTokens = JSON.parse(storedTokens);
        const userData: User = JSON.parse(storedUser);
        setUser(userData);
      } catch (error) {
        console.error('Failed to parse stored auth data:', error);
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const tokens: AuthTokens = await response.json();
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));

    // Fetch user info
    const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`,
      },
    });

    if (!userResponse.ok) {
      throw new Error('Failed to fetch user info');
    }

    const userData: User = await userResponse.json();
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(userData));
    setUser(userData);
  }, []);

  const register = useCallback(async (username: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    // Auto-login after successful registration
    await login(username, password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    setUser(null);
  }, []);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    const storedTokens = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!storedTokens) {
      return false;
    }

    try {
      const tokens: AuthTokens = JSON.parse(storedTokens);

      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: tokens.refresh_token }),
      });

      if (!response.ok) {
        // Refresh failed, clear auth state
        logout();
        return false;
      }

      const newTokens: AuthTokens = await response.json();
      localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(newTokens));
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      return false;
    }
  }, [logout]);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Helper function to get current access token
export const getAccessToken = (): string | null => {
  const storedTokens = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (!storedTokens) return null;
  try {
    const tokens: AuthTokens = JSON.parse(storedTokens);
    return tokens.access_token;
  } catch {
    return null;
  }
};
