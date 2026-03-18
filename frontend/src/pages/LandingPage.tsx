/**
 * Landing Page - High-end tech-style landing page
 * Parallel with existing Home.tsx, accessible at /landing
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, Typography, FloatButton, Dropdown, Modal, Form, Input, message } from 'antd';
import {
  LoginOutlined,
  UserOutlined,
  ArrowUpOutlined,
  LogoutOutlined,
  LockOutlined,
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
  const location = useLocation();
  const { isAuthenticated, user, logout, changePassword } = useAuth();
  const [authModalVisible, setAuthModalVisible] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<'login' | 'register'>('login');
  const [redirectPath, setRedirectPath] = useState<string | null>(null);
  const [scrolled, setScrolled] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [passwordForm] = Form.useForm();
  const [passwordLoading, setPasswordLoading] = useState(false);

  // Check if redirected from protected route
  useEffect(() => {
    const fromPath = location.state?.from?.pathname;
    if (fromPath && !isAuthenticated) {
      setRedirectPath(fromPath);
      setAuthModalTab('login');
      setAuthModalVisible(true);
      // Clear location state after processing
      window.history.replaceState({}, document.title);
    }
  }, [location.state, isAuthenticated]);

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
          <img
            src="/1726038425446-logo.png"
            alt="FundEval.Beta"
            style={{
              height: 40,
              width: 'auto',
              borderRadius: 8,
            }}
          />
          <span
            style={{
              fontSize: 20,
              fontWeight: 700,
              color: scrolled ? '#1f1f1f' : '#1f1f1f',
            }}
          >
            FundEval.Beta
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {isAuthenticated ? (
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
                    onClick: () => setPasswordModalVisible(true),
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
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '4px 12px',
                  background: 'rgba(24, 144, 255, 0.1)',
                  borderRadius: 20,
                  cursor: 'pointer',
                }}
              >
                <UserOutlined style={{ color: '#1890ff' }} />
                <Text strong style={{ color: '#1890ff' }}>
                  {user?.username}
                </Text>
              </div>
            </Dropdown>
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

      {/* Change Password Modal */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onOk={() => passwordForm.submit()}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        confirmLoading={passwordLoading}
        okText="确认修改"
        cancelText="取消"
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={async (values) => {
            setPasswordLoading(true);
            try {
              await changePassword(values.currentPassword, values.newPassword);
              message.success('密码修改成功');
              setPasswordModalVisible(false);
              passwordForm.resetFields();
            } catch (error) {
              message.error(error instanceof Error ? error.message : '密码修改失败');
            } finally {
              setPasswordLoading(false);
            }
          }}
        >
          <Form.Item
            label="当前密码"
            name="currentPassword"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password placeholder="请输入当前密码" />
          </Form.Item>
          <Form.Item
            label="新密码"
            name="newPassword"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '新密码长度至少为6位' },
            ]}
          >
            <Input.Password placeholder="请输入新密码（至少6位）" />
          </Form.Item>
          <Form.Item
            label="确认新密码"
            name="confirmPassword"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default LandingPage;
