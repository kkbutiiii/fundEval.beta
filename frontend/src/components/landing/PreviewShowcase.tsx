/**
 * Preview Showcase - Feature preview section with mock charts
 * Alternating left-right layout
 * Uses ECharts (already installed in project)
 */
import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import {
  BarChartOutlined,
  PieChartOutlined,
  RiseOutlined,
} from '@ant-design/icons';

// Mock data for charts
// Intraday valuation - step-like pattern with plateaus (simulating fund valuation)
const intradayData = [
  { time: '09:30', value: 1.005 },
  { time: '09:35', value: 1.012 },
  { time: '09:40', value: 1.012 },
  { time: '09:45', value: 1.018 },
  { time: '09:50', value: 1.025 },
  { time: '09:55', value: 1.025 },
  { time: '10:00', value: 1.032 },
  { time: '10:05', value: 1.032 },
  { time: '10:10', value: 1.038 },
  { time: '10:15', value: 1.032 },
  { time: '10:20', value: 1.025 },
  { time: '10:25', value: 1.025 },
  { time: '10:30', value: 1.018 },
  { time: '10:35', value: 1.025 },
  { time: '10:40', value: 1.032 },
  { time: '10:45', value: 1.028 },
  { time: '10:50', value: 1.015 },
  { time: '10:55', value: 1.008 },
  { time: '11:00', value: 1.012 },
  { time: '11:05', value: 1.008 },
  { time: '11:10', value: 1.005 },
  { time: '11:15', value: 1.012 },
  { time: '11:20', value: 1.018 },
  { time: '11:25', value: 1.022 },
  { time: '11:30', value: 1.022 },
  { time: '13:00', value: 1.025 },
  { time: '13:05', value: 1.028 },
  { time: '13:10', value: 1.028 },
  { time: '13:15', value: 1.032 },
  { time: '13:20', value: 1.035 },
  { time: '13:25', value: 1.032 },
  { time: '13:30', value: 1.025 },
  { time: '13:35', value: 1.028 },
  { time: '13:40', value: 1.035 },
  { time: '13:45', value: 1.038 },
  { time: '13:50', value: 1.042 },
  { time: '13:55', value: 1.038 },
  { time: '14:00', value: 1.045 },
  { time: '14:05', value: 1.048 },
  { time: '14:10', value: 1.045 },
  { time: '14:15', value: 1.042 },
  { time: '14:20', value: 1.045 },
  { time: '14:25', value: 1.052 },
  { time: '14:30', value: 1.055 },
  { time: '14:35', value: 1.055 },
  { time: '14:40', value: 1.052 },
  { time: '14:45', value: 1.058 },
  { time: '14:50', value: 1.050 },
  { time: '14:55', value: 1.058 },
  { time: '15:00', value: 1.062 },
];

// NAV history data - realistic fund performance with multiple peaks and valleys
const navData = [
  { date: '12-18', value: 1.85 },
  { date: '12-19', value: 1.88 },
  { date: '12-20', value: 1.92 },
  { date: '12-21', value: 1.95 },
  { date: '12-22', value: 1.93 },
  { date: '12-23', value: 1.96 },
  { date: '12-24', value: 1.98 },
  { date: '12-25', value: 1.95 },
  { date: '12-26', value: 1.97 },
  { date: '12-27', value: 1.94 },
  { date: '12-28', value: 1.98 },
  { date: '12-29', value: 2.02 },
  { date: '12-30', value: 2.05 },
  { date: '12-31', value: 2.08 },
  { date: '01-01', value: 2.06 },
  { date: '01-02', value: 2.10 },
  { date: '01-03', value: 2.15 },
  { date: '01-04', value: 2.12 },
  { date: '01-05', value: 2.08 },
  { date: '01-06', value: 2.15 },
  { date: '01-07', value: 2.18 },
  { date: '01-08', value: 2.15 },
  { date: '01-09', value: 2.12 },
  { date: '01-10', value: 2.18 },
  { date: '01-11', value: 2.22 },
  { date: '01-12', value: 2.25 },
  { date: '01-13', value: 2.28 },
  { date: '01-14', value: 2.32 },
  { date: '01-15', value: 2.30 },
  { date: '01-16', value: 2.25 },
  { date: '01-17', value: 2.28 },
  { date: '01-18', value: 2.35 },
  { date: '01-19', value: 2.38 },
  { date: '01-20', value: 2.42 },
  { date: '01-21', value: 2.45 },
  { date: '01-22', value: 2.48 },
  { date: '01-23', value: 2.35 },
  { date: '01-24', value: 2.32 },
  { date: '01-25', value: 2.38 },
  { date: '01-26', value: 2.42 },
  { date: '01-27', value: 2.45 },
  { date: '01-28', value: 2.38 },
  { date: '01-29', value: 2.22 },
  { date: '01-30', value: 2.18 },
  { date: '01-31', value: 2.25 },
  { date: '02-01', value: 2.28 },
  { date: '02-02', value: 2.32 },
  { date: '02-03', value: 2.35 },
  { date: '02-04', value: 2.28 },
  { date: '02-05', value: 2.25 },
  { date: '02-06', value: 2.22 },
  { date: '02-07', value: 2.25 },
  { date: '02-08', value: 2.28 },
  { date: '02-09', value: 2.32 },
  { date: '02-10', value: 2.35 },
  { date: '02-11', value: 2.38 },
  { date: '02-12', value: 2.42 },
  { date: '02-13', value: 2.38 },
  { date: '02-14', value: 2.32 },
  { date: '02-15', value: 2.35 },
  { date: '02-16', value: 2.40 },
  { date: '02-17', value: 2.42 },
  { date: '02-18', value: 2.38 },
  { date: '02-19', value: 2.35 },
  { date: '02-20', value: 2.32 },
  { date: '02-21', value: 2.28 },
  { date: '02-22', value: 2.22 },
  { date: '02-23', value: 2.25 },
  { date: '02-24', value: 2.28 },
  { date: '02-25', value: 2.42 },
  { date: '02-26', value: 2.55 },
  { date: '02-27', value: 2.49 },
  { date: '02-28', value: 2.53 },
  { date: '03-01', value: 2.49 },
  { date: '03-02', value: 2.42 },
  { date: '03-03', value: 2.41 },
  { date: '03-04', value: 2.43 },
  { date: '03-05', value: 2.49 },
  { date: '03-06', value: 2.53 },
  { date: '03-07', value: 2.54 },
  { date: '03-08', value: 2.58 },
  { date: '03-09', value: 2.60 },
  { date: '03-10', value: 2.35 },
  { date: '03-11', value: 2.32 },
  { date: '03-12', value: 2.31 },
  { date: '03-13', value: 2.33 },
  { date: '03-14', value: 2.40 },
  { date: '03-15', value: 2.34 },
  { date: '03-16', value: 2.32 },
  { date: '03-17', value: 2.35 },
  { date: '03-18', value: 2.25 },
];

// Mock data for portfolio return chart (simulated based on real TWR data)
const portfolioReturnData = [
  { date: '1/17', return: 0.2, dailyProfit: -8 },
  { date: '1/20', return: -0.5, dailyProfit: -15 },
  { date: '1/21', return: 4.5, dailyProfit: 72 },
  { date: '1/22', return: 3.8, dailyProfit: -25 },
  { date: '1/23', return: 4.2, dailyProfit: 18 },
  { date: '1/24', return: 2.1, dailyProfit: -42 },
  { date: '1/27', return: 0.5, dailyProfit: -35 },
  { date: '1/28', return: 1.2, dailyProfit: 15 },
  { date: '1/29', return: -0.8, dailyProfit: -22 },
  { date: '1/30', return: -2.5, dailyProfit: -38 },
  { date: '2/3', return: -5.2, dailyProfit: -62 },
  { date: '2/4', return: -7.2, dailyProfit: -22 },
  { date: '2/5', return: -4.8, dailyProfit: 48 },
  { date: '2/6', return: -3.2, dailyProfit: 32 },
  { date: '2/7', return: -2.5, dailyProfit: 15 },
  { date: '2/10', return: -1.8, dailyProfit: 15 },
  { date: '2/11', return: -0.5, dailyProfit: 28 },
  { date: '2/12', return: -1.2, dailyProfit: -15 },
  { date: '2/13', return: -2.0, dailyProfit: -18 },
  { date: '2/14', return: -1.5, dailyProfit: 12 },
  { date: '2/17', return: -2.2, dailyProfit: -18 },
  { date: '2/18', return: -1.8, dailyProfit: 8 },
  { date: '2/19', return: -2.0, dailyProfit: -5 },
  { date: '2/20', return: -1.5, dailyProfit: 12 },
  { date: '2/21', return: -1.8, dailyProfit: -8 },
  { date: '2/24', return: -0.5, dailyProfit: 28 },
  { date: '2/25', return: 0.2, dailyProfit: 15 },
  { date: '2/26', return: -0.3, dailyProfit: -8 },
  { date: '2/27', return: 0.5, dailyProfit: 18 },
  { date: '2/28', return: -0.8, dailyProfit: -28 },
  { date: '3/3', return: -2.5, dailyProfit: -35 },
  { date: '3/4', return: -4.2, dailyProfit: -38 },
  { date: '3/5', return: -5.0, dailyProfit: -18 },
  { date: '3/6', return: -4.5, dailyProfit: 12 },
  { date: '3/7', return: -3.8, dailyProfit: 15 },
  { date: '3/10', return: -5.2, dailyProfit: -32 },
  { date: '3/11', return: -4.8, dailyProfit: 8 },
  { date: '3/12', return: -5.5, dailyProfit: -18 },
  { date: '3/13', return: -6.0, dailyProfit: -12 },
  { date: '3/14', return: -5.8, dailyProfit: 5 },
  { date: '3/17', return: -6.2, dailyProfit: -8 },
  { date: '3/18', return: -6.0, dailyProfit: 5 },
];


interface PreviewItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  features: string[];
  chart: React.ReactNode;
}

const PreviewShowcase: React.FC = () => {
  // ECharts option for intraday area chart
  const intradayOption = useMemo(() => ({
    grid: { top: 10, right: 10, bottom: 30, left: 40 },
    xAxis: {
      type: 'category',
      data: intradayData.map(d => d.time),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 9, color: '#999', interval: 5 },
    },
    yAxis: {
      type: 'value',
      min: 0.98,
      max: 1.06,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#999' },
      splitLine: { lineStyle: { type: 'dashed', color: 'rgba(0,0,0,0.05)' } },
    },
    series: [{
      type: 'line',
      data: intradayData.map(d => d.value),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#1890ff', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0)' },
          ],
        },
      },
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: 'rgba(0,0,0,0.05)',
      textStyle: { fontSize: 12 },
    },
  }), []);

  // ECharts option for NAV line chart
  const navOption = useMemo(() => ({
    grid: { top: 10, right: 10, bottom: 30, left: 40 },
    xAxis: {
      type: 'category',
      data: navData.map(d => d.date),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 9, color: '#999', interval: 9 },
    },
    yAxis: {
      type: 'value',
      min: 1.7,
      max: 2.6,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#999' },
      splitLine: { lineStyle: { type: 'dashed', color: 'rgba(0,0,0,0.05)' } },
    },
    series: [{
      type: 'line',
      data: navData.map(d => d.value),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#52c41a', width: 2 },
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: 'rgba(0,0,0,0.05)',
      textStyle: { fontSize: 12 },
    },
  }), []);

  // ECharts option for portfolio return chart
  const portfolioReturnOption = useMemo(() => {
    const dates = portfolioReturnData.map(d => d.date);
    const returns = portfolioReturnData.map(d => d.return);
    const dailyProfits = portfolioReturnData.map(d => d.dailyProfit);
    const zeroLine = new Array(dates.length).fill(0);

    return {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: 'rgba(0,0,0,0.05)',
        textStyle: { fontSize: 11 },
        formatter: (params: any[]) => {
          const date = params[0].axisValue;
          const returnData = params.find((p: any) => p.seriesName === '收益率');
          const profitData = params.find((p: any) => p.seriesName === '当日收益额');
          const returnValue = returnData?.value || 0;
          const profitValue = profitData?.value || 0;
          const returnColor = returnValue >= 0 ? '#cf1322' : '#3f8600';
          const profitColor = profitValue >= 0 ? '#ff4d4f' : '#52c41a';

          return `
            <div style="font-weight: bold; margin-bottom: 2px; font-size: 11px;">${date}</div>
            <div style="color: ${returnColor}; font-size: 11px;">收益率: ${returnValue >= 0 ? '+' : ''}${returnValue.toFixed(2)}%</div>
            <div style="color: ${profitColor}; font-size: 11px;">当日收益: ${profitValue >= 0 ? '+' : ''}¥${profitValue.toLocaleString('zh-CN')}</div>
          `;
        },
      },
      legend: {
        data: ['收益率', '当日收益额', '零线'],
        bottom: 0,
        itemWidth: 12,
        itemHeight: 8,
        textStyle: { fontSize: 10, color: '#666' },
      },
      grid: {
        left: 8,
        right: 45,
        bottom: 25,
        top: 25,
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        boundaryGap: true,
        data: dates,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { fontSize: 10, color: '#999', interval: 4 },
      },
      yAxis: [
        {
          type: 'value',
          name: '收益率(%)',
          nameTextStyle: { fontSize: 10, color: '#999', padding: [0, 0, 0, 0] },
          position: 'left',
          min: -8,
          max: 6,
          axisLabel: {
            fontSize: 10,
            color: '#999',
            formatter: '{value}%',
          },
          splitLine: { lineStyle: { type: 'dashed', color: 'rgba(0,0,0,0.05)' } },
        },
        {
          type: 'value',
          name: '当日收益(元)',
          nameTextStyle: { fontSize: 10, color: '#999', padding: [0, 0, 0, 0] },
          position: 'right',
          min: -90,
          max: 90,
          axisLabel: {
            fontSize: 10,
            color: '#999',
            formatter: '{value}',
          },
          splitLine: { show: false },
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
            width: 2,
            color: (params: any) => params.value >= 0 ? '#cf1322' : '#3f8600',
          },
          itemStyle: {
            color: (params: any) => params.value >= 0 ? '#cf1322' : '#3f8600',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(207, 19, 34, 0.15)' },
                { offset: 0.5, color: 'rgba(255, 255, 255, 0)' },
                { offset: 1, color: 'rgba(63, 134, 0, 0.15)' },
              ],
            },
          },
        },
        {
          name: '当日收益额',
          type: 'bar',
          yAxisIndex: 1,
          data: dailyProfits.map((value: number) => ({
            value: value,
            itemStyle: {
              color: value >= 0 ? '#ff4d4f' : '#52c41a',
            },
          })),
          barMaxWidth: 6,
          barGap: '10%',
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
          tooltip: { show: false },
        },
      ],
    };
  }, []);

  const previews: PreviewItem[] = [
    {
      key: 'intraday',
      label: '实时估值',
      icon: <BarChartOutlined />,
      title: '实时净值估算，把握每一刻',
      description:
        '基于实时股票行情，结合基金最新持仓数据，秒级更新估值结果。让您在交易日中随时了解基金净值变化趋势。',
      features: [
        '实时股票行情对接',
        '基于季报持仓数据计算',
        '秒级估值更新',
        '日内走势可视化',
      ],
      chart: (
        <div style={{ height: 200 }}>
          <ReactECharts
            option={intradayOption}
            style={{ height: '100%', width: '100%' }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      ),
    },
    {
      key: 'history',
      label: '净值分析',
      icon: <RiseOutlined />,
      title: '历史走势，洞察先机',
      description:
        '查看基金历史净值走势，分析长期表现。支持多种时间维度，帮助您做出更明智的投资决策。',
      features: [
        '历史净值数据查询',
        '多时间维度分析',
        '涨跌幅度统计',
        '同类基金对比',
      ],
      chart: (
        <div style={{ height: 200 }}>
          <ReactECharts
            option={navOption}
            style={{ height: '100%', width: '100%' }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      ),
    },
    {
      key: 'portfolio',
      label: '组合跟踪',
      icon: <PieChartOutlined />,
      title: '组合收益，一目了然',
      description:
        '创建您的基金组合，实时跟踪整体收益。可视化收益率走势，助您优化投资组合结构。',
      features: [
        '自定义基金组合',
        '实时收益计算',
        '收益率走势可视化',
        '交易记录管理',
      ],
      chart: (
        <div style={{ height: 200 }}>
          <ReactECharts
            option={portfolioReturnOption}
            style={{ height: '100%', width: '100%' }}
            opts={{ renderer: 'svg' }}
          />
        </div>
      ),
    },
  ];

  return (
    <section className="preview-section">
      <div className="preview-container">
        {previews.map((preview, index) => (
          <div
            key={preview.key}
            className={`preview-item ${index % 2 === 1 ? 'reverse' : ''}`}
          >
            <div className="preview-content">
              <div className="preview-label">{preview.label}</div>
              <h3 className="preview-title">{preview.title}</h3>
              <p className="preview-desc">{preview.description}</p>
              <ul className="preview-features">
                {preview.features.map((feature, i) => (
                  <li key={i}>{feature}</li>
                ))}
              </ul>
            </div>
            <div className="preview-visual">
              <div className="preview-mockup">
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 16,
                    paddingBottom: 12,
                    borderBottom: '1px solid rgba(0,0,0,0.05)',
                  }}
                >
                  <span style={{ color: '#1890ff' }}>{preview.icon}</span>
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#333' }}>
                    {preview.label}预览
                  </span>
                </div>
                {preview.chart}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default PreviewShowcase;
