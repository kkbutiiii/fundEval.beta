/**
 * Fund Detail Page V2 - Light Tech Style
 * Glassmorphism design consistent with landing page
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Typography, Button, Spin, Alert, Row, Col, Tabs, Table, Space, Tag } from 'antd';
import { ReloadOutlined, InfoCircleOutlined, StarFilled, StarOutlined } from '@ant-design/icons';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import GlassCard from '../components/dashboard/GlassCard';
import AssetAllocationCard from '../components/AssetAllocationCard';
import BondHoldingsTable from '../components/BondHoldingsTable';
import ConvertibleHoldingsTable from '../components/ConvertibleHoldingsTable';
import NavHistoryChart from '../components/NavHistoryChart';
import IntradayValuationChart from '../components/IntradayValuationChart';
import api from '../services/api';
import { useWatchlist } from '../hooks/useWatchlist';
import type { FundInfo, Fund } from '../types';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const FundDetailV2: React.FC = () => {
  const { fundCode } = useParams<{ fundCode: string }>();

  const [fundInfo, setFundInfo] = useState<FundInfo | null>(null);
  const [fundHoldings, setFundHoldings] = useState<Fund | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { isInWatchlist, addToWatchlist, removeFromWatchlist } = useWatchlist();

  const loadData = useCallback(async (forceRefresh: boolean = false) => {
    if (!fundCode) return;

    setLoading(true);
    setError(null);

    try {
      const info = await api.getFundInfo(fundCode).catch(() => null);
      if (info) setFundInfo(info);

      api.getFundHoldings(fundCode, forceRefresh)
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

  const stockColumns = [
    { title: '股票代码', dataIndex: 'stock_code', key: 'stock_code', width: 80 },
    { title: '股票简称', dataIndex: 'stock_name', key: 'stock_name', width: 100 },
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

  if (loading) {
    return (
      <DashboardLayout title="基金详情" showBackButton={true}>
        <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="基金详情" showBackButton={true}>
      <div className="dash-fade-in">
        {/* Fund Header Card */}
        <GlassCard style={{ marginBottom: 24 }} hoverable={false}>
          {/* Fund Name and Actions */}
          <Row justify="space-between" align="middle" style={{ marginBottom: 20 }}>
            <Col>
              <Title level={3} style={{ margin: 0 }}>
                {fundInfo?.fund_name || fundHoldings?.fund_name || fundCode}
              </Title>
              <Text type="secondary">{fundCode}</Text>
            </Col>
            <Col>
              <Space>
                {fundInfo && (
                  <Button
                    icon={isInWatchlist(fundCode!) ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
                    onClick={() => {
                      if (isInWatchlist(fundCode!)) {
                        removeFromWatchlist(fundCode!);
                      } else {
                        addToWatchlist(fundInfo);
                      }
                    }}
                    style={{ borderRadius: 8 }}
                  >
                    {isInWatchlist(fundCode!) ? '从自选移除' : '加入自选'}
                  </Button>
                )}
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={() => loadData(true)}
                  loading={loading}
                  style={{
                    background: 'linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)',
                    border: 'none',
                    borderRadius: 8,
                  }}
                >
                  强制刷新
                </Button>
              </Space>
            </Col>
          </Row>

          {/* Main Content: Left (NAV + Returns) | Right (Info Panel) */}
          <Row gutter={[24, 24]}>
            {/* Left Side: NAV and Returns */}
            <Col xs={24} lg={12}>
              {/* NAV Section */}
              <div style={{ marginBottom: 16 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  单位净值 ({fundInfo?.nav_date || '--'})
                </Text>
                <div>
                  <Text strong style={{ fontSize: 36, marginRight: 8 }}>
                    {fundInfo?.nav?.toFixed(4) || '--'}
                  </Text>
                  {fundInfo?.nav_change_percent !== undefined && fundInfo.nav_change_percent !== null && (
                    <Tag
                      color={fundInfo.nav_change_percent >= 0 ? '#cf1322' : '#3f8600'}
                      style={{ fontSize: 14, padding: '2px 8px' }}
                    >
                      {fundInfo.nav_change_percent >= 0 ? '+' : ''}
                      {fundInfo.nav_change_percent.toFixed(2)}%
                    </Tag>
                  )}
                </div>
                {fundInfo?.accumulated_nav !== undefined && fundInfo.accumulated_nav !== null && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    累计净值: {fundInfo.accumulated_nav.toFixed(4)}
                  </Text>
                )}
              </div>

              {/* Returns Grid */}
              <Row gutter={[16, 8]}>
                {[
                  { label: '近1月', value: fundInfo?.return_1m },
                  { label: '近3月', value: fundInfo?.return_3m },
                  { label: '近6月', value: fundInfo?.return_6m },
                  { label: '近1年', value: fundInfo?.return_1y },
                  { label: '近3年', value: fundInfo?.return_3y },
                  { label: '成立来', value: fundInfo?.return_since_inception },
                ].map((item) => (
                  <Col span={8} key={item.label}>
                    <div
                      style={{
                        background: 'rgba(24, 144, 255, 0.05)',
                        borderRadius: 8,
                        padding: '8px 12px',
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: 11, color: '#999', marginBottom: 4 }}>{item.label}</div>
                      <div
                        style={{
                          fontSize: 14,
                          fontWeight: 600,
                          color: item.value === undefined ? '#999' : (item.value ?? 0) >= 0 ? '#cf1322' : '#3f8600',
                        }}
                      >
                        {item.value !== undefined && item.value !== null
                          ? `${(item.value >= 0 ? '+' : '')}${item.value.toFixed(2)}%`
                          : '--'}
                      </div>
                    </div>
                  </Col>
                ))}
              </Row>
            </Col>

            {/* Right Side: Info Panel */}
            <Col xs={24} lg={12}>
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.5)',
                  borderRadius: 12,
                  padding: 16,
                  lineHeight: '28px',
                }}
              >
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text type="secondary" style={{ fontSize: 12 }}>类型: </Text>
                    <Text style={{ fontSize: 12 }}>
                      {fundInfo?.fund_type || '--'}
                      {fundInfo?.risk_level && (
                        <Tag color="orange" style={{ marginLeft: 8, fontSize: 10 }}>
                          {fundInfo.risk_level}
                        </Tag>
                      )}
                    </Text>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary" style={{ fontSize: 12 }}>规模: </Text>
                    <Text style={{ fontSize: 12 }}>
                      {fundInfo?.total_assets ? `${fundInfo.total_assets.toFixed(2)}亿元` : '--'}
                    </Text>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary" style={{ fontSize: 12 }}>成立日: </Text>
                    <Text style={{ fontSize: 12 }}>{fundInfo?.inception_date || '--'}</Text>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary" style={{ fontSize: 12 }}>管理人: </Text>
                    <Text style={{ fontSize: 12 }}>{fundInfo?.company || '--'}</Text>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary" style={{ fontSize: 12 }}>基金经理: </Text>
                    <Text style={{ fontSize: 12 }}>{fundInfo?.manager || '--'}</Text>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary" style={{ fontSize: 12 }}>评级: </Text>
                    {fundInfo?.rating ? (
                      <span>
                        {Array.from({ length: 5 }).map((_, i) =>
                          i < (fundInfo?.rating || 0) ? (
                            <StarFilled key={i} style={{ color: '#faad14', fontSize: 12 }} />
                          ) : (
                            <StarOutlined key={i} style={{ color: '#d9d9d9', fontSize: 12 }} />
                          )
                        )}
                      </span>
                    ) : (
                      <Text style={{ fontSize: 12 }}>暂无评级</Text>
                    )}
                  </Col>
                  {fundInfo?.benchmark && (
                    <Col span={24}>
                      <Text type="secondary" style={{ fontSize: 12 }}>跟踪标的: </Text>
                      <Text style={{ fontSize: 12 }}>{fundInfo.benchmark}</Text>
                    </Col>
                  )}
                </Row>
              </div>
            </Col>
          </Row>
        </GlassCard>

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

        {/* Intraday Valuation Chart and Holdings */}
        <Row gutter={[24, 24]} align="stretch" style={{ marginBottom: 24 }}>
          <Col xs={24} lg={12}>
            <GlassCard style={{ height: 520 }} hoverable={false}>
              <IntradayValuationChart fundCode={fundCode!} />
            </GlassCard>
          </Col>
          <Col xs={24} lg={12}>
            {fundHoldings && (
              <GlassCard style={{ height: 520 }} hoverable={false}>
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
              </GlassCard>
            )}
          </Col>
        </Row>

        {/* NAV History Chart and Asset Allocation */}
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <GlassCard style={{ height: 450 }} hoverable={false}>
              <NavHistoryChart fundCode={fundCode!} />
            </GlassCard>
          </Col>
          <Col xs={24} lg={12}>
            <GlassCard style={{ height: 450 }} hoverable={false}>
              <AssetAllocationCard fundCode={fundCode!} />
            </GlassCard>
          </Col>
        </Row>

        {/* Disclaimer */}
        <Alert
          message="免责声明"
          description="本系统提供的基金估值数据来源于天天基金网官方实时估算，仅供参考，不代表实际净值。基金实际净值以基金公司每日公布为准。由于市场波动和基金经理可能进行的调仓操作，估算值与实际净值可能存在偏差。投资有风险，入市需谨慎。"
          type="warning"
          showIcon
          icon={<InfoCircleOutlined />}
          style={{ marginTop: 24 }}
        />
      </div>
    </DashboardLayout>
  );
};

export default FundDetailV2;
