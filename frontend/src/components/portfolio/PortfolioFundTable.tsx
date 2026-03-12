/**
 * Table component for displaying portfolio funds.
 */
import React, { useState } from 'react';
import {
  Table,
  Button,
  InputNumber,
  Popconfirm,
  Space,
  Tag,
  Typography,
  Empty,
  Tooltip,
} from 'antd';
import {
  DeleteOutlined,
  PlusOutlined,
  ImportOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { PortfolioFund } from '../../types';

const { Text } = Typography;

interface PortfolioFundTableProps {
  funds: PortfolioFund[];
  loading: boolean;
  onAdd: () => void;
  onImport: () => void;
  onDelete: (fundCodes: string[]) => void;
  onUpdateShares: (fundCode: string, shares: number) => void;
  onRefresh: () => void;
}

const PortfolioFundTable: React.FC<PortfolioFundTableProps> = ({
  funds,
  loading,
  onAdd,
  onImport,
  onDelete,
  onUpdateShares,
  onRefresh,
}) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const formatCurrency = (value: number | undefined) => {
    if (value === undefined || isNaN(value)) return '-';
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
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
    // Chinese stock market convention: red = up, green = down
    return value >= 0 ? '#cf1322' : '#3f8600';
  };

  // Format nav_date to mm-dd for display in column header
  const formatNavDate = (dateStr: string | undefined): string => {
    if (!dateStr) return '';
    // Handle both YYYY-MM-DD and MM-DD formats
    if (dateStr.includes('-')) {
      const parts = dateStr.split('-');
      if (parts.length === 3) {
        return `${parts[1]}-${parts[2]}`; // YYYY-MM-DD -> MM-DD
      }
      if (parts.length === 2) {
        return dateStr; // Already MM-DD
      }
    }
    return '';
  };

  // Get the nav_date from the first fund (assuming all funds have the same nav_date)
  const navDateLabel = funds.length > 0 ? formatNavDate(funds[0].nav_date) : '';

  const columns = [
    {
      title: '基金代码',
      dataIndex: 'fund_code',
      key: 'fund_code',
      width: 100,
      fixed: 'left' as const,
      render: (code: string) => <Text strong>{code}</Text>,
    },
    {
      title: '基金简称',
      dataIndex: 'fund_name',
      key: 'fund_name',
      width: 180,
      ellipsis: true,
    },
    {
      title: '估算净值',
      dataIndex: 'estimated_nav',
      key: 'estimated_nav',
      width: 110,
      align: 'right' as const,
      render: (value: number, record: PortfolioFund) => (
        <div>
          <div>{formatNumber(value, 4)}</div>
          {record.estimation_time && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.estimation_time}
            </Text>
          )}
        </div>
      ),
    },
    {
      title: '估算涨跌',
      dataIndex: 'estimated_growth',
      key: 'estimated_growth',
      width: 100,
      align: 'right' as const,
      render: (value: number, record: PortfolioFund) => (
        <div>
          <Tag color={getGrowthColor(value)} style={{ fontSize: 13 }}>
            {formatPercent(value)}
          </Tag>
          {record.estimation_time && (
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {record.estimation_time}
              </Text>
            </div>
          )}
        </div>
      ),
    },
    {
      title: () => (
        <div style={{ textAlign: 'right' }}>
          <div>最新净值</div>
          {navDateLabel && (
            <div style={{ fontSize: 12, color: '#999', fontWeight: 'normal' }}>
              {navDateLabel}
            </div>
          )}
        </div>
      ),
      dataIndex: 'latest_nav',
      key: 'latest_nav',
      width: 110,
      align: 'right' as const,
      render: (value: number) => formatNumber(value, 4),
    },
    {
      title: () => (
        <div style={{ textAlign: 'right' }}>
          <div>最新涨跌</div>
          {navDateLabel && (
            <div style={{ fontSize: 12, color: '#999', fontWeight: 'normal' }}>
              {navDateLabel}
            </div>
          )}
        </div>
      ),
      dataIndex: 'latest_growth',
      key: 'latest_growth',
      width: 100,
      align: 'right' as const,
      render: (value: number) => (
        <Tag color={getGrowthColor(value)} style={{ fontSize: 13 }}>
          {formatPercent(value)}
        </Tag>
      ),
    },
    {
      title: '持仓份额',
      dataIndex: 'shares',
      key: 'shares',
      width: 140,
      align: 'right' as const,
      render: (value: number, record: PortfolioFund) => (
        <InputNumber
          min={0}
          step={0.01}
          precision={2}
          defaultValue={value}
          onBlur={(e) => {
            const newValue = parseFloat(e.target.value);
            if (!isNaN(newValue) && newValue !== value) {
              onUpdateShares(record.fund_code, newValue);
            }
          }}
          style={{ width: 120 }}
        />
      ),
    },
    {
      title: '估算市值',
      dataIndex: 'estimated_value',
      key: 'estimated_value',
      width: 140,
      align: 'right' as const,
      render: (value: number, record: PortfolioFund) => (
        <div>
          <div>
            <Text strong>{formatCurrency(value)}</Text>
            {record.is_estimated_fallback && (
              <Tooltip title="估算净值未更新，使用最新净值计算">
                <Tag color="orange" style={{ marginLeft: 4, fontSize: 10, padding: '0 4px' }}>昨</Tag>
              </Tooltip>
            )}
          </div>
          {record.estimation_time ? (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.estimation_time}
            </Text>
          ) : record.is_estimated_fallback && record.nav_date ? (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.nav_date}
            </Text>
          ) : null}
        </div>
      ),
    },
    {
      title: () => (
        <div style={{ textAlign: 'right' }}>
          <div>最新市值</div>
          {navDateLabel && (
            <div style={{ fontSize: 12, color: '#999', fontWeight: 'normal' }}>
              {navDateLabel}
            </div>
          )}
        </div>
      ),
      dataIndex: 'latest_value',
      key: 'latest_value',
      width: 130,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right' as const,
      render: (_: unknown, record: PortfolioFund) => (
        <Popconfirm
          title="删除基金"
          description={`确定要从组合中删除 ${record.fund_name} 吗？`}
          onConfirm={() => onDelete([record.fund_code])}
          okText="删除"
          cancelText="取消"
          okButtonProps={{ danger: true }}
        >
          <Button
            type="text"
            danger
            size="small"
            icon={<DeleteOutlined />}
          >
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
  };

  const handleBatchDelete = () => {
    onDelete(selectedRowKeys as string[]);
    setSelectedRowKeys([]);
  };

  return (
    <div>
      {/* Toolbar */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={onAdd}
          >
            添加基金
          </Button>
          <Button
            icon={<ImportOutlined />}
            onClick={onImport}
          >
            批量导入
          </Button>
          {selectedRowKeys.length > 0 && (
            <Popconfirm
              title="批量删除"
              description={`确定要删除选中的 ${selectedRowKeys.length} 只基金吗？`}
              onConfirm={handleBatchDelete}
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <Button
                danger
                icon={<DeleteOutlined />}
              >
                删除选中 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </Space>
        <Tooltip title="刷新数据">
          <Button
            icon={<ReloadOutlined />}
            onClick={onRefresh}
            loading={loading}
          >
            刷新
          </Button>
        </Tooltip>
      </div>

      {/* Table */}
      {funds.length === 0 ? (
        <Empty
          description="暂无基金，请点击上方按钮添加"
          style={{ marginTop: 48 }}
        />
      ) : (
        <Table
          rowKey="fund_code"
          rowSelection={rowSelection}
          columns={columns}
          dataSource={funds}
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 只基金`,
          }}
          size="middle"
        />
      )}
    </div>
  );
};

export default PortfolioFundTable;
