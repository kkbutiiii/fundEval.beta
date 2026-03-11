/**
 * Sidebar component for watchlist page with search and fund list.
 */
import React from 'react';
import { Typography, Badge } from 'antd';
import FundSearch from '../FundSearch';
import WatchlistFundList from './WatchlistFundList';
import type { FundInfo } from '../../types';
import type { WatchlistFundWithRealtime } from '../../hooks/useWatchlist';

const { Text } = Typography;

interface WatchlistSidebarProps {
  funds: WatchlistFundWithRealtime[];
  currentFundCode: string | null;
  isLoading: boolean;
  lastUpdate: Date | null;
  onSelectFund: (fundCode: string) => void;
  onRemoveFund: (fundCode: string) => void;
  onAddFund: (fund: FundInfo) => void;
}

const WatchlistSidebar: React.FC<WatchlistSidebarProps> = ({
  funds,
  currentFundCode,
  isLoading,
  lastUpdate,
  onSelectFund,
  onRemoveFund,
  onAddFund,
}) => {
  const handleFundSelect = (fund: FundInfo) => {
    onAddFund(fund);
    // Also select the newly added fund
    onSelectFund(fund.fund_code);
  };

  // Format last update time
  const formatLastUpdate = (date: Date | null): string => {
    if (!date) return '未更新';
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return '刚刚更新';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分钟前`;
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#fff',
        borderRight: '1px solid #f0f0f0',
      }}
    >
      {/* Search Section */}
      <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
        <FundSearch
          onSelect={handleFundSelect}
          placeholder="搜索基金代码或名称"
        />
      </div>

      {/* Header with count */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: '#fafafa',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <Text strong style={{ fontSize: 14 }}>
            自选基金
          </Text>
          <Badge
            count={funds.length}
            style={{ marginLeft: 8, backgroundColor: '#1890ff' }}
            showZero
          />
        </div>
        <Text type="secondary" style={{ fontSize: 11 }}>
          {formatLastUpdate(lastUpdate)}
        </Text>
      </div>

      {/* Fund List */}
      <WatchlistFundList
        funds={funds}
        currentFundCode={currentFundCode}
        isLoading={isLoading}
        onSelect={onSelectFund}
        onRemove={onRemoveFund}
      />
    </div>
  );
};

export default WatchlistSidebar;
