/**
 * Fund valuation display component.
 */
import React from 'react';
import { Card, Statistic, Row, Col, Tag, Divider, Alert, Table, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined } from '@ant-design/icons';
import type { ValuationResult, HoldingContribution } from '../types';

const { Text, Title } = Typography;

interface ValuationDisplayProps {
  valuation: ValuationResult;
  loading?: boolean;
}

const ValuationDisplay: React.FC<ValuationDisplayProps> = ({ valuation, loading }) => {
  const isPositive = valuation.estimated_change_percent >= 0;
  const isNeutral = valuation.estimated_change_percent === 0;

  const color = isNeutral ? '#666' : isPositive ? '#cf1322' : '#3f8600';
  const icon = isNeutral ? null : isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />;

  const columns = [
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 120,
    },
    {
      title: '持仓占比',
      dataIndex: 'weight',
      key: 'weight',
      width: 100,
      render: (value: number) => `${value.toFixed(2)}%`,
    },
    {
      title: '涨跌幅',
      dataIndex: 'change_percent',
      key: 'change_percent',
      width: 100,
      render: (value: number) => (
        <Tag color={value > 0 ? 'red' : value < 0 ? 'green' : 'default'}>
          {value > 0 ? '+' : ''}{value.toFixed(2)}%
        </Tag>
      ),
    },
    {
      title: '贡献度',
      dataIndex: 'contribution',
      key: 'contribution',
      width: 100,
      render: (value: number) => (
        <Tag color={value > 0 ? 'red' : value < 0 ? 'green' : 'default'}>
          {value > 0 ? '+' : ''}{value.toFixed(3)}%
        </Tag>
      ),
    },
  ];

  return (
    <Card loading={loading} title="实时估值" bordered={false}>
      {/* Main Valuation Display */}
      <Row gutter={24} justify="center" style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} style={{ textAlign: 'center' }}>
          <Statistic
            title="估算净值"
            value={valuation.estimated_nav}
            precision={4}
            valueStyle={{ color, fontSize: '36px', fontWeight: 'bold' }}
            prefix={icon}
          />
        </Col>
        <Col xs={24} sm={12} style={{ textAlign: 'center' }}>
          <Statistic
            title="估算涨跌幅"
            value={valuation.estimated_change_percent}
            precision={2}
            valueStyle={{ color, fontSize: '36px', fontWeight: 'bold' }}
            suffix="%"
            prefix={icon}
          />
        </Col>
      </Row>

      {/* Latest Official NAV */}
      {valuation.latest_nav && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Text type="secondary">
              最新净值: <strong>{valuation.latest_nav.toFixed(4)}</strong>
              {valuation.nav_date && ` (${valuation.nav_date})`}
            </Text>
          </Col>
        </Row>
      )}

      <Divider />

      {/* Contribution Breakdown */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card size="small" title="重仓股贡献">
            <Tag color={valuation.top10_contribution >= 0 ? 'red' : 'green'}>
              {valuation.top10_contribution >= 0 ? '+' : ''}
              {valuation.top10_contribution.toFixed(2)}%
            </Tag>
            <Text type="secondary" style={{ marginLeft: 8 }}>
              占比 {valuation.top10_weight.toFixed(1)}%
            </Text>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" title="剩余仓位贡献">
            <Tag color={valuation.remaining_contribution >= 0 ? 'red' : 'green'}>
              {valuation.remaining_contribution >= 0 ? '+' : ''}
              {valuation.remaining_contribution.toFixed(2)}%
            </Tag>
            <Text type="secondary" style={{ marginLeft: 8 }}>
              占比 {valuation.remaining_weight.toFixed(1)}%
            </Text>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" title="补全方法">
            <Text>{valuation.completion_method || valuation.completion_index || '无'}</Text>
          </Card>
        </Col>
      </Row>

      <Divider />

      {/* Holdings Table */}
      <Title level={5}>重仓股明细</Title>
      <Table
        dataSource={valuation.holdings_details}
        columns={columns}
        rowKey="stock_code"
        size="small"
        pagination={false}
        scroll={{ x: 'max-content' }}
      />

      <Divider />

      {/* Data Source Info */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={24}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            数据来源: {valuation.data_source} |
            持仓报告期: {valuation.report_date || '未知'} |
            计算时间: {new Date(valuation.calculation_time).toLocaleString()}
          </Text>
        </Col>
      </Row>

      {/* Disclaimer */}
      <Alert
        message={valuation.disclaimer}
        type="warning"
        showIcon
        icon={<InfoCircleOutlined />}
        style={{ marginTop: 16 }}
      />
    </Card>
  );
};

export default ValuationDisplay;
