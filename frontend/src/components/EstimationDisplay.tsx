/**
 * Official Fund Estimation Display Component
 * Displays real-time estimation data from 天天基金 (TTJJ) official API
 */
import React from 'react';
import { Card, Statistic, Row, Col, Tag, Divider, Alert, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined, LineChartOutlined } from '@ant-design/icons';
import type { FundEstimation, EstimationDataPoint } from '../types';

const { Text, Title } = Typography;

interface EstimationDisplayProps {
  estimation: FundEstimation;
  loading?: boolean;
}

const EstimationDisplay: React.FC<EstimationDisplayProps> = ({ estimation, loading }) => {
  // Get the latest data point
  const latestData: EstimationDataPoint | null = estimation.data && estimation.data.length > 0
    ? estimation.data[estimation.data.length - 1]
    : null;

  if (!latestData) {
    return (
      <Card loading={loading} title="实时估值" bordered={false} style={{ marginTop: 24 }}>
        <Alert
          message="暂无估值数据"
          description="该基金暂时没有实时估值数据，可能处于非交易时间或数据尚未采集。"
          type="info"
          showIcon
        />
      </Card>
    );
  }

  const isPositive = latestData.growth >= 0;
  const isNeutral = latestData.growth === 0;

  // Chinese market color convention: red = up, green = down
  const color = isNeutral ? '#666' : isPositive ? '#cf1322' : '#3f8600';
  const icon = isNeutral ? null : isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />;

  // Format date from YYYYMMDD to YYYY-MM-DD
  const formatDate = (dateNum: number): string => {
    const dateStr = dateNum.toString();
    if (dateStr.length !== 8) return dateStr;
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
  };

  return (
    <Card
      loading={loading}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <LineChartOutlined />
          <span>实时估值</span>
          <Tag color="blue" style={{ fontSize: 12 }}>天天基金官方</Tag>
        </div>
      }
      bordered={false}
      style={{ marginTop: 24 }}
    >
      {/* Main Estimation Display */}
      <Row gutter={24} justify="center" style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} style={{ textAlign: 'center' }}>
          <Statistic
            title="估算净值"
            value={latestData.nav}
            precision={4}
            valueStyle={{ color, fontSize: '36px', fontWeight: 'bold' }}
            prefix={icon}
          />
        </Col>
        <Col xs={24} sm={12} style={{ textAlign: 'center' }}>
          <Statistic
            title="估算涨跌幅"
            value={latestData.growth}
            precision={2}
            valueStyle={{ color, fontSize: '36px', fontWeight: 'bold' }}
            suffix="%"
            prefix={icon}
          />
        </Col>
      </Row>

      <Divider />

      {/* Data Info */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={8}>
          <Card size="small" title="估值日期">
            <Text strong>{formatDate(estimation.date)}</Text>
          </Card>
        </Col>
        <Col xs={12} sm={8}>
          <Card size="small" title="最新估值时间">
            <Text strong>{latestData.time}</Text>
          </Card>
        </Col>
        <Col xs={12} sm={8}>
          <Card size="small" title="日内数据点">
            <Text strong>{estimation.count} 个</Text>
            <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
              ({estimation.first_time} - {estimation.last_time})
            </Text>
          </Card>
        </Col>
      </Row>

      {/* Valuation History Table */}
      {estimation.data.length > 0 && (
        <>
          <Divider />
          <Title level={5}>日内估值记录</Title>
          <div style={{ maxHeight: '200px', overflow: 'auto' }}>
            <table style={{ width: '100%', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <th style={{ textAlign: 'left', padding: '8px' }}>时间</th>
                  <th style={{ textAlign: 'right', padding: '8px' }}>估算净值</th>
                  <th style={{ textAlign: 'right', padding: '8px' }}>涨跌幅</th>
                </tr>
              </thead>
              <tbody>
                {[...estimation.data].reverse().slice(0, 10).map((item, index) => (
                  <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '8px' }}>{item.time}</td>
                    <td style={{ textAlign: 'right', padding: '8px' }}>{item.nav.toFixed(4)}</td>
                    <td style={{ textAlign: 'right', padding: '8px' }}>
                      <Tag color={item.growth >= 0 ? 'red' : 'green'} style={{ fontSize: 12 }}>
                        {item.growth >= 0 ? '+' : ''}{item.growth.toFixed(2)}%
                      </Tag>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {estimation.data.length > 10 && (
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
              显示最近 10 条记录，共 {estimation.data.length} 条
            </Text>
          )}
        </>
      )}

      <Divider />

      {/* Data Source Info */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={24}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            数据来源: 天天基金网 ( Eastmoney ) 官方估算 |
            基金代码: {estimation.code}
            {estimation.name && ` | ${estimation.name}`}
          </Text>
        </Col>
      </Row>

      {/* Disclaimer */}
      <Alert
        message="免责声明"
        description="本估值数据来源于天天基金网官方实时估算，仅供参考，不代表实际净值。基金实际净值以基金公司每日公布为准。投资有风险，入市需谨慎。"
        type="warning"
        showIcon
        icon={<InfoCircleOutlined />}
        style={{ marginTop: 16 }}
      />
    </Card>
  );
};

export default EstimationDisplay;
