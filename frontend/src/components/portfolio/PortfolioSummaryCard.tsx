/**
 * Summary card component showing portfolio statistics.
 */
import React from 'react';
import { Card, Row, Col, Typography, Statistic, Divider } from 'antd';
import {
  WalletOutlined,
  RiseOutlined,
  FallOutlined,
  FundOutlined,
} from '@ant-design/icons';
import type { PortfolioFund } from '../../types';

const { Title, Text } = Typography;

interface PortfolioSummaryCardProps {
  funds: PortfolioFund[];
  portfolioName: string;
  lastUpdate: Date | null;
}

const PortfolioSummaryCard: React.FC<PortfolioSummaryCardProps> = ({
  funds,
  portfolioName,
  lastUpdate,
}) => {
  // Calculate portfolio statistics
  const stats = React.useMemo(() => {
    if (funds.length === 0) {
      return {
        totalEstimatedValue: 0,
        totalLatestValue: 0,
        totalEstimatedGrowth: 0,
        totalLatestGrowth: 0,
        fundCount: 0,
      };
    }

    const totalEstimatedValue = funds.reduce((sum, f) => sum + (f.estimated_value || 0), 0);
    const totalLatestValue = funds.reduce((sum, f) => sum + (f.latest_value || 0), 0);

    // Calculate weighted growth
    const totalEstimatedGrowth = totalEstimatedValue > 0
      ? funds.reduce((sum, f) => {
          const weight = (f.estimated_value || 0) / totalEstimatedValue;
          return sum + (f.estimated_growth || 0) * weight;
        }, 0)
      : 0;

    const totalLatestGrowth = totalLatestValue > 0
      ? funds.reduce((sum, f) => {
          const weight = (f.latest_value || 0) / totalLatestValue;
          return sum + (f.latest_growth || 0) * weight;
        }, 0)
      : 0;

    return {
      totalEstimatedValue,
      totalLatestValue,
      totalEstimatedGrowth,
      totalLatestGrowth,
      fundCount: funds.length,
    };
  }, [funds]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getGrowthColor = (value: number) => {
    // Chinese stock market convention: red = up, green = down
    return value >= 0 ? '#cf1322' : '#3f8600';
  };

  return (
    <Card style={{ marginBottom: 24 }}>
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          <FundOutlined style={{ marginRight: 8 }} />
          {portfolioName}
        </Title>
        {lastUpdate && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            更新时间: {lastUpdate.toLocaleString('zh-CN')}
          </Text>
        )}
      </div>

      <Row gutter={[24, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="估算总市值"
            value={stats.totalEstimatedValue}
            precision={2}
            formatter={(value) => formatCurrency(Number(value))}
            prefix={<WalletOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="最新总市值"
            value={stats.totalLatestValue}
            precision={2}
            formatter={(value) => formatCurrency(Number(value))}
            prefix={<WalletOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="估算涨跌幅"
            value={stats.totalEstimatedGrowth}
            precision={2}
            formatter={(value) => (
              <span style={{ color: getGrowthColor(Number(value)) }}>
                {Number(value) >= 0 ? <RiseOutlined /> : <FallOutlined />}
                {formatPercent(Number(value))}
              </span>
            )}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Statistic
            title="最新涨跌幅"
            value={stats.totalLatestGrowth}
            precision={2}
            formatter={(value) => (
              <span style={{ color: getGrowthColor(Number(value)) }}>
                {Number(value) >= 0 ? <RiseOutlined /> : <FallOutlined />}
                {formatPercent(Number(value))}
              </span>
            )}
          />
        </Col>
      </Row>

      <Divider style={{ margin: '16px 0' }} />

      <Text type="secondary">
        共持有 <Text strong>{stats.fundCount}</Text> 只基金
      </Text>
    </Card>
  );
};

export default PortfolioSummaryCard;
