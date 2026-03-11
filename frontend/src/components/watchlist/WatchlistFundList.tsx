/**
 * List of watchlist funds.
 */
import React from 'react';
import { Empty, Spin } from 'antd';
import WatchlistFundItem from './WatchlistFundItem';
import type { WatchlistFundWithRealtime } from '../../hooks/useWatchlist';

interface WatchlistFundListProps {
  funds: WatchlistFundWithRealtime[];
  currentFundCode: string | null;
  isLoading: boolean;
  onSelect: (fundCode: string) => void;
  onRemove: (fundCode: string) => void;
}

const WatchlistFundList: React.FC<WatchlistFundListProps> = ({
  funds,
  currentFundCode,
  isLoading,
  onSelect,
  onRemove,
}) => {
  if (isLoading && funds.length === 0) {
    return (
      <div style={{ padding: '40px 0', textAlign: 'center' }}>
        <Spin size="small" />
        <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>加载中...</div>
      </div>
    );
  }

  if (funds.length === 0) {
    return (
      <Empty
        description="暂无自选基金"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        style={{ marginTop: 40 }}
      >
        <div style={{ fontSize: 12, color: '#999', textAlign: 'center' }}>
          搜索上方添加基金到自选
        </div>
      </Empty>
    );
  }

  return (
    <div
      style={{
        flex: 1,
        overflowY: 'auto',
        borderTop: '1px solid #f0f0f0',
      }}
    >
      {funds.map((fund) => (
        <WatchlistFundItem
          key={fund.fund_code}
          fund={fund}
          isSelected={fund.fund_code === currentFundCode}
          onSelect={onSelect}
          onRemove={onRemove}
        />
      ))}
    </div>
  );
};

export default WatchlistFundList;
