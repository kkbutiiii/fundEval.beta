/**
 * Component for displaying transaction history of a fund.
 */
import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Popconfirm,
  Tag,
  Typography,
  Empty,
  Spin,
  message,
} from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { api } from '../../services/api';
import type { FundTransaction, TransactionSummary } from '../../types';

const { Text } = Typography;

interface TransactionHistoryProps {
  portfolioId: string;
  fundCode: string;
  fundName?: string;
  onRefresh?: () => void;
}

export const TransactionHistory: React.FC<TransactionHistoryProps> = ({
  portfolioId,
  fundCode,
  fundName,
  onRefresh,
}) => {
  const [transactions, setTransactions] = useState<FundTransaction[]>([]);
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    if (!portfolioId || !fundCode) return;

    setLoading(true);
    try {
      const [txData, summaryData] = await Promise.all([
        api.getFundTransactions(portfolioId, fundCode),
        api.getTransactionSummary(portfolioId, fundCode),
      ]);
      setTransactions(txData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [portfolioId, fundCode]);

  const handleDelete = async (transactionId: number) => {
    try {
      await api.deleteTransaction(portfolioId, transactionId);
      await fetchData();
      onRefresh?.();
    } catch (error: any) {
      console.error('Failed to delete transaction:', error);
      // Show error message from backend
      const errorMsg = error?.response?.data?.detail || '删除交易失败';
      message.error(errorMsg);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatNumber = (value: number, digits: number = 2) => {
    return value.toFixed(digits);
  };

  const columns = [
    {
      title: '日期',
      dataIndex: 'transaction_date',
      key: 'transaction_date',
      width: 110,
      render: (date: string) => (
        <Text>{new Date(date).toLocaleDateString('zh-CN')}</Text>
      ),
    },
    {
      title: '类型',
      dataIndex: 'transaction_type',
      key: 'transaction_type',
      width: 80,
      render: (type: 'buy' | 'sell') => (
        <Tag
          color={type === 'buy' ? 'green' : 'red'}
          icon={type === 'buy' ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
        >
          {type === 'buy' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '确认净值',
      dataIndex: 'nav',
      key: 'nav',
      width: 100,
      align: 'right' as const,
      render: (value: number) => formatNumber(value, 4),
    },
    {
      title: '份额',
      dataIndex: 'shares',
      key: 'shares',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatNumber(value, 2),
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right' as const,
      render: (value: number) => (
        <Text strong={false}>{formatCurrency(value)}</Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: unknown, record: FundTransaction) => (
        <Popconfirm
          title="删除交易记录"
          description="确定要删除这条交易记录吗？"
          onConfirm={() => handleDelete(record.id)}
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

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 40 }}>
        <Spin />
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">加载交易记录...</Text>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Summary Card */}
      {summary && (
        <div
          style={{
            background: '#f5f5f5',
            padding: '12px 16px',
            borderRadius: 8,
            marginBottom: 16,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div>
              <Text type="secondary">当前份额</Text>
              <div>
                <Text strong style={{ fontSize: 18 }}>
                  {formatNumber(summary.current_shares, 2)}
                </Text>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <Text type="secondary">净投入</Text>
              <div>
                <Text strong style={{ fontSize: 18 }}>
                  {formatCurrency(summary.net_investment)}
                </Text>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Transaction List */}
      {transactions.length === 0 ? (
        <Empty description="暂无交易记录" />
      ) : (
        <Table
          rowKey="id"
          columns={columns}
          dataSource={transactions}
          pagination={false}
          size="small"
          scroll={{ y: 300 }}
        />
      )}
    </div>
  );
};

export default TransactionHistory;
