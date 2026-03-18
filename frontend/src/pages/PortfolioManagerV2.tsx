/**
 * Portfolio Management Page V2 - Light Tech Style
 * New design consistent with landing page
 */
import React, { useState } from 'react';
import { Button, message, Row, Col } from 'antd';
import { PlusOutlined, FundOutlined } from '@ant-design/icons';
import { usePortfolios } from '../hooks/usePortfolios';
import { usePortfolioRealtime } from '../hooks/usePortfolioRealtime';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import DashboardSidebar from '../components/dashboard/DashboardSidebar';
import CompactFundTable from '../components/dashboard/CompactFundTable';
import PortfolioSummaryCard from '../components/portfolio/PortfolioSummaryCard';
import AddPortfolioModal from '../components/portfolio/AddPortfolioModal';
import ImportFundsModal from '../components/portfolio/ImportFundsModal';
import AddFundModal from '../components/portfolio/AddFundModal';
import TransactionModal from '../components/portfolio/TransactionModal';
import FundDetailDrawer from '../components/portfolio/FundDetailDrawer';
import FundDetailModal from '../components/portfolio/FundDetailModal';
import PortfolioValueChart from '../components/portfolio/PortfolioValueChart';
import PortfolioReturnChart from '../components/portfolio/PortfolioReturnChart';
import { api } from '../services/api';
import type { PortfolioFund, CreateTransactionRequest } from '../types';


const PortfolioManagerV2: React.FC = () => {
  const {
    portfolios,
    currentPortfolio,
    setCurrentPortfolio,
    createPortfolio,
    deletePortfolio,
    addFundToPortfolio,
    removeFundFromPortfolio,
    batchAddFunds,
    refresh: refreshPortfolios,
  } = usePortfolios();

  const { fundsWithRealtime, isLoading: realtimeLoading, lastUpdate, refresh } = usePortfolioRealtime(
    currentPortfolio
  );

  const isLoading = realtimeLoading;

  // Modal states
  const [addPortfolioVisible, setAddPortfolioVisible] = useState(false);
  const [importFundsVisible, setImportFundsVisible] = useState(false);
  const [addFundVisible, setAddFundVisible] = useState(false);

  // Transaction states
  const [selectedFund, setSelectedFund] = useState<PortfolioFund | null>(null);
  const [transactionType, setTransactionType] = useState<'buy' | 'sell'>('buy');
  const [transactionModalVisible, setTransactionModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);

  // Fund detail modal state
  const [fundDetailModalVisible, setFundDetailModalVisible] = useState(false);
  const [selectedFundForDetail, setSelectedFundForDetail] = useState<PortfolioFund | null>(null);

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

  // Handle adding a single fund with first buy transaction
  const handleAddFund = async (
    fundCode: string,
    fundName: string,
    transaction: CreateTransactionRequest
  ) => {
    if (!currentPortfolio) {
      message.warning('请先选择一个组合');
      return;
    }

    try {
      const exists = currentPortfolio.funds.some(f => f.fund_code === fundCode);
      if (exists) {
        message.warning('该基金已在组合中');
        return;
      }

      const portfolioFund: PortfolioFund = {
        fund_code: fundCode,
        fund_name: fundName,
        shares: 0,
      };
      await addFundToPortfolio(currentPortfolio.id, portfolioFund);
      await api.createTransaction(currentPortfolio.id, fundCode, transaction);

      setAddFundVisible(false);
      message.success('基金添加成功（已记录首次买入交易）');

      setTimeout(() => {
        refreshPortfolios();
        refresh();
      }, 100);
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

  const handleViewFundDetail = (fund: PortfolioFund) => {
    setSelectedFundForDetail(fund);
    setFundDetailModalVisible(true);
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
      setTimeout(() => {
        refreshPortfolios();
        refresh();
      }, 100);
    } catch (error) {
      message.error('交易失败');
      console.error(error);
    }
  };

  return (
    <DashboardLayout
      title="基金组合管理"
      sidebar={
        <DashboardSidebar
          portfolios={portfolios}
          currentPortfolio={currentPortfolio}
          onSelect={setCurrentPortfolio}
          onAdd={() => setAddPortfolioVisible(true)}
          onDelete={handleDeletePortfolio}
        />
      }
      sidebarWidth={260}
      showBackButton={true}
    >
      <div className="dash-fade-in">
        {currentPortfolio ? (
          <>
            {/* Summary Card */}
            <div style={{ marginBottom: 24 }}>
              <PortfolioSummaryCard
                funds={fundsWithRealtime}
                portfolioName={currentPortfolio.name}
                lastUpdate={lastUpdate}
                portfolioId={currentPortfolio.id}
              />
            </div>

            {/* Fund Table */}
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.7)',
                backdropFilter: 'blur(10px)',
                borderRadius: 16,
                padding: 16,
                border: '1px solid rgba(255, 255, 255, 0.5)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
                marginBottom: 24,
              }}
            >
              <CompactFundTable
                funds={fundsWithRealtime}
                loading={isLoading}
                onAdd={() => setAddFundVisible(true)}
                onImport={() => setImportFundsVisible(true)}
                onDelete={handleDeleteFunds}
                onRefresh={refresh}
                onViewDetail={handleViewDetail}
                onViewFundDetail={handleViewFundDetail}
                onBuy={handleBuy}
                onSell={handleSell}
              />
            </div>

            {/* Charts Row */}
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.7)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: 16,
                    padding: 16,
                    border: '1px solid rgba(255, 255, 255, 0.5)',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
                  }}
                >
                  <PortfolioValueChart portfolioId={currentPortfolio.id} />
                </div>
              </Col>
              <Col xs={24} lg={12}>
                <div
                  style={{
                    background: 'rgba(255, 255, 255, 0.7)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: 16,
                    padding: 16,
                    border: '1px solid rgba(255, 255, 255, 0.5)',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
                  }}
                >
                  <PortfolioReturnChart portfolioId={currentPortfolio.id} />
                </div>
              </Col>
            </Row>
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
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.7)',
                backdropFilter: 'blur(10px)',
                borderRadius: 20,
                padding: 48,
                textAlign: 'center',
                border: '1px solid rgba(255, 255, 255, 0.5)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
              }}
            >
              <FundOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
              <div style={{ fontSize: 18, color: '#999', marginBottom: 24 }}>
                请先创建一个基金组合
              </div>
              <Button
                type="primary"
                size="large"
                icon={<PlusOutlined />}
                onClick={() => setAddPortfolioVisible(true)}
                style={{
                  background: 'linear-gradient(135deg, #1890ff 0%, #36cfc9 100%)',
                  border: 'none',
                  borderRadius: 8,
                }}
              >
                新建组合
              </Button>
            </div>
          </div>
        )}
      </div>

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

      <TransactionModal
        visible={transactionModalVisible}
        fund={selectedFund}
        type={transactionType}
        onCancel={() => setTransactionModalVisible(false)}
        onConfirm={handleTransactionSubmit}
      />

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

      <FundDetailModal
        visible={fundDetailModalVisible}
        fundCode={selectedFundForDetail?.fund_code || null}
        onClose={() => setFundDetailModalVisible(false)}
      />
    </DashboardLayout>
  );
};

export default PortfolioManagerV2;
