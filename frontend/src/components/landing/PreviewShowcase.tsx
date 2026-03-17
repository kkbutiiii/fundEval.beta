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
const intradayData = [
  { time: '09:30', value: 1.0 },
  { time: '10:00', value: 1.008 },
  { time: '10:30', value: 1.012 },
  { time: '11:00', value: 1.005 },
  { time: '11:30', value: 1.018 },
  { time: '13:00', value: 1.022 },
  { time: '13:30', value: 1.028 },
  { time: '14:00', value: 1.025 },
  { time: '14:30', value: 1.032 },
  { time: '15:00', value: 1.035 },
];

const navData = [
  { date: '01-01', value: 1.0 },
  { date: '01-05', value: 1.02 },
  { date: '01-10', value: 0.99 },
  { date: '01-15', value: 1.05 },
  { date: '01-20', value: 1.08 },
  { date: '01-25', value: 1.12 },
  { date: '01-30', value: 1.15 },
];

const portfolioData = [
  { name: '股票型', value: 45 },
  { name: '债券型', value: 30 },
  { name: '混合型', value: 20 },
  { name: '货币型', value: 5 },
];

const colors = ['#1890ff', '#52c41a', '#faad14', '#722ed1'];

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
      axisLabel: { fontSize: 10, color: '#999' },
    },
    yAxis: {
      type: 'value',
      min: 0.99,
      max: 1.04,
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
      axisLabel: { fontSize: 10, color: '#999' },
    },
    yAxis: {
      type: 'value',
      min: 0.95,
      max: 1.2,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#999' },
      splitLine: { lineStyle: { type: 'dashed', color: 'rgba(0,0,0,0.05)' } },
    },
    series: [{
      type: 'line',
      data: navData.map(d => d.value),
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#52c41a' },
      lineStyle: { color: '#52c41a', width: 2 },
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: 'rgba(0,0,0,0.05)',
      textStyle: { fontSize: 12 },
    },
  }), []);

  // ECharts option for portfolio pie chart
  const pieOption = useMemo(() => ({
    color: colors,
    series: [{
      type: 'pie',
      radius: ['45%', '65%'],
      center: ['40%', '50%'],
      data: portfolioData,
      label: { show: false },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.2)',
        },
      },
    }],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: 'rgba(0,0,0,0.05)',
      textStyle: { fontSize: 12 },
      formatter: '{b}: {c}%',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { fontSize: 11, color: '#666' },
      formatter: (name: string) => {
        const item = portfolioData.find(d => d.name === name);
        return `${name}  ${item?.value}%`;
      },
    },
  }), []);

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
        '创建您的基金组合，实时跟踪整体收益。可视化资产配置，助您优化投资组合结构。',
      features: [
        '自定义基金组合',
        '实时收益计算',
        '资产配置可视化',
        '交易记录管理',
      ],
      chart: (
        <div style={{ height: 200 }}>
          <ReactECharts
            option={pieOption}
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
