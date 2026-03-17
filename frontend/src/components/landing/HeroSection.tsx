/**
 * Hero Section - Main visual area with dynamic background
 */
import React from 'react';
import { ThunderboltOutlined } from '@ant-design/icons';
import FundSearch from '../FundSearch';
import type { FundInfo } from '../../types';

interface HeroSectionProps {
  onFundSelect: (fund: FundInfo) => void;
}

const HeroSection: React.FC<HeroSectionProps> = ({
  onFundSelect,
}) => {
  const handleFundSelect = (fund: FundInfo) => {
    onFundSelect(fund);
  };

  return (
    <section className="hero-section">
      {/* Animated grid background */}
      <div className="hero-grid" />

      {/* Gradient orbs */}
      <div className="hero-orb hero-orb-1" />
      <div className="hero-orb hero-orb-2" />

      {/* Content */}
      <div className="hero-content">
        {/* Badge */}
        <div className="hero-badge">
          <ThunderboltOutlined />
          <span>实时估算 · 数据精准 · 免费使用</span>
        </div>

        {/* Title */}
        <h1 className="hero-title">
          华福资管
          <br />
          <span className="hero-title-highlight">基金实时估值平台</span>
        </h1>

        {/* Subtitle */}
        <p className="hero-subtitle">
          基于最新季报持仓数据，结合实时股票行情，
          <br />
          为您提供专业、精准的基金净值估算服务
        </p>

        {/* Search Box */}
        <div className="hero-search-wrapper">
          <FundSearch
            onSelect={handleFundSelect}
            placeholder="输入基金代码或名称搜索（如：000001 或 华夏成长）"
            style={{ width: '100%' }}
          />
        </div>

        {/* Quick Stats */}
        <div className="hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-value">10000+</div>
            <div className="hero-stat-label">支持基金</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">实时</div>
            <div className="hero-stat-label">估值更新</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">99%</div>
            <div className="hero-stat-label">准确率</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
