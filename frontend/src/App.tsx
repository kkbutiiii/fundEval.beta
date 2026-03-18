/**
 * Main application component.
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import FundDetail from './pages/FundDetail';
import FundDetailV2 from './pages/FundDetailV2';
import PortfolioManager from './pages/PortfolioManager';
import PortfolioManagerV2 from './pages/PortfolioManagerV2';
import Watchlist from './pages/Watchlist';
import WatchlistV2 from './pages/WatchlistV2';
import Register from './pages/Register';
import LandingPage from './pages/LandingPage';

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/register" element={<Register />} />

            {/* Protected routes */}
            <Route path="/fund/:fundCode" element={<ProtectedRoute><FundDetail /></ProtectedRoute>} />
            <Route path="/fund-v2/:fundCode" element={<ProtectedRoute><FundDetailV2 /></ProtectedRoute>} />
            <Route path="/portfolio" element={<ProtectedRoute><PortfolioManager /></ProtectedRoute>} />
            <Route path="/portfolio-v2" element={<ProtectedRoute><PortfolioManagerV2 /></ProtectedRoute>} />
            <Route path="/watchlist" element={<ProtectedRoute><Watchlist /></ProtectedRoute>} />
            <Route path="/watchlist-v2" element={<ProtectedRoute><WatchlistV2 /></ProtectedRoute>} />
          </Routes>
        </Router>
      </AuthProvider>
    </ConfigProvider>
  );
};

export default App;
