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
import PortfolioManager from './pages/PortfolioManager';
import Watchlist from './pages/Watchlist';
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
            <Route path="/portfolio" element={<ProtectedRoute><PortfolioManager /></ProtectedRoute>} />
            <Route path="/watchlist" element={<ProtectedRoute><Watchlist /></ProtectedRoute>} />
          </Routes>
        </Router>
      </AuthProvider>
    </ConfigProvider>
  );
};

export default App;
