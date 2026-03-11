/**
 * Modal for batch importing funds into a portfolio.
 */
import React, { useState } from 'react';
import { Modal, Input, Form, Alert, Typography } from 'antd';

const { Text } = Typography;

interface ImportFundsModalProps {
  visible: boolean;
  onCancel: () => void;
  onConfirm: (codes: string[]) => void;
}

const ImportFundsModal: React.FC<ImportFundsModalProps> = ({
  visible,
  onCancel,
  onConfirm,
}) => {
  const [form] = Form.useForm();
  const [confirmLoading, setConfirmLoading] = useState(false);

  const parseFundCodes = (input: string): string[] => {
    // Split by comma, newline, space, or tab
    const codes = input
      .split(/[,，\s\n\r\t]+/)
      .map(code => code.trim())
      .filter(code => code.length > 0);

    // Remove duplicates
    return [...new Set(codes)];
  };

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setConfirmLoading(true);
      const codes = parseFundCodes(values.codes);
      onConfirm(codes);
      form.resetFields();
    } catch (error) {
      console.error('Form validation failed:', error);
    } finally {
      setConfirmLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="批量导入基金"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={confirmLoading}
      okText="导入"
      cancelText="取消"
      width={500}
    >
      <Form form={form} layout="vertical">
        <Alert
          message="提示"
          description="支持输入多个基金代码，使用逗号、空格或换行分隔。系统将自动过滤重复的代码。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Form.Item
          name="codes"
          label="基金代码"
          rules={[
            { required: true, message: '请输入基金代码' },
          ]}
        >
          <Input.TextArea
            placeholder="例如：000001, 005827, 161725"
            rows={6}
            style={{ fontFamily: 'monospace' }}
          />
        </Form.Item>
        <Text type="secondary" style={{ fontSize: 12 }}>
          示例格式：000001,005827,161725 或每行一个代码
        </Text>
      </Form>
    </Modal>
  );
};

export default ImportFundsModal;
