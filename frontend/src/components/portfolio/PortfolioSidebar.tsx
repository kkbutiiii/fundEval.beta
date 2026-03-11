/**
 * Sidebar component for portfolio list.
 */
import React from 'react';
import { Button, List, Typography, Popconfirm, Empty } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  WalletOutlined,
} from '@ant-design/icons';
import type { FundPortfolio } from '../../types';

interface PortfolioSidebarProps {
  portfolios: FundPortfolio[];
  currentPortfolio: FundPortfolio | null;
  onSelect: (portfolio: FundPortfolio) => void;
  onAdd: () => void;
  onDelete: (id: string) => void;
}

const PortfolioSidebar: React.FC<PortfolioSidebarProps> = ({
  portfolios,
  currentPortfolio,
  onSelect,
  onAdd,
  onDelete,
}) => {
  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: '#304156',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
      }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={onAdd}
          block
          style={{
            background: '#1890ff',
            borderColor: '#1890ff',
          }}
        >
          新建组合
        </Button>
      </div>

      {/* Portfolio List */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '8px 0',
      }}>
        {portfolios.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span style={{ color: 'rgba(255,255,255,0.45)' }}>
                暂无组合
              </span>
            }
          />
        ) : (
          <List
            dataSource={portfolios}
            renderItem={(portfolio) => {
              const isSelected = currentPortfolio?.id === portfolio.id;
              return (
                <List.Item
                  style={{
                    padding: '0 16px',
                    cursor: 'pointer',
                    background: isSelected ? '#1890ff' : 'transparent',
                    transition: 'all 0.3s',
                    borderLeft: isSelected ? '4px solid #fff' : '4px solid transparent',
                  }}
                  onClick={() => onSelect(portfolio)}
                  actions={[
                    <Popconfirm
                      key="delete"
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
                          color: isSelected ? 'rgba(255,255,255,0.85)' : 'rgba(255,255,255,0.45)',
                        }}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>,
                  ]}
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px 0',
                    color: isSelected ? '#fff' : 'rgba(255,255,255,0.85)',
                  }}>
                    <WalletOutlined style={{ marginRight: 12, fontSize: 16 }} />
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
                      <div style={{
                        fontSize: 12,
                        color: isSelected ? 'rgba(255,255,255,0.65)' : 'rgba(255,255,255,0.45)',
                        marginTop: 2,
                      }}>
                        {portfolio.funds.length} 只基金
                      </div>
                    </div>
                  </div>
                </List.Item>
              );
            }}
          />
        )}
      </div>
    </div>
  );
};

export default PortfolioSidebar;
