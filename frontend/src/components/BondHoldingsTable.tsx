/**
 * Bond Holdings Table Component
 * Displays bond holdings (excluding convertible bonds)
 */
import React from 'react';
import { Table, Typography, Empty } from 'antd';
import type { BondHolding } from '../types';

const { Text } = Typography;

interface BondHoldingsTableProps {
  holdings: BondHolding[];
  totalWeight: number;
  loading?: boolean;
}

export const BondHoldingsTable: React.FC<BondHoldingsTableProps> = ({
  holdings,
  totalWeight,
  loading
}) => {
  const columns = [
    {
      title: '债券代码',
      dataIndex: 'bond_code',
      key: 'bond_code',
      width: 80,
    },
    {
      title: '债券名称',
      dataIndex: 'bond_name',
      key: 'bond_name',
      width: 150,
    },
    {
      title: '持仓占比',
      dataIndex: 'weight',
      key: 'weight',
      width: 80,
      render: (value: number) => `${value.toFixed(2)}%`,
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
        description="暂无债券持仓数据"
        style={{ padding: 40 }}
      />
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 8, fontSize: 12, color: '#666' }}>
        债券总占比: <strong>{totalWeight.toFixed(2)}%</strong>
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

export default BondHoldingsTable;
