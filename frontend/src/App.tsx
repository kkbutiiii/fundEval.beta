/**
 * Main application component.
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Home from './pages/Home';
import FundDetail from './pages/FundDetail';
import PortfolioManager from './pages/PortfolioManager';
import Watchlist from './pages/Watchlist';

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/fund/:fundCode" element={<FundDetail />} />
          <Route path="/portfolio" element={<PortfolioManager />} />
          <Route path="/watchlist" element={<Watchlist />} />
        </Routes>
      </Router>
    </ConfigProvider>
  );
};

export default App;
