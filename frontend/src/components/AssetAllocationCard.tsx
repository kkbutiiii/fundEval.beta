/**
 * Asset Allocation History Card Component
 * Displays historical asset allocation using ECharts
 */
import React, { useEffect, useState } from 'react';
import { Card, Spin, Empty, Typography } from 'antd';
import type { AssetAllocationHistory } from '../types';
import { api } from '../services/api';

const { Text } = Typography;

interface AssetAllocationCardProps {
  fundCode: string;
}

// Dynamically import echarts to avoid SSR issues
let echarts: any = null;
if (typeof window !== 'undefined') {
  import('echarts').then((module) => {
    echarts = module;
  });
}

export const AssetAllocationCard: React.FC<AssetAllocationCardProps> = ({ fundCode }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<AssetAllocationHistory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const chartRef = React.useRef<HTMLDivElement>(null);
  const chartInstance = React.useRef<any>(null);

  useEffect(() => {
    // Delay fetch to avoid competing with slow API requests
    // Asset allocation is fast (~6s) but gets blocked by slow requests
    const timer = setTimeout(() => {
      const fetchData = async () => {
        try {
          setLoading(true);
          const result = await api.getAssetAllocation(fundCode, 8);
          setData(result);
          setError(null);
        } catch (err) {
          setError('获取资产配置数据失败');
          console.error('Error fetching asset allocation:', err);
        } finally {
          setLoading(false);
        }
      };

      fetchData();
    }, 1000); // Delay to let fast requests complete first

    return () => clearTimeout(timer);
  }, [fundCode]);

  useEffect(() => {
    if (!data?.allocations?.length || !chartRef.current || !echarts) {
      return;
    }

    // Destroy existing chart
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    // Initialize chart
    chartInstance.current = echarts.init(chartRef.current);

    // Format data - keep original order (oldest first for left-to-right display)
    const allocations = data.allocations;
    const dates = allocations.map(a => {
      const date = a.report_date;
      return `${date.substring(0, 4)}-${date.substring(4, 6)}`;
    });

    const stockData = allocations.map(a => a.stock_ratio);
    const bondData = allocations.map(a => a.bond_ratio);
    const cashData = allocations.map(a => a.cash_ratio);
    const otherData = allocations.map(a => a.other_ratio);
    const netAssetData = allocations.map(a => a.net_asset || 0); // 净资产单位已经是亿元

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          crossStyle: { color: '#999' }
        },
        formatter: function(params: any[]) {
          let result = params[0].axisValue + '<br/>';
          params.forEach(param => {
            if (param.seriesName === '净资产') {
              result += `${param.marker} ${param.seriesName}: ${param.value.toFixed(2)}亿元<br/>`;
            } else {
              result += `${param.marker} ${param.seriesName}: ${param.value.toFixed(2)}%<br/>`;
            }
          });
          return result;
        }
      },
      legend: {
        data: ['股票占比', '债券占比', '现金占比', '其他占比', '净资产'],
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
        data: dates,
        axisPointer: { type: 'shadow' }
      },
      yAxis: [
        {
          type: 'value',
          name: '占比(%)',
          min: 0,
          max: 100,
          interval: 20,
          axisLabel: { formatter: '{value}%' }
        },
        {
          type: 'value',
          name: '净资产(亿元)',
          axisLabel: { formatter: '{value}' }
        }
      ],
      series: [
        {
          name: '股票占比',
          type: 'bar',
          stack: 'allocation',
          data: stockData,
          itemStyle: { color: '#5470c6' }
        },
        {
          name: '债券占比',
          type: 'bar',
          stack: 'allocation',
          data: bondData,
          itemStyle: { color: '#91cc75' }
        },
        {
          name: '现金占比',
          type: 'bar',
          stack: 'allocation',
          data: cashData,
          itemStyle: { color: '#fac858' }
        },
        {
          name: '其他占比',
          type: 'bar',
          stack: 'allocation',
          data: otherData,
          itemStyle: { color: '#ee6666' }
        },
        {
          name: '净资产',
          type: 'line',
          yAxisIndex: 1,
          data: netAssetData,
          itemStyle: { color: '#ea7ccc' },
          lineStyle: { width: 3 },
          symbol: 'circle',
          symbolSize: 8
        }
      ]
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
    };
  }, [data]);

  if (loading) {
    return (
      <Card title="资产配置历史" style={{ height: '100%' }}>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">加载资产配置数据...</Text>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="资产配置历史" style={{ height: '100%' }}>
        <Empty description={error} />
      </Card>
    );
  }

  if (!data?.allocations?.length) {
    return (
      <Card title="资产配置历史" style={{ height: '100%' }}>
        <Empty description="暂无资产配置数据" />
      </Card>
    );
  }

  return (
    <Card title="资产配置历史趋势" style={{ height: '100%' }}>
      <div ref={chartRef} style={{ width: '100%', height: 320 }} />
      <div style={{ marginTop: 16, textAlign: 'center' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          展示最近{data.allocations.length}个季度的资产配置变化及净资产规模
        </Text>
      </div>
    </Card>
  );
};

export default AssetAllocationCard;
