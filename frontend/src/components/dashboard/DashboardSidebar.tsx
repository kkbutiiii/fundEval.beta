/**
 * Modern Dashboard Sidebar Component
 * Light tech style with glassmorphism effect
 */
import React from 'react';
import { Button, List, Typography, Popconfirm, Empty } from 'antd';
import { PlusOutlined, DeleteOutlined, WalletOutlined } from '@ant-design/icons';
import type { FundPortfolio } from '../../types';

interface DashboardSidebarProps {
  portfolios: FundPortfolio[];
  currentPortfolio: FundPortfolio | null;
  onSelect: (portfolio: FundPortfolio) => void;
  onAdd: () => void;
  onDelete: (id: string) => void;
}

const DashboardSidebar: React.FC<DashboardSidebarProps> = ({
  portfolios,
  currentPortfolio,
  onSelect,
  onAdd,
  onDelete,
}) => {
  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(255, 255, 255, 0.7)',
        backdropFilter: 'blur(10px)',
        borderRight: '1px solid rgba(255, 255, 255, 0.5)',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
        }}
      >
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={onAdd}
          block
          style={{
            background: 'linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)',
            border: 'none',
            borderRadius: '8px',
            height: '40px',
          }}
        >
          新建组合
        </Button>
      </div>

      {/* Portfolio List */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '8px 0',
        }}
      >
        {portfolios.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={<span style={{ color: '#999' }}>暂无组合</span>}
          />
        ) : (
          <List
            dataSource={portfolios}
            renderItem={(portfolio) => {
              const isSelected = currentPortfolio?.id === portfolio.id;
              return (
                <List.Item
                  style={{
                    padding: '4px 12px',
                    cursor: 'pointer',
                    border: 'none',
                  }}
                  onClick={() => onSelect(portfolio)}
                >
                  <div
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      padding: '10px 12px',
                      borderRadius: '10px',
                      background: isSelected
                        ? 'rgba(24, 144, 255, 0.12)'
                        : 'transparent',
                      color: isSelected ? '#1890ff' : '#666',
                      transition: 'all 0.2s ease',
                      position: 'relative',
                    }}
                  >
                    {/* Active indicator */}
                    {isSelected && (
                      <div
                        style={{
                          position: 'absolute',
                          left: '-12px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          width: '3px',
                          height: '20px',
                          background:
                            'linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)',
                          borderRadius: '0 3px 3px 0',
                        }}
                      />
                    )}

                    <WalletOutlined
                      style={{
                        marginRight: 12,
                        fontSize: 16,
                        color: isSelected ? '#1890ff' : 'inherit',
                      }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Typography.Text
                        ellipsis
                        style={{
                          color: 'inherit',
                          fontSize: 14,
                          fontWeight: isSelected ? 500 : 400,
                        }}
                      >
                        {portfolio.name}
                      </Typography.Text>
                      <div
                        style={{
                          fontSize: 12,
                          color: isSelected
                            ? 'rgba(24, 144, 255, 0.7)'
                            : '#999',
                          marginTop: 2,
                        }}
                      >
                        {portfolio.funds.length} 只基金
                      </div>
                    </div>

                    <Popconfirm
                      title="删除组合"
                      description={`确定要删除组合"${portfolio.name}"吗？`}
                      onConfirm={(e) => {
                        e?.stopPropagation();
                        onDelete(portfolio.id);
                      }}
                      onCancel={(e) => e?.stopPropagation()}
                      okText="删除"
                      cancelText="取消"
                      okButtonProps={{ danger: true }}
                    >
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        style={{
                          color: isSelected
                            ? 'rgba(255, 77, 79, 0.8)'
                            : 'rgba(0, 0, 0, 0.25)',
                          opacity: 0,
                          transition: 'opacity 0.2s',
                        }}
                        className="delete-btn"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>
                  </div>
                </List.Item>
              );
            }}
          />
        )}
      </div>

      <style>{`
        .ant-list-item:hover .delete-btn {
          opacity: 1 !important;
        }
      `}</style>
    </div>
  );
};

export default DashboardSidebar;
