/**
 * Individual fund item in the watchlist.
 * Display: Fund code/name in first row, NAV data in second row
 */
import React from 'react';
import { Button } from 'antd';
import { CloseOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import type { WatchlistFundWithRealtime } from '../../hooks/useWatchlist';

interface WatchlistFundItemProps {
  fund: WatchlistFundWithRealtime;
  isSelected: boolean;
  onSelect: (fundCode: string) => void;
  onRemove: (fundCode: string) => void;
}

const WatchlistFundItem: React.FC<WatchlistFundItemProps> = ({
  fund,
  isSelected,
  onSelect,
  onRemove,
}) => {
  const handleClick = () => {
    onSelect(fund.fund_code);
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRemove(fund.fund_code);
  };

  // Format NAV with 4 decimal places
  const formatNav = (nav?: number): string => {
    if (nav === undefined || nav === null) return '--';
    return nav.toFixed(4);
  };

  // Format growth with sign and %
  const formatGrowth = (growth?: number): string => {
    if (growth === undefined || growth === null) return '--';
    const sign = growth >= 0 ? '+' : '';
    return `${sign}${growth.toFixed(2)}%`;
  };

  // Get color based on growth (red for up, green for down - Chinese stock market convention)
  const getGrowthColor = (growth?: number): string => {
    if (growth === undefined || growth === null) return '#666';
    return growth >= 0 ? '#cf1322' : '#3f8600';
  };

  const growthColor = getGrowthColor(fund.estimated_growth);
  const GrowthIcon = fund.estimated_growth && fund.estimated_growth >= 0 ? ArrowUpOutlined : ArrowDownOutlined;

  return (
    <div
      onClick={handleClick}
      style={{
        padding: '10px 12px',
        cursor: 'pointer',
        backgroundColor: isSelected ? '#e6f7ff' : 'transparent',
        borderBottom: '1px solid #f0f0f0',
        transition: 'background-color 0.2s',
        position: 'relative',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = '#fafafa';
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = 'transparent';
        }
      }}
    >
      {/* Delete button - shows on hover */}
      <Button
        type="text"
        size="small"
        icon={<CloseOutlined />}
        onClick={handleRemove}
        style={{
          position: 'absolute',
          right: 4,
          top: '50%',
          transform: 'translateY(-50%)',
          opacity: 0,
          transition: 'opacity 0.2s',
          color: '#999',
        }}
        className="watchlist-delete-btn"
      />

      {/* First row: Fund code and name */}
      <div style={{ marginBottom: 4, paddingRight: 28 }}>
        <span
          style={{
            fontSize: 12,
            color: '#999',
            marginRight: 8,
          }}
        >
          {fund.fund_code}
        </span>
        {fund.fund_name && fund.fund_name !== fund.fund_code && (
          <span
            style={{
              fontSize: 14,
              color: '#333',
              fontWeight: isSelected ? 600 : 500,
            }}
          >
            {fund.fund_name}
          </span>
        )}
      </div>

      {/* Second row: NAV data - horizontal layout */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          fontSize: 12,
          gap: 12,
          paddingRight: 28,
          flexWrap: 'wrap',
        }}
      >
        {/* Previous NAV */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 2, whiteSpace: 'nowrap' }}>
          <span style={{ color: '#999', fontSize: 11 }}>昨净:</span>
          <span
            style={{
              color: '#333',
              fontFamily: '"PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif',
              fontSize: 13,
              fontWeight: 700,
            }}
          >
            {formatNav(fund.previous_nav)}
          </span>
        </div>

        {/* Estimated NAV */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 2, whiteSpace: 'nowrap' }}>
          <span style={{ color: '#999', fontSize: 11 }}>估净:</span>
          <span
            style={{
              color: growthColor,
              fontFamily: '"PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif',
              fontSize: 13,
              fontWeight: 700,
            }}
          >
            {formatNav(fund.estimated_nav)}
          </span>
        </div>

        {/* Estimated Growth */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 2, whiteSpace: 'nowrap' }}>
          <span style={{ color: '#999', fontSize: 11 }}>涨跌:</span>
          <span
            style={{
              color: growthColor,
              fontFamily: '"PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif',
              fontSize: 13,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 2,
            }}
          >
            <GrowthIcon style={{ fontSize: 12 }} />
            {formatGrowth(fund.estimated_growth)}
          </span>
        </div>
      </div>

      <style>{`
        .watchlist-delete-btn {
          opacity: 0 !important;
        }
        div:hover .watchlist-delete-btn {
          opacity: 1 !important;
        }
      `}</style>
    </div>
  );
};

export default WatchlistFundItem;
