/**
 * Feature Grid - Three core feature cards with glassmorphism effect
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  SearchOutlined,
  WalletOutlined,
  StarOutlined,
} from '@ant-design/icons';

interface FeatureGridProps {
  isAuthenticated: boolean;
  onAuthRequired: (redirectTo: string) => void;
}

interface Feature {
  key: string;
  icon: React.ReactNode;
  iconClass: string;
  title: string;
  description: string;
  path: string;
  preview: React.ReactNode;
}

const MiniSearchPreview: React.FC = () => (
  <div style={{ padding: '8px 0' }}>
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '8px 12px',
        background: 'rgba(24, 144, 255, 0.05)',
        borderRadius: 8,
        marginBottom: 8,
      }}
    >
      <SearchOutlined style={{ color: '#1890ff', fontSize: 14 }} />
      <div style={{ fontSize: 12, color: '#999' }}>搜索基金...</div>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {['000001 华夏成长', '005827 易方达蓝筹', '161725 招商白酒'].map((item, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '6px 8px',
            background: i === 0 ? 'rgba(24, 144, 255, 0.08)' : 'transparent',
            borderRadius: 4,
          }}
        >
          <span style={{ fontSize: 12, color: '#333' }}>{item}</span>
          {i === 0 && (
            <span style={{ fontSize: 11, color: '#ff4d4f', fontWeight: 500 }}>+1.25%</span>
          )}
        </div>
      ))}
    </div>
  </div>
);

const MiniPortfolioPreview: React.FC = () => (
  <div style={{ padding: '8px 0' }}>
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
      }}
    >
      <span style={{ fontSize: 12, color: '#666' }}>我的组合</span>
      <span style={{ fontSize: 14, fontWeight: 600, color: '#ff4d4f' }}>+5.28%</span>
    </div>
    <div className="mini-chart" style={{ height: 50 }}>
      {[40, 55, 45, 60, 50, 70, 65, 75, 80, 72, 85, 90].map((h, i) => (
        <div
          key={i}
          className="mini-chart-bar"
          style={{
            height: `${h}%`,
            background: i > 8 ? '#52c41a' : '#1890ff',
          }}
        />
      ))}
    </div>
  </div>
);

const MiniWatchlistPreview: React.FC = () => (
  <div style={{ padding: '8px 0' }}>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {[
        { name: '华夏成长', code: '000001', change: '+1.25%', up: true },
        { name: '易方达蓝筹', code: '005827', change: '-0.68%', up: false },
        { name: '招商白酒', code: '161725', change: '+2.15%', up: true },
      ].map((fund, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '8px 12px',
            background: 'rgba(255, 255, 255, 0.5)',
            borderRadius: 8,
          }}
        >
          <div>
            <div style={{ fontSize: 12, fontWeight: 500, color: '#333' }}>
              {fund.name}
            </div>
            <div style={{ fontSize: 11, color: '#999' }}>{fund.code}</div>
          </div>
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: fund.up ? '#ff4d4f' : '#52c41a',
            }}
          >
            {fund.change}
          </div>
        </div>
      ))}
    </div>
  </div>
);

const FeatureGrid: React.FC<FeatureGridProps> = ({
  isAuthenticated,
  onAuthRequired,
}) => {
  const navigate = useNavigate();

  const features: Feature[] = [
    {
      key: 'search',
      icon: <SearchOutlined />,
      iconClass: 'feature-card-icon-blue',
      title: '基金搜索',
      description: '支持按基金代码、名称快速搜索，实时查看估算净值和涨跌幅',
      path: '/',
      preview: <MiniSearchPreview />,
    },
    {
      key: 'portfolio',
      icon: <WalletOutlined />,
      iconClass: 'feature-card-icon-green',
      title: '组合管理',
      description: '创建基金组合，录入交易记录，追踪组合实时收益和资产配置',
      path: '/portfolio',
      preview: <MiniPortfolioPreview />,
    },
    {
      key: 'watchlist',
      icon: <StarOutlined />,
      iconClass: 'feature-card-icon-orange',
      title: '自选监控',
      description: '关注感兴趣的基金，实时监控估算净值变化，及时把握投资机会',
      path: '/watchlist',
      preview: <MiniWatchlistPreview />,
    },
  ];

  const handleCardClick = (feature: Feature) => {
    if (feature.key === 'search') {
      // Search is available without login
      const searchWrapper = document.querySelector('.hero-search-wrapper');
      if (searchWrapper) {
        // Scroll to top of the page to ensure search box is visible
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
        // Add highlight animation after scroll starts
        setTimeout(() => {
          searchWrapper.classList.add('highlight');
          // Remove highlight class after animation completes (2 seconds for 2 flashes)
          setTimeout(() => {
            searchWrapper.classList.remove('highlight');
          }, 2000);
        }, 600); // Wait for scroll to complete
      }
    } else if (isAuthenticated) {
      navigate(feature.path);
    } else {
      onAuthRequired(feature.path);
    }
  };

  return (
    <section className="feature-section">
      <div className="feature-container">
        <div className="feature-grid">
          {features.map((feature) => (
            <div
              key={feature.key}
              className="feature-card"
              onClick={() => handleCardClick(feature)}
            >
              <div className={`feature-card-icon ${feature.iconClass}`}>
                {feature.icon}
              </div>
              <h3 className="feature-card-title">{feature.title}</h3>
              <p className="feature-card-desc">{feature.description}</p>
              <div className="feature-card-preview">{feature.preview}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeatureGrid;
