/**
 * Unified Dashboard Layout Component
 * Glassmorphism navbar with scroll effect, consistent with landing page
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dropdown, Typography, Button } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  LockOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
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

const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  showBackButton = true,
  backPath = '/',
  title,
  sidebar,
  sidebarWidth = 260,
}) => {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);

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
        <div className="dash-navbar-logo" onClick={scrollToTop}>
          <img
            src="/1726038425446-logo.png"
            alt="华福资管"
          />
          <span className="dash-navbar-title">华福资管</span>
          {title && (
            <>
              <span style={{ color: '#d9d9d9', margin: '0 8px' }}>|</span>
              <span style={{ fontSize: 16, fontWeight: 500, color: '#666' }}>
                {title}
              </span>
            </>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
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
