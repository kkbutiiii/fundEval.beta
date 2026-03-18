/**
 * Unified Dashboard Layout Component
 * Glassmorphism navbar with scroll effect, consistent with landing page
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { Dropdown, Typography, Button, AutoComplete, Input, Spin } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  LockOutlined,
  ArrowLeftOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import type { FundInfo } from '../../types';
import '../../styles/unified-dashboard.css';

const { Text } = Typography;

interface DashboardLayoutProps {
  children: React.ReactNode;
  showBackButton?: boolean;
  backPath?: string;
  title?: string;
  sidebar?: React.ReactNode;
  sidebarWidth?: number;
}

interface SearchOption {
  value: string;
  label: React.ReactNode;
  fund: FundInfo;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  showBackButton = true,
  backPath = '/',
  title,
  sidebar,
  sidebarWidth = 260,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);

  // Search state
  const [searchOptions, setSearchOptions] = useState<SearchOption[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const searchTimeout = useRef<NodeJS.Timeout | null>(null);

  // Handle scroll for navbar styling
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Determine current page for navigation highlighting
  const isPortfolioPage = location.pathname === '/portfolio';
  const isWatchlistPage = location.pathname === '/watchlist';

  // Handle fund search
  const handleSearch = useCallback(async (value: string) => {
    if (!value || value.length < 2) {
      setSearchOptions([]);
      return;
    }

    // Debounce search
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }

    searchTimeout.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const funds = await api.searchFunds(value, 20);
        const newOptions: SearchOption[] = funds.map((fund) => ({
          value: fund.fund_code,
          label: (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>
                <strong>{fund.fund_code}</strong> - {fund.fund_name}
              </span>
              {fund.fund_type && (
                <span style={{ color: '#999', fontSize: '12px' }}>{fund.fund_type}</span>
              )}
            </div>
          ),
          fund,
        }));
        setSearchOptions(newOptions);
      } catch (error) {
        console.error('Search error:', error);
        setSearchOptions([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);
  }, []);

  // Handle fund selection
  const handleSelect = useCallback((value: string, option: SearchOption) => {
    navigate(`/fund/${option.fund.fund_code}`);
    setSearchOptions([]);
  }, [navigate]);

  return (
    <div className="dashboard-page">
      {/* Grid Background */}
      <div className="dash-grid-bg" />

      {/* Navigation Bar */}
      <nav
        className={`dash-navbar ${scrolled ? 'scrolled' : ''}`}
        style={{
          left: sidebar ? sidebarWidth : 0,
        }}
      >
        {/* Left Section: Logo + Navigation + Search */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 32, flex: 1 }}>
          <div className="dash-navbar-logo" onClick={scrollToTop}>
            <img
              src="/1726038425446-logo.png"
              alt="FundEval.Beta"
            />
            <span className="dash-navbar-title">FundEval.Beta</span>
          </div>

          {/* Navigation Links */}
          <div className="dash-navbar-nav">
            <Link
              to="/portfolio"
              className={`dash-navbar-nav-item ${isPortfolioPage ? 'active' : ''}`}
            >
              基金组合管理
            </Link>
            <Link
              to="/watchlist"
              className={`dash-navbar-nav-item ${isWatchlistPage ? 'active' : ''}`}
            >
              自选监控
            </Link>
          </div>

          {/* Search Box */}
          <div className="dash-navbar-search">
            <AutoComplete
              options={searchOptions}
              onSearch={handleSearch}
              onSelect={handleSelect}
              style={{ width: 480 }}
              notFoundContent={searchLoading ? <Spin size="small" /> : '无搜索结果'}
            >
              <Input
                size="middle"
                placeholder="搜索基金代码或名称"
                prefix={<SearchOutlined style={{ color: '#999' }} />}
                suffix={searchLoading && <Spin size="small" />}
              />
            </AutoComplete>
          </div>
        </div>

        {/* Right Section: User */}
        <div className="dash-navbar-right">

          {isAuthenticated && user && (
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'user',
                    label: user?.username,
                    disabled: true,
                    icon: <UserOutlined />,
                  },
                  { type: 'divider' as const },
                  {
                    key: 'changePassword',
                    label: '修改密码',
                    icon: <LockOutlined />,
                    onClick: () => {
                      // Navigate to profile or show modal
                      // For now, we can just show a message
                    },
                  },
                  {
                    key: 'logout',
                    label: '退出登录',
                    icon: <LogoutOutlined />,
                    onClick: logout,
                  },
                ],
              }}
              placement="bottomRight"
            >
              <div className="dash-navbar-user">
                <UserOutlined style={{ color: '#1890ff' }} />
                <Text strong style={{ color: '#1890ff' }}>
                  {user?.username}
                </Text>
              </div>
            </Dropdown>
          )}
        </div>
      </nav>

      {/* Sidebar */}
      {sidebar && (
        <div
          style={{
            position: 'fixed',
            left: 0,
            top: 0,
            bottom: 0,
            width: sidebarWidth,
            zIndex: 99,
          }}
        >
          {sidebar}
        </div>
      )}

      {/* Main Content */}
      <main
        className="dash-content"
        style={{
          marginLeft: sidebar ? sidebarWidth : 0,
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Back Button */}
        {showBackButton && (
          <div style={{ marginBottom: 16 }}>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(backPath)}
              style={{ borderRadius: 8 }}
            >
              返回首页
            </Button>
          </div>
        )}

        {children}
      </main>
    </div>
  );
};

export default DashboardLayout;
