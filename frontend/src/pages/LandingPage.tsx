/**
 * Landing Page - High-end tech-style landing page
 * Parallel with existing Home.tsx, accessible at /landing
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Typography, FloatButton } from 'antd';
import {
  FundOutlined,
  LoginOutlined,
  UserOutlined,
  HomeOutlined,
  ArrowUpOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import HeroSection from '../components/landing/HeroSection';
import FeatureGrid from '../components/landing/FeatureGrid';
import PreviewShowcase from '../components/landing/PreviewShowcase';
import AuthModal from '../components/landing/AuthModal';
import type { FundInfo } from '../types';
import '../styles/landing.css';

const { Text } = Typography;

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [authModalVisible, setAuthModalVisible] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<'login' | 'register'>('login');
  const [redirectPath, setRedirectPath] = useState<string | null>(null);
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll for navbar styling
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleFundSelect = (fund: FundInfo) => {
    if (isAuthenticated) {
      navigate(`/fund/${fund.fund_code}`);
    } else {
      setRedirectPath(`/fund/${fund.fund_code}`);
      setAuthModalTab('login');
      setAuthModalVisible(true);
    }
  };

  const handleAuthRequired = (path: string) => {
    setRedirectPath(path);
    setAuthModalTab('login');
    setAuthModalVisible(true);
  };

  const handleAuthSuccess = () => {
    if (redirectPath) {
      navigate(redirectPath);
      setRedirectPath(null);
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="landing-page">
      {/* Navigation Bar */}
      <nav
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          padding: '16px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: scrolled ? 'rgba(255, 255, 255, 0.9)' : 'transparent',
          backdropFilter: scrolled ? 'blur(10px)' : 'none',
          borderBottom: scrolled ? '1px solid rgba(0, 0, 0, 0.05)' : 'none',
          transition: 'all 0.3s ease',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            cursor: 'pointer',
          }}
          onClick={scrollToTop}
        >
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: 'linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 20,
            }}
          >
            <FundOutlined />
          </div>
          <span
            style={{
              fontSize: 20,
              fontWeight: 700,
              color: scrolled ? '#1f1f1f' : '#1f1f1f',
            }}
          >
            华福资管
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {isAuthenticated ? (
            <>
              <Button
                type="text"
                icon={<HomeOutlined />}
                onClick={() => navigate('/')}
              >
                进入系统
              </Button>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '4px 12px',
                  background: 'rgba(24, 144, 255, 0.1)',
                  borderRadius: 20,
                }}
              >
                <UserOutlined style={{ color: '#1890ff' }} />
                <Text strong style={{ color: '#1890ff' }}>
                  {user?.username}
                </Text>
              </div>
            </>
          ) : (
            <>
              <Button
                type="text"
                onClick={() => {
                  setAuthModalTab('login');
                  setRedirectPath('/');
                  setAuthModalVisible(true);
                }}
              >
                登录
              </Button>
              <Button
                type="primary"
                icon={<LoginOutlined />}
                onClick={() => {
                  setAuthModalTab('register');
                  setRedirectPath('/');
                  setAuthModalVisible(true);
                }}
                style={{
                  borderRadius: 8,
                  background: 'linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)',
                  border: 'none',
                }}
              >
                免费注册
              </Button>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <HeroSection
        onFundSelect={handleFundSelect}
      />

      {/* Feature Grid */}
      <FeatureGrid
        isAuthenticated={isAuthenticated}
        onAuthRequired={handleAuthRequired}
      />

      {/* Preview Showcase */}
      <PreviewShowcase />

      {/* Stats Section */}
      <section className="stats-section">
        <div className="stats-container">
          <div className="stat-item">
            <div className="stat-number">
              10000<span className="stat-suffix">+</span>
            </div>
            <div className="stat-label">支持基金数量</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">
              99<span className="stat-suffix">%</span>
            </div>
            <div className="stat-label">估值准确率</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">
              3<span className="stat-suffix">秒</span>
            </div>
            <div className="stat-label">数据更新频率</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">
              24<span className="stat-suffix">/7</span>
            </div>
            <div className="stat-label">全天候服务</div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-logo">华福资管</div>
          <p className="footer-text">
            基金实时估值平台 · 基于最新季报持仓数据，实时估算基金净值
            <br />
            © 2024 华福证券资产管理部
          </p>
          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'center', gap: 24 }}>
            <Button type="link" onClick={() => navigate('/')}>
              现有版本首页
            </Button>
            <Button type="link" onClick={() => navigate('/login')}>
              传统登录页面
            </Button>
          </div>
        </div>
      </footer>

      {/* Back to Top Button */}
      <FloatButton
        icon={<ArrowUpOutlined />}
        onClick={scrollToTop}
        style={{ right: 24, bottom: 24 }}
        tooltip="回到顶部"
      />

      {/* Auth Modal */}
      <AuthModal
        visible={authModalVisible}
        onClose={() => {
          setAuthModalVisible(false);
          setRedirectPath(null);
        }}
        defaultTab={authModalTab}
        onSuccess={handleAuthSuccess}
      />
    </div>
  );
};

export default LandingPage;
