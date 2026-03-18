/**
 * Auth Modal - Login/Register modal for landing page
 * Glassmorphism design with tab switching
 */
import React, { useState } from 'react';
import { Modal, Form, Input, Button, Tabs, Alert, Typography } from 'antd';
import { UserOutlined, LockOutlined, FundOutlined } from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';

const { Text } = Typography;

interface AuthModalProps {
  visible: boolean;
  onClose: () => void;
  defaultTab?: 'login' | 'register';
  onSuccess?: () => void;
}

interface LoginFormValues {
  username: string;
  password: string;
}

const AuthModal: React.FC<AuthModalProps> = ({
  visible,
  onClose,
  defaultTab = 'login',
  onSuccess,
}) => {
  const { login, register } = useAuth();
  const [activeTab, setActiveTab] = useState<string>(defaultTab);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();

  const handleLogin = async (values: LoginFormValues) => {
    setError(null);
    setLoading(true);

    try {
      await login(values.username, values.password);
      onSuccess?.();
      onClose();
      loginForm.resetFields();
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: LoginFormValues & { confirmPassword: string }) => {
    setError(null);
    setLoading(true);

    try {
      await register(values.username, values.password);
      onSuccess?.();
      onClose();
      registerForm.resetFields();
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError(null);
    loginForm.resetFields();
    registerForm.resetFields();
    onClose();
  };

  const loginItems = [
    {
      key: 'login',
      label: '登录',
      children: (
        <div>
          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
              style={{ marginBottom: 16 }}
            />
          )}
          <Form
            form={loginForm}
            name="login"
            onFinish={handleLogin}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input
                prefix={<UserOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="用户名"
                autoFocus
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="密码"
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                style={{ borderRadius: 8 }}
              >
                登录
              </Button>
            </Form.Item>
          </Form>
        </div>
      ),
    },
    {
      key: 'register',
      label: '注册',
      children: (
        <div>
          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
              style={{ marginBottom: 16 }}
            />
          )}
          <Form
            form={registerForm}
            name="register"
            onFinish={handleRegister}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input
                prefix={<UserOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="用户名"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="密码"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              dependencies={['password']}
              rules={[
                { required: true, message: '请确认密码' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(new Error('两次输入的密码不一致'));
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined style={{ color: '#bfbfbf' }} />}
                placeholder="确认密码"
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                style={{ borderRadius: 8 }}
              >
                注册
              </Button>
            </Form.Item>
          </Form>
        </div>
      ),
    },
  ];

  return (
    <Modal
      open={visible}
      onCancel={handleClose}
      footer={null}
      width={720}
      centered
      className="auth-modal"
      closable={false}
      maskClosable={!loading}
    >
      <div className="auth-modal-content">
        {/* Left side - Brand */}
        <div className="auth-modal-brand">
          <FundOutlined className="auth-modal-logo" />
          <h3 className="auth-modal-title">FundEval.Beta</h3>
          <p className="auth-modal-desc">
            基金实时估值平台
            <br />
            基于最新季报持仓数据，实时估算基金净值
          </p>
        </div>

        {/* Right side - Form */}
        <div className="auth-modal-form">
          <Tabs
            items={loginItems}
            activeKey={activeTab}
            onChange={setActiveTab}
            centered
            className="auth-modal-tabs"
          />
          <Text type="secondary" style={{ textAlign: 'center', display: 'block', marginTop: 16 }}>
            {activeTab === 'login' ? '还没有账号？点击上方"注册"' : '已有账号？点击上方"登录"'}
          </Text>
        </div>
      </div>
    </Modal>
  );
};

export default AuthModal;
