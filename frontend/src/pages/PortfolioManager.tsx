/**
 * Main portfolio management page.
 */
import React, { useState } from 'react';
import { Layout, Button, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { usePortfolios } from '../hooks/usePortfolios';
import { usePortfolioRealtime } from '../hooks/usePortfolioRealtime';
import PortfolioSidebar from '../components/portfolio/PortfolioSidebar';
import PortfolioSummaryCard from '../components/portfolio/PortfolioSummaryCard';
import PortfolioFundTable from '../components/portfolio/PortfolioFundTable';
import AddPortfolioModal from '../components/portfolio/AddPortfolioModal';
import ImportFundsModal from '../components/portfolio/ImportFundsModal';
import AddFundModal from '../components/portfolio/AddFundModal';
import TransactionModal from '../components/portfolio/TransactionModal';
import FundDetailDrawer from '../components/portfolio/FundDetailDrawer';
import { api } from '../services/api';
import type { PortfolioFund, CreateTransactionRequest } from '../types';

const { Content, Sider } = Layout;

const PortfolioManager: React.FC = () => {
  const navigate = useNavigate();
  const {
    portfolios,
    currentPortfolio,
    setCurrentPortfolio,
    createPortfolio,
    deletePortfolio,
    addFundToPortfolio,
    removeFundFromPortfolio,
    updateFundShares,
    batchAddFunds,
    loading: portfolioLoading,
  } = usePortfolios();

  const { fundsWithRealtime, isLoading: realtimeLoading, lastUpdate, refresh } = usePortfolioRealtime(
    currentPortfolio
  );

  // Combined loading state
  const isLoading = portfolioLoading || realtimeLoading;

  // Modal states
  const [addPortfolioVisible, setAddPortfolioVisible] = useState(false);
  const [importFundsVisible, setImportFundsVisible] = useState(false);
  const [addFundVisible, setAddFundVisible] = useState(false);

  // Transaction states
  const [selectedFund, setSelectedFund] = useState<PortfolioFund | null>(null);
  const [transactionType, setTransactionType] = useState<'buy' | 'sell'>('buy');
  const [transactionModalVisible, setTransactionModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);

  // Handle portfolio creation
  const handleCreatePortfolio = async (name: string) => {
    try {
      await createPortfolio(name);
      setAddPortfolioVisible(false);
      message.success(`组合 "${name}" 创建成功`);
    } catch (error) {
      message.error('创建组合失败');
      console.error(error);
    }
  };

  // Handle portfolio deletion
  const handleDeletePortfolio = async (id: string) => {
    try {
      await deletePortfolio(id);
      message.success('组合已删除');
    } catch (error) {
      message.error('删除组合失败');
      console.error(error);
    }
  };

  // Handle adding a single fund
  const handleAddFund = async (fund: { fund_code: string; fund_name: string; shares: number }) => {
    if (!currentPortfolio) {
      message.warning('请先选择一个组合');
      return;
    }

    try {
      // Check if fund already exists
      const exists = currentPortfolio.funds.some(f => f.fund_code === fund.fund_code);
      if (exists) {
        message.warning('该基金已在组合中');
        return;
      }

      const portfolioFund: PortfolioFund = {
        fund_code: fund.fund_code,
        fund_name: fund.fund_name,
        shares: fund.shares,
      };

      await addFundToPortfolio(currentPortfolio.id, portfolioFund);
      setAddFundVisible(false);
      message.success('基金添加成功');

      // Refresh to get realtime data for the new fund
      setTimeout(() => refresh(), 100);
    } catch (error) {
      message.error('添加基金失败');
      console.error(error);
    }
  };

  // Handle batch import
  const handleBatchImport = async (codes: string[]) => {
    if (!currentPortfolio) {
      message.warning('请先选择一个组合');
      return;
    }

    if (codes.length === 0) {
      message.warning('请输入基金代码');
      return;
    }

    try {
      message.loading({ content: '正在导入基金...', key: 'import' });

      // Fetch fund info for each code
      const fundPromises = codes.map(async (code) => {
        try {
          const info = await api.getFundInfo(code);
          return {
            fund_code: info.fund_code,
            fund_name: info.fund_name,
            shares: 0,
          };
        } catch (error) {
          console.error(`Failed to get fund info for ${code}:`, error);
          return null;
        }
      });

      const funds = (await Promise.all(fundPromises)).filter(
        (f): f is PortfolioFund => f !== null
      );

      if (funds.length === 0) {
        message.error({ content: '未能找到有效的基金代码', key: 'import' });
        return;
      }

      await batchAddFunds(currentPortfolio.id, funds);
      setImportFundsVisible(false);
      message.success({ content: `成功导入 ${funds.length} 只基金`, key: 'import' });

      // Refresh to get realtime data
      setTimeout(() => refresh(), 100);
    } catch (error) {
      message.error({ content: '导入失败', key: 'import' });
      console.error(error);
    }
  };

  // Handle deleting funds
  const handleDeleteFunds = async (fundCodes: string[]) => {
    if (!currentPortfolio) return;

    try {
      for (const code of fundCodes) {
        await removeFundFromPortfolio(currentPortfolio.id, code);
      }
      message.success(`已删除 ${fundCodes.length} 只基金`);
    } catch (error) {
      message.error('删除基金失败');
      console.error(error);
    }
  };

  // Transaction handlers
  const handleViewDetail = (fund: PortfolioFund) => {
    setSelectedFund(fund);
    setDrawerVisible(true);
  };

  const handleBuy = (fund: PortfolioFund) => {
    setSelectedFund(fund);
    setTransactionType('buy');
    setTransactionModalVisible(true);
  };

  const handleSell = (fund: PortfolioFund) => {
    setSelectedFund(fund);
    setTransactionType('sell');
    setTransactionModalVisible(true);
  };

  const handleTransactionSubmit = async (data: CreateTransactionRequest) => {
    if (!currentPortfolio || !selectedFund) return;

    try {
      await api.createTransaction(currentPortfolio.id, selectedFund.fund_code, data);
      message.success(`${data.transaction_type === 'buy' ? '买入' : '卖出'}成功`);
      setTransactionModalVisible(false);
      // Refresh data
      setTimeout(() => refresh(), 100);
    } catch (error) {
      message.error('交易失败');
      console.error(error);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Sidebar */}
      <Sider
        width={260}
        style={{
          background: '#304156',
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <PortfolioSidebar
          portfolios={portfolios}
          currentPortfolio={currentPortfolio}
          onSelect={setCurrentPortfolio}
          onAdd={() => setAddPortfolioVisible(true)}
          onDelete={handleDeletePortfolio}
        />
      </Sider>

      {/* Main Content */}
      <Layout style={{ marginLeft: 260 }}>
        <Content style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
          {/* Navigation */}
          <div style={{ marginBottom: 24 }}>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/')}
              style={{ marginRight: 16 }}
            >
              返回首页
            </Button>
            <span style={{ fontSize: 20, fontWeight: 500 }}>基金组合管理</span>
          </div>

          {currentPortfolio ? (
            <>
              {/* Summary Card */}
              <PortfolioSummaryCard
                funds={fundsWithRealtime}
                portfolioName={currentPortfolio.name}
                lastUpdate={lastUpdate}
              />

              {/* Fund Table */}
              <PortfolioFundTable
                funds={fundsWithRealtime}
                loading={isLoading}
                onAdd={() => setAddFundVisible(true)}
                onImport={() => setImportFundsVisible(true)}
                onDelete={handleDeleteFunds}
                onRefresh={refresh}
                onViewDetail={handleViewDetail}
                onBuy={handleBuy}
                onSell={handleSell}
              />
            </>
          ) : (
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: 'calc(100vh - 200px)',
                flexDirection: 'column',
              }}
            >
              <div style={{ fontSize: 18, color: '#999', marginBottom: 16 }}>
                请先创建一个基金组合
              </div>
              <Button
                type="primary"
                size="large"
                onClick={() => setAddPortfolioVisible(true)}
              >
                新建组合
              </Button>
            </div>
          )}
        </Content>
      </Layout>

      {/* Modals */}
      <AddPortfolioModal
        visible={addPortfolioVisible}
        onCancel={() => setAddPortfolioVisible(false)}
        onConfirm={handleCreatePortfolio}
      />

      <ImportFundsModal
        visible={importFundsVisible}
        onCancel={() => setImportFundsVisible(false)}
        onConfirm={handleBatchImport}
      />

      <AddFundModal
        visible={addFundVisible}
        onCancel={() => setAddFundVisible(false)}
        onConfirm={handleAddFund}
      />

      {/* Transaction Modal */}
      <TransactionModal
        visible={transactionModalVisible}
        fund={selectedFund}
        type={transactionType}
        onCancel={() => setTransactionModalVisible(false)}
        onConfirm={handleTransactionSubmit}
      />

      {/* Fund Detail Drawer */}
      <FundDetailDrawer
        visible={drawerVisible}
        fund={selectedFund}
        portfolioId={currentPortfolio?.id || ''}
        onClose={() => setDrawerVisible(false)}
        onBuy={() => {
          setTransactionType('buy');
          setTransactionModalVisible(true);
        }}
        onSell={() => {
          setTransactionType('sell');
          setTransactionModalVisible(true);
        }}
      />
    </Layout>
  );
};

export default PortfolioManager;
