/**
 * NAV History Chart Component
 * Displays historical NAV with benchmark comparison
 */
import React, { useEffect, useState } from 'react';
import { Card, Spin, Empty, Typography, Radio } from 'antd';
import type { NavHistoryData } from '../types';
import { api } from '../services/api';

const { Text } = Typography;

interface NavHistoryChartProps {
  fundCode: string;
}

const PERIOD_OPTIONS = [
  { label: '近1月', value: '1m' },
  { label: '近3月', value: '3m' },
  { label: '近6月', value: '6m' },
  { label: '近1年', value: '1y' },
  { label: '近2年', value: '2y' },
  { label: '近5年', value: '5y' },
];

const VIEW_MODE_OPTIONS = [
  { label: '涨跌', value: 'change' },
  { label: '净值', value: 'nav' },
];

// Dynamically import echarts to avoid SSR issues
let echarts: any = null;
if (typeof window !== 'undefined') {
  import('echarts').then((module) => {
    echarts = module;
  });
}

export const NavHistoryChart: React.FC<NavHistoryChartProps> = ({ fundCode }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<NavHistoryData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('3m');
  const [viewMode, setViewMode] = useState<'change' | 'nav'>('change');
  const chartRef = React.useRef<HTMLDivElement>(null);
  const chartInstance = React.useRef<any>(null);

  useEffect(() => {
    // Delay fetch to avoid competing with slow API requests
    const timer = setTimeout(() => {
      const fetchData = async () => {
        try {
          setLoading(true);
          const result = await api.getNavHistory(fundCode, period);
          setData(result);
          setError(null);
        } catch (err) {
          setError('获取净值历史数据失败');
          console.error('Error fetching NAV history:', err);
        } finally {
          setLoading(false);
        }
      };

      fetchData();
    }, 1000); // Delay to let fast requests complete first

    return () => clearTimeout(timer);
  }, [fundCode, period]);

  useEffect(() => {
    if (!data || !chartRef.current || !echarts) {
      return;
    }

    // Check if we have any data
    if (!data.fund_nav_history?.length) {
      return;
    }

    // Destroy existing chart
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    // Initialize chart
    chartInstance.current = echarts.init(chartRef.current);

    // Get dates from fund data
    const fundData = data.fund_nav_history;
    const dates = fundData.map(n => n.date);

    let option: any;

    if (viewMode === 'nav') {
      // 单位净值模式 - 显示原始净值
      const navData = fundData.map(n => n.nav);

      option = {
        tooltip: {
          trigger: 'axis',
          formatter: function (params: any[]) {
            const param = params[0];
            return `${param.axisValue}<br/>${param.marker} 单位净值: <strong>${param.value.toFixed(4)}元</strong>`;
          }
        },
        legend: {
          data: ['单位净值'],
          bottom: 0
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: dates,
          axisLabel: {
            formatter: (value: string) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '单位净值(元)',
          scale: true,
          axisLabel: {
            formatter: (value: number) => value.toFixed(2)
          }
        },
        series: [
          {
            name: '单位净值',
            type: 'line',
            data: navData,
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 3, color: '#5470c6' },
            itemStyle: { color: '#5470c6' },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
                  { offset: 1, color: 'rgba(84, 112, 198, 0.05)' }
                ]
              }
            }
          }
        ]
      };
    } else {
      // 涨跌幅模式 - 显示归一化百分比变化
      const benchmarkData = data.benchmark_history || [];
      const marketData = data.market_index_history || [];

      // Find base values for normalization
      const baseNav = fundData[0]?.nav || 1;
      const baseBenchmark = benchmarkData[0]?.close || 1;
      const baseMarket = marketData[0]?.close || 1;

      // Normalize to percentage
      const fundPct = fundData.map(n => ((n.nav / baseNav) - 1) * 100);
      const benchmarkPct = benchmarkData.map((b: { date: string; close: number }) =>
        baseBenchmark > 0 ? ((b.close / baseBenchmark) - 1) * 100 : 0
      );
      const marketPct = marketData.map((m: { date: string; close: number }) =>
        baseMarket > 0 ? ((m.close / baseMarket) - 1) * 100 : 0
      );

      option = {
        tooltip: {
          trigger: 'axis',
          formatter: function (params: any[]) {
            let result = params[0].axisValue + '<br/>';
            params.forEach(param => {
              const color = param.value >= 0 ? '#cf1322' : '#3f8600';
              result += `${param.marker} ${param.seriesName}: <span style="color:${color}">${param.value >= 0 ? '+' : ''}${param.value.toFixed(2)}%</span><br/>`;
            });
            return result;
          }
        },
        legend: {
          data: ['本基金', '业绩基准', '沪深300'],
          bottom: 0
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: dates,
          axisLabel: {
            formatter: (value: string) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '涨跌幅(%)',
          axisLabel: {
            formatter: '{value}%'
          }
        },
        series: [
          {
            name: '本基金',
            type: 'line',
            data: fundPct,
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 3, color: '#5470c6' },
            itemStyle: { color: '#5470c6' }
          },
          {
            name: '业绩基准',
            type: 'line',
            data: benchmarkPct,
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 2, color: '#fac858', type: 'dashed' },
            itemStyle: { color: '#fac858' }
          },
          {
            name: '沪深300',
            type: 'line',
            data: marketPct,
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 2, color: '#91cc75' },
            itemStyle: { color: '#91cc75' }
          }
        ]
      };
    }

    chartInstance.current.setOption(option);

    // Handle resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [data, viewMode]);

  const handlePeriodChange = (e: any) => {
    setPeriod(e.target.value);
  };

  const handleViewModeChange = (e: any) => {
    setViewMode(e.target.value);
  };

  const renderExtra = () => (
    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
      <Radio.Group value={viewMode} onChange={handleViewModeChange} size="small">
        {VIEW_MODE_OPTIONS.map(opt => (
          <Radio.Button key={opt.value} value={opt.value}>
            {opt.label}
          </Radio.Button>
        ))}
      </Radio.Group>
      <Radio.Group value={period} onChange={handlePeriodChange} size="small">
        {PERIOD_OPTIONS.map(opt => (
          <Radio.Button key={opt.value} value={opt.value}>
            {opt.label}
          </Radio.Button>
        ))}
      </Radio.Group>
    </div>
  );

  if (loading) {
    return (
      <Card title="历史净值走势" style={{ height: '100%', background: 'transparent' }} bordered={false} extra={renderExtra()}>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">加载净值历史数据...</Text>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="历史净值走势" style={{ height: '100%', background: 'transparent' }} bordered={false}>
        <Empty description={error} />
      </Card>
    );
  }

  if (!data?.fund_nav_history?.length) {
    return (
      <Card title="历史净值走势" style={{ height: '100%', background: 'transparent' }} bordered={false}>
        <Empty description="暂无净值历史数据" />
      </Card>
    );
  }

  return (
    <Card
      title="历史净值走势"
      style={{ height: '100%', background: 'transparent' }}
      bordered={false}
      extra={renderExtra()}
    >
      <div ref={chartRef} style={{ width: '100%', height: 320 }} />
      {viewMode === 'change' && (
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            与本基金业绩基准（{data.benchmark_name || '未知'}）及沪深300指数对比
          </Text>
        </div>
      )}
    </Card>
  );
};

export default NavHistoryChart;
