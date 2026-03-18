/**
 * Modal for adding a fund to a portfolio with first buy transaction.
 */
import React, { useState } from 'react';
import {
  Modal,
  Input,
  Form,
  Select,
  Spin,
  Typography,
  DatePicker,
  InputNumber,
  Space,
  Divider,
  Alert,
} from 'antd';
import dayjs from 'dayjs';
import { api } from '../../services/api';
import type { FundInfo, CreateTransactionRequest } from '../../types';

const { Text } = Typography;
const { Option } = Select;

interface AddFundModalProps {
  visible: boolean;
  onCancel: () => void;
  onConfirm: (fundCode: string, fundName: string, transaction: CreateTransactionRequest) => void;
}

const AddFundModal: React.FC<AddFundModalProps> = ({
  visible,
  onCancel,
  onConfirm,
}) => {
  const [form] = Form.useForm();
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<FundInfo[]>([]);
  const [selectedFund, setSelectedFund] = useState<FundInfo | null>(null);
  const [calculating, setCalculating] = useState<'shares' | 'amount' | null>(null);
  const [navLoading, setNavLoading] = useState(false);
  const [dateWarning, setDateWarning] = useState<string | null>(null);

  const handleSearch = async (keyword: string) => {
    if (!keyword || keyword.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const results = await api.searchFunds(keyword, 10);
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleFundSelect = async (fundCode: string) => {
    const fund = searchResults.find(f => f.fund_code === fundCode);
    setSelectedFund(fund || null);

    // Get the currently selected date from the form
    const currentDate = form.getFieldValue('transaction_date') as dayjs.Dayjs;

    if (currentDate && fund) {
      // If date is already selected, fetch NAV for that date
      setNavLoading(true);
      setDateWarning(null);
      try {
        const navHistory = await api.getNavHistory(fund.fund_code, '1y');
        if (navHistory?.fund_nav_history?.length > 0) {
          const selectedDateStr = currentDate.format('YYYY-MM-DD');
          const navForDate = navHistory.fund_nav_history.find(
            item => item.date === selectedDateStr
          );

          if (navForDate?.nav) {
            form.setFieldsValue({ nav: navForDate.nav });
          } else {
            const warningMsg = `${selectedDateStr} 可能不是交易日，未找到净值数据。请手动输入净值或选择其他日期。`;
            setDateWarning(warningMsg);
            // Clear NAV field since no data found for this date
            form.setFieldsValue({ nav: undefined });
          }
        }
      } catch (error) {
        console.error('Failed to fetch NAV history:', error);
      } finally {
        setNavLoading(false);
      }
    } else if (fund?.nav) {
      // If no date selected yet, use the latest NAV
      form.setFieldsValue({ nav: fund.nav });
    }
  };

  const handleDateChange = async (date: dayjs.Dayjs | null) => {
    if (!date || !selectedFund) return;

    // Clear previous warning
    setDateWarning(null);

    // Only fetch historical NAV if we have a fund selected
    setNavLoading(true);
    try {
      // Get NAV history for the last 1 year to cover the selected date
      const navHistory = await api.getNavHistory(selectedFund.fund_code, '1y');

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

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setConfirmLoading(true);

      const fund = searchResults.find(f => f.fund_code === values.fundCode);
      if (fund) {
        const transaction: CreateTransactionRequest = {
          transaction_type: 'buy',
          transaction_date: values.transaction_date.format('YYYY-MM-DD'),
          nav: values.nav,
          shares: values.shares,
          amount: values.amount,
        };
        onConfirm(fund.fund_code, fund.fund_name, transaction);
      }

      // Reset form
      form.resetFields();
      setSelectedFund(null);
      setSearchResults([]);
    } catch (error) {
      console.error('Form validation failed:', error);
    } finally {
      setConfirmLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setSelectedFund(null);
    setSearchResults([]);
    setDateWarning(null);
    onCancel();
  };

  return (
    <Modal
      title="添加基金（首次买入）"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={confirmLoading}
      okText="添加"
      cancelText="取消"
      width={500}
    >
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
      >
        <Form.Item
          name="fundCode"
          label="选择基金"
          rules={[{ required: true, message: '请选择基金' }]}
        >
          <Select
            showSearch
            placeholder="输入基金代码或名称搜索"
            onSearch={handleSearch}
            onSelect={handleFundSelect}
            notFoundContent={searching ? <Spin size="small" /> : null}
            filterOption={false}
            style={{ width: '100%' }}
          >
            {searchResults.map(fund => (
              <Option key={fund.fund_code} value={fund.fund_code}>
                {fund.fund_name} ({fund.fund_code})
              </Option>
            ))}
          </Select>
        </Form.Item>

        {selectedFund && (
          <Form.Item>
            <Text type="secondary">
              已选择: {selectedFund.fund_name} ({selectedFund.fund_code})
              {selectedFund.fund_type && (
                <span style={{ marginLeft: 8 }}>[{selectedFund.fund_type}]</span>
              )}
              {selectedFund.nav && (
                <span style={{ marginLeft: 8 }}>最新净值: {selectedFund.nav}</span>
              )}
            </Text>
          </Form.Item>
        )}

        <Form.Item
          name="transaction_date"
          label="确认日期"
          rules={[{ required: true, message: '请选择确认日期' }]}
          initialValue={dayjs().subtract(1, 'day')}
        >
          <DatePicker
            style={{ width: '100%' }}
            format="YYYY-MM-DD"
            allowClear={false}
            onChange={handleDateChange}
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
            label="买入份额"
            style={{ width: 210 }}
            rules={[{ required: true, message: '请输入份额' }]}
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
            label="买入金额"
            style={{ width: 210 }}
            rules={[{ required: true, message: '请输入金额' }]}
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

export default AddFundModal;
