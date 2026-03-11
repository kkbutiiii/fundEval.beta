/**
 * Convertible Bond Holdings Table Component
 * Displays convertible bond holdings
 */
import React from 'react';
import { Table, Typography, Empty, Tag } from 'antd';
import type { ConvertibleHolding } from '../types';

const { Text } = Typography;

interface ConvertibleHoldingsTableProps {
  holdings: ConvertibleHolding[];
  totalWeight: number;
  loading?: boolean;
}

export const ConvertibleHoldingsTable: React.FC<ConvertibleHoldingsTableProps> = ({
  holdings,
  totalWeight,
  loading
}) => {
  const columns = [
    {
      title: '转债代码',
      dataIndex: 'bond_code',
      key: 'bond_code',
      width: 80,
    },
    {
      title: '转债名称',
      dataIndex: 'bond_name',
      key: 'bond_name',
      width: 120,
    },
    {
      title: '持仓占比',
      dataIndex: 'weight',
      key: 'weight',
      width: 80,
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
      width: 110,
      render: (value?: number) => {
        if (value === undefined || value === null) return '-';
        return `¥${value.toFixed(2)}万元`;
      },
    },
  ];

  if (!holdings || holdings.length === 0) {
    return (
      <Empty
        description="暂无可转债持仓数据"
        style={{ padding: 40 }}
      />
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 8, fontSize: 12, color: '#666' }}>
        可转债总占比: <strong>{totalWeight.toFixed(2)}%</strong>
      </div>
      <Table
        dataSource={holdings}
        columns={columns}
        rowKey="bond_code"
        size="small"
        pagination={false}
        loading={loading}
        scroll={{ x: 'max-content' }}
      />
    </div>
  );
};

export default ConvertibleHoldingsTable;
