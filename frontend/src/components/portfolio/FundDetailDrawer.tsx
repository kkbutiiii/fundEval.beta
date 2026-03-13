/**
 * Drawer component for showing fund details and transaction history.
 */
import React, { useState } from 'react';
import {
  Drawer,
  Space,
  Button,
  Typography,
  Descriptions,
  Divider,
} from 'antd';
import {
  ShoppingCartOutlined,
  MoneyCollectOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { TransactionHistory } from './TransactionHistory';
import type { PortfolioFund } from '../../types';

const { Text, Title } = Typography;

interface FundDetailDrawerProps {
  visible: boolean;
  fund: PortfolioFund | null;
  portfolioId: string;
  onClose: () => void;
  onBuy: () => void;
  onSell: () => void;
}

export const FundDetailDrawer: React.FC<FundDetailDrawerProps> = ({
  visible,
  fund,
  portfolioId,
  onClose,
  onBuy,
  onSell,
}) => {
  // State to trigger refresh of transaction history
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const formatCurrency = (value: number | undefined) => {
    if (value === undefined || isNaN(value)) return '-';
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatNumber = (value: number | undefined, digits: number = 4) => {
    if (value === undefined || isNaN(value)) return '-';
    return value.toFixed(digits);
  };

  const formatPercent = (value: number | undefined) => {
    if (value === undefined || isNaN(value)) return '-';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getGrowthColor = (value: number | undefined) => {
    if (value === undefined) return 'inherit';
    return value >= 0 ? '#cf1322' : '#3f8600';
  };

  if (!fund) return null;

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Title level={5} style={{ margin: 0 }}>
              {fund.fund_name}
            </Title>
            <Text type="secondary">{fund.fund_code}</Text>
          </div>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            size="small"
            title="刷新交易记录"
          />
        </div>
      }
      placement="right"
      width={560}
      open={visible}
      onClose={onClose}
    >
      {/* Current Position Summary */}
      <Descriptions column={2} size="small" bordered>
        <Descriptions.Item label="当前份额">
          <Text strong>{formatNumber(fund.shares, 4)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="估算市值">
          <Text strong>{formatCurrency(fund.estimated_value)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="最新市值">
          {formatCurrency(fund.latest_value)}
        </Descriptions.Item>
        <Descriptions.Item label="最新净值">
          {formatNumber(fund.latest_nav, 4)}
        </Descriptions.Item>
        <Descriptions.Item label="估算净值">
          {formatNumber(fund.estimated_nav, 4)}
        </Descriptions.Item>
        <Descriptions.Item label="最新涨跌">
          <Text style={{ color: getGrowthColor(fund.latest_growth) }}>
            {formatPercent(fund.latest_growth)}
          </Text>
        </Descriptions.Item>
      </Descriptions>

      {/* Action Buttons */}
      <div style={{ marginTop: 24, marginBottom: 24 }}>
        <Space>
          <Button
            type="primary"
            icon={<ShoppingCartOutlined />}
            onClick={onBuy}
          >
            买入
          </Button>
          <Button
            icon={<MoneyCollectOutlined />}
            onClick={onSell}
            danger
          >
            卖出
          </Button>
        </Space>
      </div>

      <Divider />

      {/* Transaction History */}
      <div>
        <Title level={5}>交易记录</Title>
        <TransactionHistory
          key={refreshKey}
          portfolioId={portfolioId}
          fundCode={fund.fund_code}
          fundName={fund.fund_name}
        />
      </div>
    </Drawer>
  );
};

export default FundDetailDrawer;
