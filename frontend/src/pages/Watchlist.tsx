/**
 * Watchlist monitoring page with left sidebar and fund detail.
 */
import React from 'react';
import { Layout, Typography, Button, Row, Col } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import WatchlistSidebar from '../components/watchlist/WatchlistSidebar';
import EmbeddedFundDetail from '../components/watchlist/EmbeddedFundDetail';
import { useWatchlist } from '../hooks/useWatchlist';

const { Title } = Typography;
const { Content } = Layout;

const Watchlist: React.FC = () => {
  const navigate = useNavigate();
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

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      {/* Page Header */}
      <div style={{ background: '#fff', borderBottom: '1px solid #f0f0f0', padding: '16px 24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/')}
              style={{ marginRight: 16 }}
            >
              返回首页
            </Button>
            <Title level={4} style={{ margin: 0, display: 'inline' }}>
              自选监控
            </Title>
          </Col>
        </Row>
      </div>

      {/* Main Content */}
      <Content style={{ padding: 0, height: 'calc(100vh - 73px)' }}>
        <Row style={{ height: '100%', margin: 0 }}>
          {/* Left Sidebar - ~30% width */}
          <Col
            span={7}
            style={{
              height: '100%',
              maxWidth: 400,
              padding: 0,
            }}
          >
            <WatchlistSidebar
              funds={watchlistWithRealtime}
              currentFundCode={currentFundCode}
              isLoading={isLoading}
              lastUpdate={lastUpdate}
              onSelectFund={setCurrentFundCode}
              onRemoveFund={removeFromWatchlist}
              onAddFund={addToWatchlist}
            />
          </Col>

          {/* Right Content - ~70% width */}
          <Col
            span={17}
            style={{
              height: '100%',
              overflow: 'auto',
              padding: '24px',
            }}
          >
            {currentFundCode ? (
              <EmbeddedFundDetail
                fundCode={currentFundCode}
                isInWatchlist={isInWatchlist(currentFundCode)}
                onAddToWatchlist={() => {
                  // This will be called when user clicks add in the detail view
                  // But since we're showing from watchlist, this shouldn't happen
                }}
                onRemoveFromWatchlist={() => removeFromWatchlist(currentFundCode)}
              />
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: '#999',
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 16, marginBottom: 8 }}>请从左侧选择基金</div>
                  <div style={{ fontSize: 14 }}>或搜索添加基金到自选列表</div>
                </div>
              </div>
            )}
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default Watchlist;
