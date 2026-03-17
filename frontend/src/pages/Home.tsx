/**
 * Home page with fund search and popular funds.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Typography, Card, Row, Col, Tag } from 'antd';
import { FundOutlined, RiseOutlined, WalletOutlined, StarOutlined } from '@ant-design/icons';
import FundSearch from '../components/FundSearch';
import api from '../services/api';
import type { FundInfo, EstimationSummary } from '../types';

const { Title, Text } = Typography;
const { Content } = Layout;

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [popularFunds, setPopularFunds] = useState<FundInfo[]>([]);
  const [popularValuations, setPopularValuations] = useState<Record<string, EstimationSummary>>({});
  const [loading, setLoading] = useState(true);

  // Popular fund codes (some well-known funds)
  const popularFundCodes = ['000001', '005827', '161725', '110022', '003096', '005827', '161005'];

  useEffect(() => {
    const loadPopularFunds = async () => {
      try {
        // Get all funds first
        const funds = await api.getAllFunds(500);
        // Filter for popular codes
        const filtered = funds.filter(f => popularFundCodes.includes(f.fund_code));
        setPopularFunds(filtered.slice(0, 8));

        // Load valuations for popular funds using batch API
        const valuations: Record<string, EstimationSummary> = {};
        const codesToFetch = filtered.slice(0, 5).map(f => f.fund_code);
        try {
          const batchResults = await api.getBatchValuation(codesToFetch);
          for (const result of batchResults) {
            valuations[result.code] = result;
          }
        } catch (e) {
          console.error('Failed to load batch valuations', e);
        }
        setPopularValuations(valuations);
      } catch (error) {
        console.error('Failed to load popular funds', error);
      } finally {
        setLoading(false);
      }
    };

    loadPopularFunds();
  }, []);

  const handleFundSelect = (fund: FundInfo) => {
    navigate(`/fund/${fund.fund_code}`);
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Content style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 24px' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <Title level={1} style={{ marginBottom: 16 }}>
            <FundOutlined style={{ marginRight: 12 }} />
            华福资管-基金实时估值平台
          </Title>
          <Text type="secondary" style={{ fontSize: 16 }}>
            {/* 基于最新季报持仓数据，实时估算基金净值 */}
          </Text>
        </div>

        {/* Search Box */}
        <Card style={{ marginBottom: 48, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
          <Title level={4} style={{ marginBottom: 16 }}>
            搜索基金
          </Title>
          <FundSearch
            onSelect={handleFundSelect}
            placeholder="输入基金代码或名称（如：000001 或 华夏成长）"
          />
        </Card>

        {/* Quick Access Cards */}
        <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
          <Col xs={24} md={12}>
            <Card
              style={{ cursor: 'pointer', background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)' }}
              onClick={() => navigate('/portfolio')}
              hoverable
            >
              <div style={{ display: 'flex', alignItems: 'center', color: '#fff' }}>
                <WalletOutlined style={{ fontSize: 48, marginRight: 24 }} />
                <div>
                  <Title level={3} style={{ color: '#fff', margin: 0 }}>
                    基金组合管理
                  </Title>
                  <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14 }}>
                    创建基金组合，录入交易，追踪组合实时收益
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card
              style={{ cursor: 'pointer', background: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)' }}
              onClick={() => navigate('/watchlist')}
              hoverable
            >
              <div style={{ display: 'flex', alignItems: 'center', color: '#fff' }}>
                <StarOutlined style={{ fontSize: 48, marginRight: 24 }} />
                <div>
                  <Title level={3} style={{ color: '#fff', margin: 0 }}>
                    自选监控
                  </Title>
                  <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14 }}>
                    关注感兴趣的基金，实时查看估算净值和涨跌
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
        </Row>

        {/* Popular Funds */}
        <Card
          title={
            <span>
              <RiseOutlined style={{ marginRight: 8 }} />
              热门基金
            </span>
          }
          loading={loading}
        >
          <Row gutter={[16, 16]}>
            {popularFunds.map((fund) => {
              const valuation = popularValuations[fund.fund_code];
              return (
                <Col xs={24} sm={12} md={8} key={fund.fund_code}>
                  <Card
                    size="small"
                    hoverable
                    onClick={() => handleFundSelect(fund)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <Text strong style={{ fontSize: 16 }}>{fund.fund_name}</Text>
                        <br />
                        <Text type="secondary">{fund.fund_code}</Text>
                      </div>
                      {valuation && (
                        <Tag
                          color={(valuation.latest_growth || 0) >= 0 ? 'red' : 'green'}
                          style={{ fontSize: 14 }}
                        >
                          {(valuation.latest_growth || 0) >= 0 ? '+' : ''}
                          {(valuation.latest_growth || 0).toFixed(2)}%
                        </Tag>
                      )}
                    </div>
                    {fund.fund_type && (
                      <Tag style={{ marginTop: 8, fontSize: 12 }}>{fund.fund_type}</Tag>
                    )}
                  </Card>
                </Col>
              );
            })}
          </Row>
        </Card>

        {/* Features */}
        {/* <Row gutter={[24, 24]} style={{ marginTop: 48 }}>
          <Col xs={24} md={8}>
            <Card>
              <Title level={4}>实时估算</Title>
              <Text type="secondary">
                基于实时股票行情，结合基金重仓股数据，秒级更新估值结果
              </Text>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Title level={4}>数据准确</Title>
              <Text type="secondary">
                使用官方披露的季报持仓数据，支持多种补全策略
              </Text>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card>
              <Title level={4}>免费开源</Title>
              <Text type="secondary">
                完全免费使用，数据源来自东方财富和AKShare
              </Text>
            </Card>
          </Col>
        </Row> */}
      </Content>
    </Layout>
  );
};

export default Home;
