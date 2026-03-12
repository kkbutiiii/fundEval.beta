/**
 * Modal for adding a single fund to a portfolio.
 */
import React, { useState } from 'react';
import { Modal, Input, Form, Select, Spin, Typography } from 'antd';
import { api } from '../../services/api';
import type { FundInfo } from '../../types';

const { Text } = Typography;
const { Option } = Select;

interface AddFundModalProps {
  visible: boolean;
  onCancel: () => void;
  onConfirm: (fund: { fund_code: string; fund_name: string; shares: number }) => void;
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

  const handleFundSelect = (fundCode: string) => {
    const fund = searchResults.find(f => f.fund_code === fundCode);
    setSelectedFund(fund || null);
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setConfirmLoading(true);

      const fund = searchResults.find(f => f.fund_code === values.fundCode);
      if (fund) {
        onConfirm({
          fund_code: fund.fund_code,
          fund_name: fund.fund_name,
          shares: values.shares,
        });
      }

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
    onCancel();
  };

  return (
    <Modal
      title="添加基金"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={confirmLoading}
      okText="添加"
      cancelText="取消"
      width={500}
    >
      <Form form={form} layout="vertical">
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
            </Text>
          </Form.Item>
        )}

        <Form.Item
          name="shares"
          label="持仓份额"
          rules={[
            { required: true, message: '请输入持仓份额' },
            {
              validator: (_, value) => {
                const num = parseFloat(value);
                if (isNaN(num) || num <= 0) {
                  return Promise.reject(new Error('份额必须大于0'));
                }
                return Promise.resolve();
              },
            },
          ]}
        >
          <Input type="number" step="0.01" placeholder="请输入持仓份额" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default AddFundModal;
