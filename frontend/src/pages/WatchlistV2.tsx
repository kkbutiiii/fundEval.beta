/**
 * Watchlist Monitoring Page V2 - Light Tech Style
 * Glassmorphism sidebar design consistent with landing page
 */
import React from 'react';
import { Typography, Badge, Empty, Spin, Button } from 'antd';
import { PlusOutlined, CloseOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import GlassCard from '../components/dashboard/GlassCard';
import EmbeddedFundDetail from '../components/watchlist/EmbeddedFundDetail';
import FundSearch from '../components/FundSearch';
import { useWatchlist } from '../hooks/useWatchlist';
import type { FundInfo } from '../types';
import type { WatchlistFundWithRealtime } from '../hooks/useWatchlist';

const { Text } = Typography;

// Compact Watchlist Fund Item Component
const CompactFundItem: React.FC<{
  fund: WatchlistFundWithRealtime;
  isSelected: boolean;
  onSelect: (fundCode: string) => void;
  onRemove: (fundCode: string) => void;
}> = ({ fund, isSelected, onSelect, onRemove }) => {
  const formatNav = (nav?: number): string => {
    if (nav === undefined || nav === null) return '--';
    return nav.toFixed(4);
  };

  const formatGrowth = (growth?: number): string => {
    if (growth === undefined || growth === null) return '--';
    const sign = growth >= 0 ? '+' : '';
    return `${sign}${growth.toFixed(2)}%`;
  };

  const getGrowthColor = (growth?: number): string => {
    if (growth === undefined || growth === null) return '#666';
    return growth >= 0 ? '#cf1322' : '#3f8600';
  };

  const growthColor = getGrowthColor(fund.estimated_growth);
  const GrowthIcon = fund.estimated_growth && fund.estimated_growth >= 0 ? ArrowUpOutlined : ArrowDownOutlined;

  return (
    <div
      onClick={() => onSelect(fund.fund_code)}
      style={{
        padding: '10px 12px',
        cursor: 'pointer',
        backgroundColor: isSelected ? 'rgba(24, 144, 255, 0.1)' : 'transparent',
        borderBottom: '1px solid rgba(0, 0, 0, 0.04)',
        transition: 'all 0.2s ease',
        position: 'relative',
        borderRadius: isSelected ? '0 8px 8px 0' : 0,
        marginRight: isSelected ? 8 : 0,
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = 'rgba(24, 144, 255, 0.04)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = 'transparent';
        }
      }}
    >
      {/* Active indicator */}
      {isSelected && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: '50%',
            transform: 'translateY(-50%)',
            width: 3,
            height: 24,
            background: 'linear-gradient(180deg, #1890ff 0%, #36cfc9 100%)',
            borderRadius: '0 3px 3px 0',
          }}
        />
      )}

      {/* Delete button */}
      <Button
        type="text"
        size="small"
        icon={<CloseOutlined />}
        onClick={(e) => {
          e.stopPropagation();
          onRemove(fund.fund_code);
        }}
        style={{
          position: 'absolute',
          right: 4,
          top: '50%',
          transform: 'translateY(-50%)',
          opacity: 0,
          transition: 'opacity 0.2s',
          color: '#999',
        }}
        className="fund-item-delete-btn"
      />

      {/* Fund code and name */}
      <div style={{ marginBottom: 4, paddingRight: 28 }}>
        <span style={{ fontSize: 11, color: '#999', marginRight: 6 }}>
          {fund.fund_code}
        </span>
        {fund.fund_name && fund.fund_name !== fund.fund_code && (
          <span
            style={{
              fontSize: 13,
              color: isSelected ? '#1890ff' : '#333',
              fontWeight: isSelected ? 500 : 400,
            }}
          >
            {fund.fund_name}
          </span>
        )}
      </div>

      {/* NAV data row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          fontSize: 11,
          gap: 10,
          paddingRight: 28,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <span style={{ color: '#999' }}>昨:</span>
          <span style={{ color: '#333', fontWeight: 600 }}>
            {formatNav(fund.previous_nav)}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <span style={{ color: '#999' }}>估:</span>
          <span style={{ color: growthColor, fontWeight: 600 }}>
            {formatNav(fund.estimated_nav)}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <span style={{ color: '#999' }}>涨跌:</span>
          <span style={{ color: growthColor, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 2 }}>
            <GrowthIcon style={{ fontSize: 10 }} />
            {formatGrowth(fund.estimated_growth)}
          </span>
        </div>
      </div>

      <style>{`
        div:hover .fund-item-delete-btn {
          opacity: 1 !important;
        }
      `}</style>
    </div>
  );
};

const WatchlistV2: React.FC = () => {
  const {
    watchlistWithRealtime,
    addToWatchlist,
    removeFromWatchlist,
    currentFundCode,
    setCurrentFundCode,
    isLoading,
    lastUpdate,
    isInWatchlist,
  } = useWatchlist();

  const handleFundSelect = (fund: FundInfo) => {
    addToWatchlist(fund);
    setCurrentFundCode(fund.fund_code);
  };

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

  // Custom sidebar content
  const sidebarContent = (
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
      {/* Search Section */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(0, 0, 0, 0.06)' }}>
        <FundSearch
          onSelect={handleFundSelect}
          placeholder="搜索基金代码或名称"
        />
      </div>

      {/* Header with count */}
      <div
        style={{
          padding: '10px 16px',
          backgroundColor: 'rgba(24, 144, 255, 0.04)',
          borderBottom: '1px solid rgba(0, 0, 0, 0.04)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <Text strong style={{ fontSize: 13 }}>自选基金</Text>
          <Badge
            count={watchlistWithRealtime.length}
            style={{ marginLeft: 8, backgroundColor: '#1890ff', fontSize: 10 }}
            showZero
          />
        </div>
        <Text type="secondary" style={{ fontSize: 10 }}>
          {formatLastUpdate(lastUpdate)}
        </Text>
      </div>

      {/* Fund List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
        {isLoading && watchlistWithRealtime.length === 0 ? (
          <div style={{ padding: '40px 0', textAlign: 'center' }}>
            <Spin size="small" />
            <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>加载中...</div>
          </div>
        ) : watchlistWithRealtime.length === 0 ? (
          <Empty
            description="暂无自选基金"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{ marginTop: 40 }}
          >
            <div style={{ fontSize: 12, color: '#999', textAlign: 'center' }}>
              搜索上方添加基金到自选
            </div>
          </Empty>
        ) : (
          watchlistWithRealtime.map((fund) => (
            <CompactFundItem
              key={fund.fund_code}
              fund={fund}
              isSelected={fund.fund_code === currentFundCode}
              onSelect={setCurrentFundCode}
              onRemove={removeFromWatchlist}
            />
          ))
        )}
      </div>
    </div>
  );

  return (
    <DashboardLayout
      title="自选监控"
      sidebar={sidebarContent}
      sidebarWidth={320}
      showBackButton={true}
    >
      <div className="dash-fade-in">
        {currentFundCode ? (
          <GlassCard hoverable={false}>
            <EmbeddedFundDetail
              fundCode={currentFundCode}
              isInWatchlist={isInWatchlist(currentFundCode)}
              onAddToWatchlist={() => {}}
              onRemoveFromWatchlist={() => removeFromWatchlist(currentFundCode)}
            />
          </GlassCard>
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
            }}
          >
            <GlassCard style={{ textAlign: 'center', padding: 48 }} hoverable={false}>
              <PlusOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
              <div style={{ fontSize: 16, color: '#999', marginBottom: 8 }}>
                请从左侧选择基金
              </div>
              <div style={{ fontSize: 14, color: '#bbb' }}>
                或搜索添加基金到自选列表
              </div>
            </GlassCard>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default WatchlistV2;
