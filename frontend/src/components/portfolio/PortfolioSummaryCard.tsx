/**
 * Summary card component showing portfolio statistics.
 */
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Typography, Statistic, Divider, Tag } from 'antd';
import {
  WalletOutlined,
  RiseOutlined,
  FallOutlined,
  FundOutlined,
} from '@ant-design/icons';
import type { PortfolioFund } from '../../types';
import { api } from '../../services/api';

const { Title, Text } = Typography;

interface PortfolioSummaryCardProps {
  funds: PortfolioFund[];
  portfolioName: string;
  lastUpdate: Date | null;
  portfolioId?: string;
}

const PortfolioSummaryCard: React.FC<PortfolioSummaryCardProps> = ({
  funds,
  portfolioName,
  lastUpdate,
  portfolioId,
}) => {
  // State for historical return rate
  const [historyReturn, setHistoryReturn] = useState<number | null>(null);

  // Fetch portfolio history to get return rate
  useEffect(() => {
    if (portfolioId) {
      api.getPortfolioHistory(portfolioId, 'ytd', 'twr').then((data) => {
        if (data.data?.length) {
          setHistoryReturn(data.data[data.data.length - 1].return_rate);
        }
      });
    }
  }, [portfolioId]);

  // Extract dates from funds
  const dates = React.useMemo(() => {
    const navDates = funds.map((f) => f.nav_date).filter(Boolean) as string[];
    const estimationTimes = funds.map((f) => f.estimation_time).filter(Boolean) as string[];
    return {
      navDate: navDates[0] || '',
      estimationTime: estimationTimes[0] || '',
    };
  }, [funds]);

  // Format date string to MM-DD
  const formatDateLabel = (dateStr: string): string => {
    if (!dateStr) return '';
    // Handle formats like "03/10" or "2025-03-10" or "03/11 15:30"
    const parts = dateStr.split(/[-\/\s]/);
    if (parts.length >= 2) {
      // Get the last two parts (month and day)
      const month = parts[parts.length - 2];
      const day = parts[parts.length - 1];
      return `${month}-${day}`;
    }
    return dateStr;
  };
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

  const formatHistoryReturn = (value: number | null) => {
    if (value === null) return '-';
    return formatPercent(value);
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
        {/* Historical Total Return */}
        {/* <Col xs={24} sm={12} md={6} lg={5}>
          <Statistic
            title="历史总收益"
            value={historyReturn !== null ? historyReturn : 0}
            precision={2}
            formatter={(value) => (
              <span style={{ color: getGrowthColor(Number(value)) }}>
                {Number(value) >= 0 ? <RiseOutlined /> : <FallOutlined />}
                {formatHistoryReturn(historyReturn)}
              </span>
            )}
          />
        </Col> */}
        {/* Estimated Total Value */}
        <Col xs={24} sm={12} md={6} lg={5}>
          <Statistic
            title={
              <span>
                估算总市值
                <Tag style={{ marginLeft: 4, fontSize: 10, lineHeight: '16px', padding: '0 4px', color: '#999', borderColor: '#d9d9d9' }}>
                  估
                </Tag>
              </span>
            }
            value={stats.totalEstimatedValue}
            precision={2}
            formatter={(value) => formatCurrency(Number(value))}
            prefix={<WalletOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        {/* Latest Total Value */}
        <Col xs={24} sm={12} md={6} lg={5}>
          <Statistic
            title={
              <span>
                最新总市值
                {dates.navDate && (
                  <span style={{ color: '#999', fontSize: 12, marginLeft: 4 }}>
                    ({formatDateLabel(dates.navDate)})
                  </span>
                )}
              </span>
            }
            value={stats.totalLatestValue}
            precision={2}
            formatter={(value) => formatCurrency(Number(value))}
            prefix={<WalletOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Col>
        {/* Estimated Growth */}
        <Col xs={24} sm={12} md={6} lg={5}>
          <Statistic
            title={
              <span>
                估算涨跌幅
                <Tag style={{ marginLeft: 4, fontSize: 10, lineHeight: '16px', padding: '0 4px', color: '#999', borderColor: '#d9d9d9' }}>
                  估
                </Tag>
              </span>
            }
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
        {/* Latest Growth */}
        <Col xs={24} sm={12} md={6} lg={4}>
          <Statistic
            title={
              <span>
                最新涨跌幅
                {dates.navDate && (
                  <span style={{ color: '#999', fontSize: 12, marginLeft: 4 }}>
                    ({formatDateLabel(dates.navDate)})
                  </span>
                )}
              </span>
            }
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
