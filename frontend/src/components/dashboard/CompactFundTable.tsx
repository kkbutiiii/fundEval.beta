/**
 * Compact Fund Table Component
 * Reduced row height and padding for financial monitoring
 */
import React, { useState, useMemo } from 'react';
import {
  Table,
  Button,
  Popconfirm,
  Space,
  Tag,
  Typography,
  Empty,
  Tooltip,
  ConfigProvider,
} from 'antd';
import {
  DeleteOutlined,
  PlusOutlined,
  ImportOutlined,
  ReloadOutlined,
  ShoppingCartOutlined,
  MoneyCollectOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import type { PortfolioFund } from '../../types';

const { Text, Link } = Typography;

interface CompactFundTableProps {
  funds: PortfolioFund[];
  loading: boolean;
  onAdd: () => void;
  onImport: () => void;
  onDelete: (fundCodes: string[]) => void;
  onRefresh: () => void;
  onViewDetail: (fund: PortfolioFund) => void;
  onViewFundDetail: (fund: PortfolioFund) => void;
  onBuy: (fund: PortfolioFund) => void;
  onSell: (fund: PortfolioFund) => void;
}

const CompactFundTable: React.FC<CompactFundTableProps> = ({
  funds,
  loading,
  onAdd,
  onImport,
  onDelete,
  onRefresh,
  onViewDetail,
  onViewFundDetail,
  onBuy,
  onSell,
}) => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 });

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
    return value >= 0 ? '#cf1322' : '#3f8600';
  };

  const formatNavDate = (dateStr: string | undefined): string => {
    if (!dateStr) return '';
    if (dateStr.includes('-')) {
      const parts = dateStr.split('-');
      if (parts.length === 3) {
        return `${parts[1]}-${parts[2]}`;
      }
      if (parts.length === 2) {
        return dateStr;
      }
    }
    return '';
  };

  const navDateLabel = funds.length > 0 ? formatNavDate(funds[0].nav_date) : '';

  const columns = [
    {
      title: '基金代码',
      dataIndex: 'fund_code',
      key: 'fund_code',
      width: 90,
      fixed: 'left' as const,
      render: (code: string) => <Text strong style={{ fontSize: 12 }}>{code}</Text>,
    },
    {
      title: '基金简称',
      dataIndex: 'fund_name',
      key: 'fund_name',
      width: 150,
      ellipsis: true,
      render: (name: string, record: PortfolioFund) => (
        <Link
          onClick={() => onViewFundDetail(record)}
          style={{ cursor: 'pointer', fontSize: 13 }}
        >
          {name}
        </Link>
      ),
    },
    {
      title: '估算净值',
      dataIndex: 'estimated_nav',
      key: 'estimated_nav',
      width: 90,
      align: 'right' as const,
      render: (value: number, record: PortfolioFund) => (
        <div>
          <div style={{ fontSize: 13 }}>{formatNumber(value, 4)}</div>
          {record.estimation_time && (
            <Text type="secondary" style={{ fontSize: 10 }}>
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
      width: 80,
      align: 'right' as const,
      render: (value: number) => (
        <Tag
          color={getGrowthColor(value)}
          style={{ fontSize: 12, padding: '0 4px', margin: 0 }}
        >
          {formatPercent(value)}
        </Tag>
      ),
    },
    {
      title: () => (
        <div style={{ textAlign: 'right' }}>
          <div>最新净值</div>
          {navDateLabel && (
            <div style={{ fontSize: 10, color: '#999', fontWeight: 'normal' }}>
              {navDateLabel}
            </div>
          )}
        </div>
      ),
      dataIndex: 'latest_nav',
      key: 'latest_nav',
      width: 90,
      align: 'right' as const,
      render: (value: number) => (
        <span style={{ fontSize: 13 }}>{formatNumber(value, 4)}</span>
      ),
    },
    {
      title: () => (
        <div style={{ textAlign: 'right' }}>
          <div>最新涨跌</div>
          {navDateLabel && (
            <div style={{ fontSize: 10, color: '#999', fontWeight: 'normal' }}>
              {navDateLabel}
            </div>
          )}
        </div>
      ),
      dataIndex: 'latest_growth',
      key: 'latest_growth',
      width: 80,
      align: 'right' as const,
      render: (value: number) => (
        <Tag
          color={getGrowthColor(value)}
          style={{ fontSize: 12, padding: '0 4px', margin: 0 }}
        >
          {formatPercent(value)}
        </Tag>
      ),
    },
    {
      title: '份额',
      dataIndex: 'shares',
      key: 'shares',
      width: 100,
      align: 'right' as const,
      render: (value: number) => (
        <Text style={{ fontSize: 13 }}>{formatNumber(value, 2)}</Text>
      ),
    },
    {
      title: '估算市值',
      dataIndex: 'estimated_value',
      key: 'estimated_value',
      width: 120,
      align: 'right' as const,
      render: (value: number, record: PortfolioFund) => (
        <div>
          <div style={{ fontSize: 13 }}>
            <Text strong>{formatCurrency(value)}</Text>
            {record.is_estimated_fallback && (
              <Tooltip title="估算净值未更新，使用最新净值计算">
                <Tag color="orange" style={{ marginLeft: 4, fontSize: 9, padding: '0 2px' }}>
                  昨
                </Tag>
              </Tooltip>
            )}
          </div>
        </div>
      ),
    },
    {
      title: () => (
        <div style={{ textAlign: 'right' }}>
          <div>最新市值</div>
          {navDateLabel && (
            <div style={{ fontSize: 10, color: '#999', fontWeight: 'normal' }}>
              {navDateLabel}
            </div>
          )}
        </div>
      ),
      dataIndex: 'latest_value',
      key: 'latest_value',
      width: 110,
      align: 'right' as const,
      render: (value: number) => (
        <span style={{ fontSize: 13 }}>{formatCurrency(value)}</span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 140,
      fixed: 'right' as const,
      render: (_: unknown, record: PortfolioFund) => (
        <Space size={4}>
          <Tooltip title="查看详情">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onViewDetail(record)}
              style={{ padding: '0 4px' }}
            />
          </Tooltip>
          <Tooltip title="买入">
            <Button
              type="text"
              size="small"
              icon={<ShoppingCartOutlined />}
              onClick={() => onBuy(record)}
              style={{ color: '#52c41a', padding: '0 4px' }}
            />
          </Tooltip>
          <Tooltip title="卖出">
            <Button
              type="text"
              size="small"
              icon={<MoneyCollectOutlined />}
              onClick={() => onSell(record)}
              style={{ color: '#f5222d', padding: '0 4px' }}
            />
          </Tooltip>
          <Popconfirm
            title="删除基金"
            description={`确定要从组合中删除 ${record.fund_name} 吗？`}
            onConfirm={() => onDelete([record.fund_code])}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                size="small"
                icon={<DeleteOutlined />}
                style={{ padding: '0 4px' }}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
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

  const handleTableChange = (newPagination: any) => {
    setPagination({
      current: newPagination.current,
      pageSize: newPagination.pageSize,
    });
  };

  return (
    <div className="dash-table-compact">
      {/* Toolbar */}
      <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={onAdd}
            style={{
              background: 'linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)',
              border: 'none',
              borderRadius: '8px',
            }}
            size="small"
          >
            添加基金
          </Button>
          <Button
            icon={<ImportOutlined />}
            onClick={onImport}
            size="small"
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
                size="small"
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
            size="small"
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
        <ConfigProvider
          getPopupContainer={(triggerNode) => triggerNode?.parentElement || document.body}
        >
          <Table
            rowKey="fund_code"
            rowSelection={rowSelection}
            columns={columns}
            dataSource={funds}
            loading={loading}
            scroll={{ x: 1100 }}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 只基金`,
              size: 'small',
              onShowSizeChange: (current, size) => {
                setPagination({ current, pageSize: size });
              },
            }}
            onChange={handleTableChange}
            size="small"
            rowClassName={() => 'compact-row'}
          />
        </ConfigProvider>
      )}

      <style>{`
        .compact-row {
          height: 40px;
        }
        .compact-row td {
          padding: 4px 8px !important;
        }
      `}</style>
    </div>
  );
};

export default CompactFundTable;
