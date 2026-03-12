/**
 * Portfolio Return Chart Component
 * Displays historical return rate trends
 */
import React, { useEffect, useState } from 'react';
import { Card, Spin, Empty, Typography, Radio, Space, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import type { PortfolioHistory } from '../../types';
import { api } from '../../services/api';

const { Text } = Typography;

interface PortfolioReturnChartProps {
  portfolioId: string;
}

const PERIOD_OPTIONS = [
  { label: '近30天', value: '30d' },
  { label: '近60天', value: '60d' },
  { label: '近半年', value: '6m' },
  { label: '今年以来', value: 'ytd' },
];

export const PortfolioReturnChart: React.FC<PortfolioReturnChartProps> = ({ portfolioId }) => {
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
    const returns = data.data.map((d) => d.return_rate);

    // Calculate zero line
    const zeroLine = new Array(dates.length).fill(0);

    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const date = params[0].axisValue;
          const value = params.find((p) => p.seriesName === '收益率')?.value || 0;
          const color = value >= 0 ? '#cf1322' : '#3f8600';
          return `
            <div style="font-weight: bold; margin-bottom: 4px;">${date}</div>
            <div style="color: ${color}">收益率: ${value >= 0 ? '+' : ''}${Number(value).toFixed(2)}%</div>
          `;
        },
      },
      legend: {
        data: ['收益率'],
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
        name: '收益率(%)',
        axisLabel: {
          formatter: '{value}%',
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0',
          },
        },
      },
      series: [
        {
          name: '收益率',
          type: 'line',
          data: returns,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 3,
            color: (params: any) => {
              return params.value >= 0 ? '#cf1322' : '#3f8600';
            },
          },
          itemStyle: {
            color: (params: any) => {
              return params.value >= 0 ? '#cf1322' : '#3f8600';
            },
          },
          areaStyle: {
            color: new echartsModule.current.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(207, 19, 34, 0.2)' },
              { offset: 0.5, color: 'rgba(255, 255, 255, 0)' },
              { offset: 1, color: 'rgba(63, 134, 0, 0.2)' },
            ]),
          },
        },
        {
          name: '零线',
          type: 'line',
          data: zeroLine,
          symbol: 'none',
          lineStyle: {
            width: 1,
            color: '#999',
            type: 'dashed',
          },
          tooltip: {
            show: false,
          },
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
    const max = Math.max(...data.data.map((d) => d.return_rate));
    const min = Math.min(...data.data.map((d) => d.return_rate));

    return {
      current: last.return_rate,
      start: first.return_rate,
      max,
      min,
      change: last.return_rate - first.return_rate,
    };
  }, [data]);

  if (loading) {
    return (
      <Card title="收益率走势" style={{ height: '100%' }}>
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
      <Card title="收益率走势" style={{ height: '100%' }}>
        <Empty description="暂无历史数据" />
      </Card>
    );
  }

  const isPositive = (stats?.current || 0) >= 0;
  const color = isPositive ? '#cf1322' : '#3f8600';

  return (
    <Card
      title="收益率走势"
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
            title="当前收益率"
            value={stats.current}
            precision={2}
            suffix="%"
            valueStyle={{ color }}
            prefix={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          />
          <Statistic
            title="区间变动"
            value={stats.change}
            precision={2}
            suffix="%"
            valueStyle={{ color: stats.change >= 0 ? '#cf1322' : '#3f8600' }}
            prefix={stats.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          />
          <Statistic title="区间最高" value={stats.max} precision={2} suffix="%" />
          <Statistic title="区间最低" value={stats.min} precision={2} suffix="%" />
        </Space>
      )}

      <div ref={chartRef} style={{ width: '100%', height: 300 }} />
    </Card>
  );
};

export default PortfolioReturnChart;
