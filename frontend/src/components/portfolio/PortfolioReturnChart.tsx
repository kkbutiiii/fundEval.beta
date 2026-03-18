/**
 * Portfolio Return Chart Component
 * Displays historical return rate trends with daily profit bars
 * (Controlled Component - data passed via props)
 */
import React, { useEffect, useState } from 'react';
import { Card, Spin, Empty, Typography, Radio, Space, Statistic, Divider, Tooltip, Button, message } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import type { PortfolioHistory } from '../../types';

const { Text } = Typography;

interface PortfolioReturnChartProps {
  portfolioId: string;
  data: PortfolioHistory | null;
  loading: boolean;
  period: string;
  calculationMethod: 'twr' | 'holding_return';
  onPeriodChange: (period: string) => void;
  onCalculationMethodChange: (method: 'twr' | 'holding_return') => void;
  onRefresh: () => Promise<void>;
}

const PERIOD_OPTIONS = [
  { label: '近30天', value: '30d' },
  { label: '近60天', value: '60d' },
  { label: '近半年', value: '6m' },
  { label: '今年以来', value: 'ytd' },
];

export const PortfolioReturnChart: React.FC<PortfolioReturnChartProps> = ({
  data,
  loading,
  period,
  calculationMethod,
  onPeriodChange,
  onCalculationMethodChange,
  onRefresh,
}) => {
  const [echartsReady, setEchartsReady] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
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
    const dailyProfits = data.data.map((d) => d.daily_profit);
    const isEstimated = data.data.map((d) => d.is_estimated);

    // Calculate zero line
    const zeroLine = new Array(dates.length).fill(0);

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
        formatter: (params: any[]) => {
          const date = params[0].axisValue;
          const returnData = params.find((p) => p.seriesName === '收益率');
          const profitData = params.find((p) => p.seriesName === '当日收益额');
          const dataIndex = params[0].dataIndex;
          const estimated = isEstimated[dataIndex];

          const returnValue = returnData?.value || 0;
          const profitValue = profitData?.value || 0;
          const returnColor = returnValue >= 0 ? '#cf1322' : '#3f8600';
          const profitColor = profitValue >= 0 ? '#ff4d4f' : '#52c41a';
          const estimatedMark = estimated ? ' <span style="color:#999">(估)</span>' : '';

          return `
            <div style="font-weight: bold; margin-bottom: 4px;">${date}${estimatedMark}</div>
            <div style="color: ${returnColor}">收益率: ${returnValue >= 0 ? '+' : ''}${Number(returnValue).toFixed(2)}%</div>
            <div style="color: ${profitColor}">当日收益: ${profitValue >= 0 ? '+' : ''}¥${Number(profitValue).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          `;
        },
      },
      legend: {
        data: ['收益率', '当日收益额', '零线'],
        bottom: 0,
      },
      grid: {
        left: '3%',
        right: '3%',   // 与左侧保持一致，containLabel 会自动处理标签空间
        bottom: '15%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: true,  // Changed to true for bar chart
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
          name: '收益率(%)',
          position: 'left',
          axisLabel: {
            formatter: '{value}%',
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
            },
          },
        },
        {
          type: 'value',
          name: '当日收益(元)',
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
          name: '当日收益额',
          type: 'bar',
          yAxisIndex: 1,  // Use right y-axis
          data: dailyProfits.map((value: number, index: number) => {
            const estimated = isEstimated[index];
            return {
              value: value,
              itemStyle: {
                color: estimated
                  ? (value >= 0 ? 'rgba(255, 77, 79, 0.5)' : 'rgba(82, 196, 26, 0.5)')  // Semi-transparent for estimated
                  : (value >= 0 ? '#ff4d4f' : '#52c41a'),  // Solid color for actual
              },
            };
          }),
          barMaxWidth: 20,
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
    onPeriodChange(e.target.value);
  };

  const handleCalculationMethodChange = (e: any) => {
    onCalculationMethodChange(e.target.value);
  };

  const handleRecalculate = async () => {
    setRecalculating(true);
    try {
      await onRefresh();
    } catch (error) {
      console.error('Failed to recalculate:', error);
      message.error('重新计算失败');
    } finally {
      setRecalculating(false);
    }
  };

  // Calculate statistics
  const stats = React.useMemo(() => {
    if (!data?.data?.length) return null;

    const first = data.data[0];
    const last = data.data[data.data.length - 1];
    const max = Math.max(...data.data.map((d) => d.return_rate));
    const min = Math.min(...data.data.map((d) => d.return_rate));

    // 使用 lifetime_return_rate（组合构建以来的累计收益率）解决问题3
    const lifetimeReturn = last.lifetime_return_rate !== undefined
      ? last.lifetime_return_rate
      : last.return_rate;

    return {
      current: lifetimeReturn,  // 使用累计收益率替代区间收益率
      start: first.return_rate,
      max,
      min,
      change: last.return_rate - first.return_rate,
      twr: last.twr,
      xirr: last.xirr,
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
      style={{ height: '100%', background: 'transparent' }}
      bordered={false}
      extra={
        <Space>
          {/* 重新计算按钮 */}
          <Tooltip title="清除缓存并重新计算">
            <Button
              icon={<ReloadOutlined spin={recalculating} />}
              onClick={handleRecalculate}
              loading={recalculating}
              size="small"
            >
              重新计算
            </Button>
          </Tooltip>

          <Radio.Group value={calculationMethod} onChange={handleCalculationMethodChange} size="small" optionType="button" buttonStyle="solid">
            <Radio.Button value="holding_return">持仓收益率</Radio.Button>
            <Radio.Button value="twr">时间加权(TWR)</Radio.Button>
          </Radio.Group>
          <Radio.Group value={period} onChange={handlePeriodChange} size="small">
            {PERIOD_OPTIONS.map((opt) => (
              <Radio.Button key={opt.value} value={opt.value}>
                {opt.label}
              </Radio.Button>
            ))}
          </Radio.Group>
        </Space>
      }
    >
      {stats && (
        <Space size="large" style={{ marginBottom: 16 }}>
          {/* <Statistic
            title="历史总收益"
            value={stats.current}
            precision={2}
            suffix="%"
            valueStyle={{ color }}
            prefix={isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          /> */}
          <Statistic
            title="区间收益"
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

      <Divider style={{ margin: '16px 0 8px 0' }} />

      {/* Return Rate Calculation Explanation */}
      <div style={{ fontSize: 12, color: '#999', lineHeight: 1.6 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          <InfoCircleOutlined style={{ marginRight: 4 }} />
          收益率计算说明：
        </Text>
        <div style={{ marginLeft: 16, marginTop: 4 }}>
          {calculationMethod === 'twr' ? (
            <>
              <div>• <strong>时间加权(TWR)</strong> = 母基金净值累积收益率，剔除资金进出影响</div>
              <div>• 将组合视为母基金，份额仅在资金进出时变化，内部调仓不影响</div>
              <div>• 可与基金净值走势直接对比，反映投资能力</div>
            </>
          ) : (
            <>
              <div>• <strong>持仓收益率</strong> = (当前持仓市值 - 持仓成本) / 持仓成本 × 100%</div>
              <div>• 持仓成本 = 累计买入金额 - 累计卖出金额（加权成本法）</div>
              <div>• 反映当前持仓的实际盈亏情况，卖出盈利会直接扣减成本</div>
            </>
          )}
          <div>• <strong>当日收益额柱状图</strong>：红色=盈利，绿色=亏损，半透明=使用估算净值</div>
        </div>
      </div>
    </Card>
  );
};

export default PortfolioReturnChart;
