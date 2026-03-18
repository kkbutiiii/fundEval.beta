/**
 * Modal for creating buy/sell transactions.
 */
import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  DatePicker,
  InputNumber,
  Space,
  Typography,
  Divider,
  Alert,
  message,
  Spin,
} from 'antd';
import dayjs from 'dayjs';
import { api } from '../../services/api';
import type { PortfolioFund, CreateTransactionRequest } from '../../types';

interface TransactionModalProps {
  visible: boolean;
  fund: PortfolioFund | null;
  type: 'buy' | 'sell';
  onCancel: () => void;
  onConfirm: (data: CreateTransactionRequest) => void;
}

const { Text } = Typography;

export const TransactionModal: React.FC<TransactionModalProps> = ({
  visible,
  fund,
  type,
  onCancel,
  onConfirm,
}) => {
  const [form] = Form.useForm();
  const [calculating, setCalculating] = useState<'shares' | 'amount' | null>(null);
  const [navLoading, setNavLoading] = useState(false);
  const [dateWarning, setDateWarning] = useState<string | null>(null);

  const isBuy = type === 'buy';
  const title = isBuy ? '买入基金' : '卖出基金';
  const confirmText = isBuy ? '确认买入' : '确认卖出';

  useEffect(() => {
    if (visible && fund) {
      // Reset form with default values
      form.resetFields();
      form.setFieldsValue({
        transaction_date: dayjs().subtract(1, 'day'),
        nav: fund.latest_nav || fund.estimated_nav || undefined,
      });
      setDateWarning(null);
    }
  }, [visible, fund, form]);

  const handleDateChange = async (date: dayjs.Dayjs | null) => {
    if (!date || !fund) return;

    // Clear previous warning
    setDateWarning(null);

    // Fetch historical NAV for the selected date
    setNavLoading(true);
    try {
      // Get NAV history for the last 1 year to cover the selected date
      const navHistory = await api.getNavHistory(fund.fund_code, '1y');

      if (navHistory?.fund_nav_history?.length > 0) {
        // Format the selected date to match NAV history format (YYYY-MM-DD)
        const selectedDateStr = date.format('YYYY-MM-DD');

        // Find the NAV for the selected date
        const navForDate = navHistory.fund_nav_history.find(
          item => item.date === selectedDateStr
        );

        if (navForDate?.nav) {
          form.setFieldsValue({ nav: navForDate.nav });
        } else {
          // If no NAV found for exact date, show a warning message
          const warningMsg = `${selectedDateStr} 可能不是交易日，未找到净值数据。请手动输入净值或选择其他日期。`;
          setDateWarning(warningMsg);
          console.log(`No NAV data found for ${selectedDateStr}`);
        }
      }
    } catch (error) {
      console.error('Failed to fetch NAV history:', error);
    } finally {
      setNavLoading(false);
    }
  };

  const handleValuesChange = (changedValues: any, allValues: any) => {
    const { nav, shares, amount } = allValues;

    if (!nav || nav <= 0) return;

    // Auto-calculate when shares or amount is entered
    if ('shares' in changedValues && shares !== undefined && shares !== null) {
      setCalculating('amount');
      const calculatedAmount = Math.round(shares * nav * 100) / 100;
      form.setFieldsValue({ amount: calculatedAmount });
      setTimeout(() => setCalculating(null), 100);
    } else if ('amount' in changedValues && amount !== undefined && amount !== null) {
      setCalculating('shares');
      const calculatedShares = Math.round((amount / nav) * 10000) / 10000;
      form.setFieldsValue({ shares: calculatedShares });
      setTimeout(() => setCalculating(null), 100);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      const data: CreateTransactionRequest = {
        transaction_type: type,
        transaction_date: values.transaction_date.format('YYYY-MM-DD'),
        nav: values.nav,
        shares: values.shares,
        amount: values.amount,
      };

      onConfirm(data);
    } catch (error) {
      message.error('请填写完整信息');
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setDateWarning(null);
    onCancel();
  };

  if (!fund) return null;

  return (
    <Modal
      title={
        <Space>
          <Text strong>{title}</Text>
          <Text type="secondary">{fund.fund_code}</Text>
          <Text>{fund.fund_name}</Text>
        </Space>
      }
      open={visible}
      onCancel={handleCancel}
      onOk={handleSubmit}
      okText={confirmText}
      cancelText="取消"
      width={480}
    >
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        style={{ marginTop: 16 }}
      >
        <Form.Item
          name="transaction_date"
          label="确认日期"
          rules={[{ required: true, message: '请选择确认日期' }]}
        >
          <DatePicker
            style={{ width: '100%' }}
            format="YYYY-MM-DD"
            allowClear={false}
            onChange={handleDateChange}
            disabled={navLoading}
          />
        </Form.Item>

        {dateWarning && (
          <Alert
            message={dateWarning}
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
            closable
            onClose={() => setDateWarning(null)}
          />
        )}

        <Form.Item
          name="nav"
          label="确认净值"
          rules={[
            { required: true, message: '请输入确认净值' },
            { type: 'number', min: 0.0001, message: '净值必须大于0' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            precision={4}
            step={0.0001}
            placeholder="请输入确认净值"
            disabled={navLoading}
          />
        </Form.Item>

        <Divider style={{ margin: '16px 0' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            填写以下任一项，另一项将自动计算
          </Text>
        </Divider>

        <Space align="start" style={{ width: '100%' }}>
          <Form.Item
            name="shares"
            label={isBuy ? '买入份额' : '卖出份额'}
            style={{ width: 200 }}
          >
            <InputNumber
              style={{ width: '100%' }}
              precision={4}
              step={100}
              placeholder="份额"
              disabled={calculating === 'shares'}
            />
          </Form.Item>

          <Form.Item
            name="amount"
            label={isBuy ? '买入金额' : '卖出金额'}
            style={{ width: 200 }}
          >
            <InputNumber
              style={{ width: '100%' }}
              precision={2}
              step={1000}
              placeholder="金额"
              disabled={calculating === 'amount'}
              prefix="¥"
            />
          </Form.Item>
        </Space>
      </Form>
    </Modal>
  );
};

export default TransactionModal;
