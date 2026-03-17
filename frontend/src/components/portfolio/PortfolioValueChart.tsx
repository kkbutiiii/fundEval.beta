/**
 * Portfolio Value Chart Component
 * Displays historical total value trends with total profit line
 */
import React, { useEffect, useState } from 'react';
import { Card, Spin, Empty, Typography, Radio, Space, Statistic, Divider } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined } from '@ant-design/icons';
import type { PortfolioHistory } from '../../types';
import { api } from '../../services/api';

const { Text } = Typography;

interface PortfolioValueChartProps {
  portfolioId: string;
}

const PERIOD_OPTIONS = [
  { label: '近30天', value: '30d' },
  { label: '近60天', value: '60d' },
  { label: '近半年', value: '6m' },
  { label: '今年以来', value: 'ytd' },
];

export const PortfolioValueChart: React.FC<PortfolioValueChartProps> = ({ portfolioId }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<PortfolioHistory | null>(null);
  const [period, setPeriod] = useState('30d');
  const [echartsReady, setEchartsReady] = useState(false);
  const chartRef = React.useRef<HTMLDivElement>(null);
  const chartInstance = React.useRef<any>(null);
  const echartsModule = React.useRef<any>(null);

  // Dynamically import echarts and track loading state
  useEffect(() => {
    if (typeof window !== 'undefined') {
      import('echarts').then((module) => {
        echartsModule.current = module;
        setEchartsReady(true);
      });
    }
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      if (!portfolioId) return;

      setLoading(true);
      try {
        const result = await api.getPortfolioHistory(portfolioId, period);
        setData(result);
      } catch (error) {
        console.error('Failed to fetch portfolio history:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [portfolioId, period]);

  useEffect(() => {
    if (!data?.data?.length || !chartRef.current || !echartsReady || !echartsModule.current) {
      return;
    }

    // Destroy existing chart
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    // Initialize chart
    chartInstance.current = echartsModule.current.init(chartRef.current);

    const dates = data.data.map((d) => d.date);
    const values = data.data.map((d) => d.total_value);
    const costs = data.data.map((d) => d.total_cost);
    const profits = data.data.map((d) => d.total_profit);
    const isEstimated = data.data.map((d) => d.is_estimated);

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any[]) => {
          const date = params[0].axisValue;
          const value = params.find((p) => p.seriesName === '总市值')?.value || 0;
          const cost = params.find((p) => p.seriesName === '总成本')?.value || 0;
          const profit = params.find((p) => p.seriesName === '总收益')?.value || 0;
          const dataIndex = params[0].dataIndex;
          const estimated = isEstimated[dataIndex];

          const profitRate = cost > 0 ? ((profit / cost) * 100).toFixed(2) : '0.00';
          const color = profit >= 0 ? '#cf1322' : '#3f8600';
          const estimatedMark = estimated ? ' <span style="color:#999">(估)</span>' : '';

          return `
            <div style="font-weight: bold; margin-bottom: 4px;">${date}${estimatedMark}</div>
            <div>总市值: ¥${Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</div>
            <div>总成本: ¥${Number(cost).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</div>
            <div style="color: ${color}">总收益: ${profit >= 0 ? '+' : ''}¥${Number(profit).toLocaleString('zh-CN', { minimumFractionDigits: 2 })} (${profitRate}%)</div>
          `;
        },
      },
      legend: {
        data: ['总市值', '总成本', '总收益'],
        bottom: 0,
      },
      grid: {
        left: '3%',
        right: '12%',  // Make room for right y-axis
        bottom: '15%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLabel: {
          formatter: (value: string) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}/${date.getDate()}`;
          },
        },
      },
      yAxis: [
        {
          type: 'value',
          name: '金额(元)',
          position: 'left',
          axisLabel: {
            formatter: (value: number) => {
              if (Math.abs(value) >= 10000) {
                return (value / 10000).toFixed(0) + '万';
              }
              return value.toFixed(0);
            },
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
            },
          },
        },
        {
          type: 'value',
          name: '总收益(元)',
          position: 'right',
          axisLabel: {
            formatter: (value: number) => {
              if (Math.abs(value) >= 10000) {
                return (value / 10000).toFixed(1) + '万';
              }
              return value.toFixed(0);
            },
          },
          splitLine: {
            show: false,
          },
        },
      ],
      series: [
        {
          name: '总市值',
          type: 'line',
          data: values,
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 3, color: '#5470c6' },
          itemStyle: { color: '#5470c6' },
          areaStyle: {
            color: new echartsModule.current.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
              { offset: 1, color: 'rgba(84, 112, 198, 0.05)' },
            ]),
          },
        },
        {
          name: '总成本',
          type: 'line',
          data: costs,
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 2, color: '#91cc75', type: 'dashed' },
          itemStyle: { color: '#91cc75' },
        },
        {
          name: '总收益',
          type: 'line',
          yAxisIndex: 1,  // Use right y-axis
          data: profits.map((value: number, index: number) => {
            const estimated = isEstimated[index];
            return {
              value: value,
              lineStyle: estimated
                ? { type: 'dashed', color: value >= 0 ? '#ff4d4f' : '#52c41a' }
                : { color: value >= 0 ? '#ff4d4f' : '#52c41a' },
              itemStyle: {
                color: estimated
                  ? (value >= 0 ? 'rgba(255, 77, 79, 0.6)' : 'rgba(82, 196, 26, 0.6)')
                  : (value >= 0 ? '#ff4d4f' : '#52c41a'),
              },
            };
          }),
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
        },
      ],
    };

    chartInstance.current.setOption(option);

    // Handle resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
      chartInstance.current = null;
    };
  }, [data, echartsReady]);

  const handlePeriodChange = (e: any) => {
    setPeriod(e.target.value);
  };

  // Calculate statistics
  const stats = React.useMemo(() => {
    if (!data?.data?.length) return null;

    const first = data.data[0];
    const last = data.data[data.data.length - 1];
    const max = Math.max(...data.data.map((d) => d.total_value));
    const min = Math.min(...data.data.map((d) => d.total_value));
    const maxProfit = Math.max(...data.data.map((d) => d.total_profit));
    const minProfit = Math.min(...data.data.map((d) => d.total_profit));

    return {
      current: last.total_value,
      start: first.total_value,
      max,
      min,
      change: last.total_value - first.total_value,
      changeRate: first.total_value > 0 ? ((last.total_value - first.total_value) / first.total_value) * 100 : 0,
      currentProfit: last.total_profit,
      maxProfit,
      minProfit,
    };
  }, [data]);

  if (loading) {
    return (
      <Card title="总资产走势" style={{ height: '100%' }}>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">加载历史数据...</Text>
          </div>
        </div>
      </Card>
    );
  }

  if (!data?.data?.length) {
    return (
      <Card title="总资产走势" style={{ height: '100%' }}>
        <Empty description="暂无历史数据" />
      </Card>
    );
  }

  const isPositive = (stats?.change || 0) >= 0;
  const isProfitPositive = (stats?.currentProfit || 0) >= 0;
  const color = isPositive ? '#cf1322' : '#3f8600';
  const profitColor = isProfitPositive ? '#cf1322' : '#3f8600';

  return (
    <Card
      title="总资产走势"
      style={{ height: '100%' }}
      extra={
        <Radio.Group value={period} onChange={handlePeriodChange} size="small">
          {PERIOD_OPTIONS.map((opt) => (
            <Radio.Button key={opt.value} value={opt.value}>
              {opt.label}
            </Radio.Button>
          ))}
        </Radio.Group>
      }
    >
      {stats && (
        <Space size="large" style={{ marginBottom: 16 }}>
          <Statistic
            title="当前资产"
            value={stats.current}
            precision={2}
            prefix="¥"
            valueStyle={{ color }}
          />
          <Statistic
            title="当前收益"
            value={stats.currentProfit}
            precision={2}
            prefix={stats.currentProfit >= 0 ? '+' : ''}
            valueStyle={{ color: profitColor }}
          />
          <Statistic
            title="资产变动"
            value={stats.changeRate}
            precision={2}
            suffix="%"
            valueStyle={{ color }}
            prefix={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          />
        </Space>
      )}

      <div ref={chartRef} style={{ width: '100%', height: 300 }} />

      <Divider style={{ margin: '16px 0 8px 0' }} />

      {/* Asset Value Calculation Explanation */}
      <div style={{ fontSize: 12, color: '#999', lineHeight: 1.6 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          <InfoCircleOutlined style={{ marginRight: 4 }} />
          总资产走势说明：
        </Text>
        <div style={{ marginLeft: 16, marginTop: 4 }}>
          <div>• <strong>总市值</strong> = 各基金份额 × 当日净值之和</div>
          <div>• <strong>总成本</strong> = 累计买入金额 - 累计卖出金额</div>
          <div>• <strong>总收益线</strong>（右轴）：总市值 - 总成本，红色=盈利，绿色=亏损，虚线=使用估算净值</div>
          <div>• 周末/节假日使用最近交易日净值，标记为估算</div>
        </div>
      </div>
    </Card>
  );
};

export default PortfolioValueChart;
