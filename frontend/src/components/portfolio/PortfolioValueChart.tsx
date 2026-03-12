/**
 * Portfolio Value Chart Component
 * Displays historical total value trends
 */
import React, { useEffect, useState } from 'react';
import { Card, Spin, Empty, Typography, Radio, Space, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
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

// Dynamically import echarts
let echarts: any = null;
if (typeof window !== 'undefined') {
  import('echarts').then((module) => {
    echarts = module;
  });
}

export const PortfolioValueChart: React.FC<PortfolioValueChartProps> = ({ portfolioId }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<PortfolioHistory | null>(null);
  const [period, setPeriod] = useState('30d');
  const chartRef = React.useRef<HTMLDivElement>(null);
  const chartInstance = React.useRef<any>(null);

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
    if (!data?.data?.length || !chartRef.current || !echarts) {
      return;
    }

    // Destroy existing chart
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    // Initialize chart
    chartInstance.current = echarts.init(chartRef.current);

    const dates = data.data.map((d) => d.date);
    const values = data.data.map((d) => d.total_value);
    const costs = data.data.map((d) => d.total_cost);

    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const date = params[0].axisValue;
          const value = params.find((p) => p.seriesName === '总市值')?.value || 0;
          const cost = params.find((p) => p.seriesName === '总成本')?.value || 0;
          const profit = value - cost;
          const profitRate = cost > 0 ? ((profit / cost) * 100).toFixed(2) : '0.00';
          const color = profit >= 0 ? '#cf1322' : '#3f8600';

          return `
            <div style="font-weight: bold; margin-bottom: 4px;">${date}</div>
            <div>总市值: ¥${Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</div>
            <div>总成本: ¥${Number(cost).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}</div>
            <div style="color: ${color}">收益: ${profit >= 0 ? '+' : ''}¥${Number(profit).toLocaleString('zh-CN', { minimumFractionDigits: 2 })} (${profitRate}%)</div>
          `;
        },
      },
      legend: {
        data: ['总市值', '总成本'],
        bottom: 0,
      },
      grid: {
        left: '3%',
        right: '4%',
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
      yAxis: {
        type: 'value',
        name: '金额(元)',
        axisLabel: {
          formatter: (value: number) => {
            if (value >= 10000) {
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
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
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
  }, [data]);

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

    return {
      current: last.total_value,
      start: first.total_value,
      max,
      min,
      change: last.total_value - first.total_value,
      changeRate: first.total_value > 0 ? ((last.total_value - first.total_value) / first.total_value) * 100 : 0,
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
  const color = isPositive ? '#cf1322' : '#3f8600';

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
            title="区间涨跌"
            value={stats.changeRate}
            precision={2}
            suffix="%"
            valueStyle={{ color }}
            prefix={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          />
          <Statistic title="区间最高" value={stats.max} precision={2} prefix="¥" />
          <Statistic title="区间最低" value={stats.min} precision={2} prefix="¥" />
        </Space>
      )}

      <div ref={chartRef} style={{ width: '100%', height: 300 }} />
    </Card>
  );
};

export default PortfolioValueChart;
