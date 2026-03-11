/**
 * Modal for creating a new portfolio.
 */
import React, { useState } from 'react';
import { Modal, Input, Form } from 'antd';

interface AddPortfolioModalProps {
  visible: boolean;
  onCancel: () => void;
  onConfirm: (name: string) => void;
}

const AddPortfolioModal: React.FC<AddPortfolioModalProps> = ({
  visible,
  onCancel,
  onConfirm,
}) => {
  const [form] = Form.useForm();
  const [confirmLoading, setConfirmLoading] = useState(false);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setConfirmLoading(true);
      onConfirm(values.name.trim());
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
      title="新建组合"
      open={visible}
      onOk={handleOk}
      onCancel={handleCancel}
      confirmLoading={confirmLoading}
      okText="创建"
      cancelText="取消"
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="组合名称"
          rules={[
            { required: true, message: '请输入组合名称' },
            { min: 1, max: 50, message: '组合名称长度应在1-50个字符之间' },
          ]}
        >
          <Input placeholder="例如：我的定投组合" maxLength={50} showCount />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default AddPortfolioModal;
