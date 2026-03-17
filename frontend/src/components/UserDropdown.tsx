/**
 * User dropdown component for the header.
 */
import React from 'react';
import { Dropdown, Button, Space, Typography } from 'antd';
import { UserOutlined, LogoutOutlined, DownOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const { Text } = Typography;

const UserDropdown: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const items = [
    {
      key: 'username',
      label: (
        <Space>
          <UserOutlined />
          <Text strong>{user?.username}</Text>
        </Space>
      ),
      disabled: true,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      label: (
        <Space onClick={handleLogout} style={{ cursor: 'pointer' }}>
          <LogoutOutlined />
          <Text>退出登录</Text>
        </Space>
      ),
    },
  ];

  return (
    <Dropdown menu={{ items }} placement="bottomRight">
      <Button type="text">
        <Space>
          <UserOutlined />
          <Text>{user?.username}</Text>
          <DownOutlined style={{ fontSize: 12 }} />
        </Space>
      </Button>
    </Dropdown>
  );
};

export default UserDropdown;
