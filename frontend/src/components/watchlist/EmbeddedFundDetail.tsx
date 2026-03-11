/**
 * Embedded fund detail for watchlist page.
 * Reuses logic from FundDetail but without full page layout.
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Typography, Button, Spin, Alert, Row, Col, Tabs, Table, Space
} from 'antd';
import { ReloadOutlined, StarFilled, StarOutlined } from '@ant-design/icons';
import AssetAllocationCard from '../AssetAllocationCard';
import BondHoldingsTable from '../BondHoldingsTable';
import ConvertibleHoldingsTable from '../ConvertibleHoldingsTable';
import NavHistoryChart from '../NavHistoryChart';
import IntradayValuationChart from '../IntradayValuationChart';
import api from '../../services/api';
import type { FundInfo, Fund } from '../../types';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface EmbeddedFundDetailProps {
  fundCode: string;
  isInWatchlist: boolean;
  onAddToWatchlist: () => void;
  onRemoveFromWatchlist: () => void;
}

const EmbeddedFundDetail: React.FC<EmbeddedFundDetailProps> = ({
  fundCode,
  isInWatchlist,
  onAddToWatchlist,
  onRemoveFromWatchlist,
}) => {
  const [fundInfo, setFundInfo] = useState<FundInfo | null>(null);
  const [fundHoldings, setFundHoldings] = useState<Fund | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!fundCode) return;

    setLoading(true);
    setError(null);

    try {
      // Step 1: Load fund info first (fast - <1s)
      const info = await api.getFundInfo(fundCode).catch(() => null);
      if (info) setFundInfo(info);

      // Step 2: Load holdings (slow - 30s+)
      api.getFundHoldings(fundCode)
        .then((holdingsData) => {
          if (holdingsData) setFundHoldings(holdingsData);
        })
        .catch(() => {
          setError('无法获取持仓数据');
        })
        .finally(() => {
          setLoading(false);
        });
    } catch (e) {
      setError('加载基金数据失败');
      setLoading(false);
    }
  }, [fundCode]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Stock holdings columns
  const stockColumns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 80,
    },
    {
      title: '股票简称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 100,
    },
    {
      title: '占净值比例',
      dataIndex: 'weight',
      key: 'weight',
      width: 90,
      render: (value: number) => `${value.toFixed(2)}%`,
    },
    {
      title: '实时涨跌幅',
      dataIndex: 'change_percent',
      key: 'change_percent',
      width: 90,
      render: (value?: number) => {
        if (value === undefined || value === null) return '-';
        const color = value >= 0 ? '#cf1322' : '#3f8600';
        return (
          <span style={{ color }}>
            {value >= 0 ? '+' : ''}{value.toFixed(2)}%
          </span>
        );
      },
    },
    {
      title: '持仓市值',
      dataIndex: 'market_value',
      key: 'market_value',
      width: 120,
      render: (value?: number) => {
        if (value === undefined || value === null) return '-';
        return `¥${value.toFixed(2)}万元`;
      },
    },
  ];

  if (loading && !fundInfo) {
    return (
      <div style={{ padding: '100px 0', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      {/* Fund Header */}
      <Card style={{ marginBottom: 24 }}>
        {/* Fund Name and Action Buttons */}
        <Row justify="space-between" align="middle" style={{ marginBottom: 20 }}>
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              {fundInfo?.fund_name || fundHoldings?.fund_name || fundCode}
            </Title>
            <Text type="secondary">{fundCode}</Text>
          </Col>
          <Col>
            <Space>
              <Button
                icon={isInWatchlist ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
                onClick={isInWatchlist ? onRemoveFromWatchlist : onAddToWatchlist}
              >
                {isInWatchlist ? '从自选移除' : '加入自选'}
              </Button>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={loadData}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>

        {/* Main Content: Left (NAV + Returns) | Right (Info Panel) */}
        <Row gutter={24}>
          {/* Left Side: NAV and Returns */}
          <Col xs={24} lg={12}>
            {/* NAV Section */}
            <div style={{ marginBottom: 12 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                单位净值 ({fundInfo?.nav_date || '--'})
              </Text>
              <div>
                <Text strong style={{ fontSize: 32, marginRight: 8 }}>
                  {fundInfo?.nav?.toFixed(4) || '--'}
                </Text>
                {fundInfo?.nav_change_percent !== undefined && fundInfo.nav_change_percent !== null && (
                  <Text strong style={{
                    fontSize: 16,
                    color: fundInfo.nav_change_percent >= 0 ? '#cf1322' : '#3f8600'
                  }}>
                    {fundInfo.nav_change_percent >= 0 ? '+' : ''}
                    {fundInfo.nav_change_percent.toFixed(2)}%
                  </Text>
                )}
              </div>
              {fundInfo?.accumulated_nav !== undefined && fundInfo.accumulated_nav !== null && (
                <Text type="secondary" style={{ fontSize: 11 }}>
                  累计净值: {fundInfo.accumulated_nav.toFixed(4)}
                </Text>
              )}
            </div>

            {/* Returns Grid - 3 columns x 2 rows */}
            <Row gutter={[24, 4]}>
              <Col span={8}>
                <Text type="secondary" style={{ fontSize: 11 }}>近1月:</Text>
                <Text strong style={{
                  fontSize: 13,
                  color: (fundInfo?.return_1m ?? 0) >= 0 ? '#cf1322' : '#3f8600',
                  marginLeft: 4
                }}>
                  {fundInfo?.return_1m !== undefined && fundInfo.return_1m !== null
                    ? `${(fundInfo.return_1m >= 0 ? '+' : '')}${fundInfo.return_1m.toFixed(2)}%`
                    : '--'}
                </Text>
              </Col>
              <Col span={8}>
                <Text type="secondary" style={{ fontSize: 11 }}>近3月:</Text>
                <Text strong style={{
                  fontSize: 13,
                  color: (fundInfo?.return_3m ?? 0) >= 0 ? '#cf1322' : '#3f8600',
                  marginLeft: 4
                }}>
                  {fundInfo?.return_3m !== undefined && fundInfo.return_3m !== null
                    ? `${(fundInfo.return_3m >= 0 ? '+' : '')}${fundInfo.return_3m.toFixed(2)}%`
                    : '--'}
                </Text>
              </Col>
              <Col span={8}>
                <Text type="secondary" style={{ fontSize: 11 }}>近6月:</Text>
                <Text strong style={{
                  fontSize: 13,
                  color: (fundInfo?.return_6m ?? 0) >= 0 ? '#cf1322' : '#3f8600',
                  marginLeft: 4
                }}>
                  {fundInfo?.return_6m !== undefined && fundInfo.return_6m !== null
                    ? `${(fundInfo.return_6m >= 0 ? '+' : '')}${fundInfo.return_6m.toFixed(2)}%`
                    : '--'}
                </Text>
              </Col>
              <Col span={8}>
                <Text type="secondary" style={{ fontSize: 11 }}>近1年:</Text>
                <Text strong style={{
                  fontSize: 13,
                  color: (fundInfo?.return_1y ?? 0) >= 0 ? '#cf1322' : '#3f8600',
                  marginLeft: 4
                }}>
                  {fundInfo?.return_1y !== undefined && fundInfo.return_1y !== null
                    ? `${(fundInfo.return_1y >= 0 ? '+' : '')}${fundInfo.return_1y.toFixed(2)}%`
                    : '--'}
                </Text>
              </Col>
              <Col span={8}>
                <Text type="secondary" style={{ fontSize: 11 }}>近3年:</Text>
                <Text strong style={{
                  fontSize: 13,
                  color: (fundInfo?.return_3y ?? 0) >= 0 ? '#cf1322' : '#3f8600',
                  marginLeft: 4
                }}>
                  {fundInfo?.return_3y !== undefined && fundInfo.return_3y !== null
                    ? `${(fundInfo.return_3y >= 0 ? '+' : '')}${fundInfo.return_3y.toFixed(2)}%`
                    : '--'}
                </Text>
              </Col>
              <Col span={8}>
                <Text type="secondary" style={{ fontSize: 11 }}>成立来:</Text>
                <Text strong style={{
                  fontSize: 13,
                  color: (fundInfo?.return_since_inception ?? 0) >= 0 ? '#cf1322' : '#3f8600',
                  marginLeft: 4
                }}>
                  {fundInfo?.return_since_inception !== undefined && fundInfo.return_since_inception !== null
                    ? `${(fundInfo.return_since_inception >= 0 ? '+' : '')}${fundInfo.return_since_inception.toFixed(2)}%`
                    : '--'}
                </Text>
              </Col>
            </Row>
          </Col>

          {/* Right Side: Info Panel */}
          <Col xs={24} lg={12}>
            <div style={{ lineHeight: '22px' }}>
              {/* Type & Risk Level */}
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>类型: </Text>
                <Text style={{ fontSize: 12 }}>
                  {fundInfo?.fund_type || '--'}
                  {fundInfo?.risk_level && (
                    <>
                      <span style={{ margin: '0 6px', color: '#d9d9d9' }}>|</span>
                      <span style={{ color: '#ff4d4f' }}>{fundInfo.risk_level}</span>
                    </>
                  )}
                </Text>
              </div>

              {/* Scale */}
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>规模: </Text>
                <Text style={{ fontSize: 12 }}>
                  {fundInfo?.total_assets ? `${fundInfo.total_assets.toFixed(2)}亿元` : '--'}
                  {fundInfo?.nav_date && (
                    <Text type="secondary" style={{ fontSize: 11 }}> ({fundInfo.nav_date})</Text>
                  )}
                </Text>
              </div>

              {/* Inception Date */}
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>成立日: </Text>
                <Text style={{ fontSize: 12 }}>{fundInfo?.inception_date || '--'}</Text>
              </div>

              {/* Company */}
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>管理人: </Text>
                <Text style={{ fontSize: 12 }}>{fundInfo?.company || '--'}</Text>
              </div>

              {/* Manager */}
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>基金经理: </Text>
                <Text style={{ fontSize: 12 }}>{fundInfo?.manager || '--'}</Text>
              </div>

              {/* Rating */}
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>基金评级: </Text>
                {fundInfo?.rating ? (
                  <span>
                    {Array.from({ length: 5 }).map((_, i) => (
                      i < (fundInfo?.rating || 0) ? (
                        <StarFilled key={i} style={{ color: '#faad14', fontSize: 12 }} />
                      ) : (
                        <StarOutlined key={i} style={{ color: '#d9d9d9', fontSize: 12 }} />
                      )
                    ))}
                  </span>
                ) : (
                  <Text style={{ fontSize: 12 }}>暂无评级</Text>
                )}
              </div>

              {/* Benchmark */}
              {fundInfo?.benchmark && (
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>跟踪标的: </Text>
                  <Text style={{ fontSize: 12 }}>{fundInfo.benchmark}</Text>
                </div>
              )}
            </div>
          </Col>
        </Row>
      </Card>

      {/* Error Message */}
      {error && (
        <Alert
          message="持仓数据加载失败"
          description={error}
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Intraday Valuation Chart and Holdings Side by Side */}
      <Row gutter={24} align="stretch" style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <div style={{ height: 520 }}>
            <IntradayValuationChart fundCode={fundCode} />
          </div>
        </Col>
        <Col xs={24} lg={12}>
          {fundHoldings && (
            <Card
              title={
                <span>
                  持仓明细
                  {fundHoldings.report_date && (
                    <span style={{ fontSize: 12, fontWeight: 'normal', marginLeft: 8, color: '#999' }}>
                      数据依据：{fundHoldings.report_date}四季报
                    </span>
                  )}
                </span>
              }
              style={{ height: 520 }}
              bodyStyle={{ padding: '12px 24px 24px', height: 'calc(100% - 57px)', overflow: 'hidden' }}
            >
              <Tabs defaultActiveKey="stocks" size="small" style={{ height: '100%' }}>
                <TabPane
                  tab={`重仓股 (${fundHoldings.top10_holdings?.length || 0})`}
                  key="stocks"
                >
                  <div style={{ marginBottom: 8, fontSize: 12, color: '#666' }}>
                    股票仓位: <strong>{fundHoldings.total_stock_ratio?.toFixed(2) || 'N/A'}%</strong>
                    <span style={{ marginLeft: 16 }}>
                      前十大重仓股占比: <strong>{fundHoldings.top10_total_weight?.toFixed(2) || 'N/A'}%</strong>
                    </span>
                  </div>
                  <Table
                    dataSource={fundHoldings.top10_holdings || []}
                    columns={stockColumns}
                    rowKey="stock_code"
                    size="small"
                    pagination={false}
                    scroll={{ x: 'max-content', y: 360 }}
                  />
                </TabPane>

                <TabPane
                  tab={`可转债 (${fundHoldings.convertible_holdings?.length || 0})`}
                  key="convertible"
                >
                  <div style={{ maxHeight: 400, overflow: 'auto' }}>
                    <ConvertibleHoldingsTable
                      holdings={fundHoldings.convertible_holdings || []}
                      totalWeight={fundHoldings.convertible_total_weight || 0}
                    />
                  </div>
                </TabPane>

                <TabPane
                  tab={`债券 (${fundHoldings.bond_holdings?.length || 0})`}
                  key="bonds"
                >
                  <div style={{ maxHeight: 400, overflow: 'auto' }}>
                    <BondHoldingsTable
                      holdings={fundHoldings.bond_holdings || []}
                      totalWeight={fundHoldings.bond_total_weight || 0}
                    />
                  </div>
                </TabPane>
              </Tabs>
            </Card>
          )}
        </Col>
      </Row>

      {/* NAV History Chart and Asset Allocation Side by Side */}
      <Row gutter={24} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <div style={{ height: 450 }}>
            <NavHistoryChart fundCode={fundCode} />
          </div>
        </Col>
        <Col xs={24} lg={12}>
          <div style={{ height: 450 }}>
            <AssetAllocationCard fundCode={fundCode} />
          </div>
        </Col>
      </Row>
    </div>
  );
};

export default EmbeddedFundDetail;
