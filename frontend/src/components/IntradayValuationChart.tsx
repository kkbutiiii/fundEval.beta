/**
 * Intraday Valuation Chart Component
 * Displays real-time intraday valuation with Wind estimate
 * Supports China A-share market trading hours (9:30-11:30, 13:00-15:00)
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Card, Spin, Empty, Typography, Tag, Statistic, Row, Col } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import type { IntradayValuationData } from '../types';
import { api } from '../services/api';

const { Text } = Typography;

interface IntradayValuationChartProps {
  fundCode: string;
}

// Dynamically import echarts to avoid SSR issues
let echarts: any = null;
if (typeof window !== 'undefined') {
  import('echarts').then((module) => {
    echarts = module;
  });
}

/**
 * Generate trading time points with 2-minute intervals
 * Morning: 9:30-11:30 (61 points), Afternoon: 13:00-15:00 (61 points)
 * Total: 122 points
 */
function generateTradingTimePoints(): string[] {
  const points: string[] = [];

  // Morning session: 9:30-11:30
  for (let h = 9; h <= 11; h++) {
    const startMin = h === 9 ? 30 : 0;
    const endMin = h === 11 ? 31 : 60; // Include 11:30
    for (let m = startMin; m < endMin; m += 2) {
      points.push(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`);
    }
  }

  // Afternoon session: 13:00-15:00
  for (let h = 13; h <= 15; h++) {
    const endMin = h === 15 ? 1 : 60; // Only include 15:00 for the last hour
    for (let m = 0; m < endMin; m += 2) {
      if (h === 15 && m > 0) break;
      points.push(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`);
    }
  }

  return points;
}

// Generate 2-minute interval time points
const TRADING_TIME_POINTS = generateTradingTimePoints();

// X-axis display labels (show at 30 minute intervals)
const X_AXIS_LABELS = [
  '09:30', '10:00', '10:30', '11:00', '11:30',
  '13:00', '13:30', '14:00', '14:30', '15:00'
];

// Index positions in TRADING_TIME_POINTS for X_AXIS_LABELS (2-minute intervals)
// 09:30=0, 10:00=15, 10:30=30, 11:00=45, 11:30=60, 13:00=61, 13:30=76, 14:00=91, 14:30=106, 15:00=121
const X_AXIS_LABEL_INDICES = [0, 15, 30, 45, 60, 61, 76, 91, 106, 121];

// Lunch break indices (11:30 and 13:00) in the 2-minute array
const LUNCH_BREAK_INDICES = [60, 61];

// Trading time constants (in minutes from midnight)
const MORNING_START = 9 * 60 + 30;   // 9:30 = 570
const MORNING_END = 11 * 60 + 30;    // 11:30 = 690
const AFTERNOON_START = 13 * 60;     // 13:00 = 780
const AFTERNOON_END = 15 * 60;       // 15:00 = 900

type MarketStatus = 'trading' | 'morning_closed' | 'afternoon_closed' | 'lunch_break' | 'non_trading_day' | 'before_open';

interface MarketState {
  status: MarketStatus;
  label: string;
  color: string;
}

/**
 * Get current time in minutes from midnight
 */
function getTimeInMinutes(date: Date = new Date()): number {
  return date.getHours() * 60 + date.getMinutes();
}

/**
 * Check if current time is within trading hours
 */
function isTradingTime(date: Date = new Date()): boolean {
  const time = getTimeInMinutes(date);
  const isMorning = time >= MORNING_START && time <= MORNING_END;
  const isAfternoon = time >= AFTERNOON_START && time <= AFTERNOON_END;
  return isMorning || isAfternoon;
}

/**
 * Check if today is a trading day (Monday to Friday, simplified)
 * Note: In production, should use a holiday API to exclude Chinese holidays
 */
function isTradingDay(date: Date = new Date()): boolean {
  const day = date.getDay();
  return day >= 1 && day <= 5; // Monday to Friday
}

/**
 * Get current market status
 */
function getMarketStatus(date: Date = new Date()): MarketState {
  if (!isTradingDay(date)) {
    return { status: 'non_trading_day', label: '非交易日', color: 'default' };
  }

  const time = getTimeInMinutes(date);

  if (time < MORNING_START) {
    return { status: 'before_open', label: '未开盘', color: 'default' };
  }
  if (time > AFTERNOON_END) {
    return { status: 'afternoon_closed', label: '已收盘', color: 'default' };
  }
  if (time > MORNING_END && time < AFTERNOON_START) {
    return { status: 'lunch_break', label: '午间休市', color: 'orange' };
  }

  return { status: 'trading', label: '交易中', color: 'green' };
}

/**
 * Check if auto-refresh should be active
 */
function shouldAutoRefresh(date: Date = new Date()): boolean {
  return isTradingDay(date) && isTradingTime(date);
}

export const IntradayValuationChart: React.FC<IntradayValuationChartProps> = ({ fundCode }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<IntradayValuationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [marketState, setMarketState] = useState<MarketState>(getMarketStatus());
  const chartRef = React.useRef<HTMLDivElement>(null);
  const chartInstance = React.useRef<any>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await api.getIntradayValuation(fundCode);
      setData(result);
      setError(null);
    } catch (err) {
      setError('获取日内估值数据失败');
      console.error('Error fetching intraday valuation:', err);
    } finally {
      setLoading(false);
    }
  }, [fundCode]);

  // Initial load
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh with comprehensive trading time and visibility handling
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    let isActive = true;

    const setupInterval = () => {
      // Clear existing interval
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }

      // Only set up interval if we should auto-refresh and page is visible
      if (!isActive || document.hidden || !shouldAutoRefresh()) {
        return;
      }

      intervalId = setInterval(() => {
        if (shouldAutoRefresh()) {
          fetchData();
        }
      }, 30000);
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page is hidden - pause the interval
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
      } else {
        // Page is visible again - check if we should restart
        if (shouldAutoRefresh()) {
          fetchData();
          setupInterval();
        }
      }
    };

    const handleMarketTimeCheck = () => {
      // Re-check trading time every minute to handle market open/close transitions
      const newState = getMarketStatus();
      setMarketState(newState);

      // Update interval based on current market status
      if (newState.status === 'trading' && !document.hidden) {
        if (!intervalId) {
          setupInterval();
        }
      } else {
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
      }
    };

    // Initial setup
    setupInterval();

    // Event listeners
    document.addEventListener('visibilitychange', handleVisibilityChange);
    const timeCheckInterval = setInterval(handleMarketTimeCheck, 60000);

    return () => {
      isActive = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
      clearInterval(timeCheckInterval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchData]);

  // Map data to fixed trading time axis using nearest-neighbor matching
  const mapDataToTimeAxis = useCallback((history: any[]) => {
    // Convert history to array of { timeInMinutes, value } for easier lookup
    const dataPoints: { time: number; value: number }[] = history.map(item => {
      const [hours, minutes] = item.time.substring(0, 5).split(':').map(Number);
      const timeInMinutes = hours * 60 + minutes;
      return {
        time: timeInMinutes,
        value: item.estimated_change_percent
      };
    }).sort((a, b) => a.time - b.time);

    // Generate data array matching TRADING_TIME_POINTS
    return TRADING_TIME_POINTS.map(time => {
      // Lunch break period should have null values (creates a gap in the line)
      if (time > '11:30' && time < '13:00') {
        return null;
      }

      // Parse target time to minutes
      const [targetHours, targetMinutes] = time.split(':').map(Number);
      const targetTimeInMinutes = targetHours * 60 + targetMinutes;

      // Find the data point closest to this time (within 2 minute tolerance)
      let closestValue: number | null = null;
      let minDiff = Infinity;

      for (const point of dataPoints) {
        const diff = Math.abs(point.time - targetTimeInMinutes);
        if (diff < minDiff && diff <= 2) { // Within 2 minutes tolerance
          minDiff = diff;
          closestValue = point.value;
        }
      }

      return closestValue;
    });
  }, []);

  // Initialize chart instance and update data
  useEffect(() => {
    if (!chartRef.current || !echarts) {
      return;
    }

    // Initialize chart only once
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    // If no data, just set up resize handler and return
    if (!data?.valuation_history?.length) {
      const handleResize = () => {
        chartInstance.current?.resize();
      };
      window.addEventListener('resize', handleResize);
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }

    const history = data.valuation_history;
    const mappedData = mapDataToTimeAxis(history);

    // Check if this is the first data load
    const isFirstLoad = !chartInstance.current.getOption()?.series?.[0]?.data;

    // Build series data
    const series: any[] = [
      {
        name: '估算涨跌幅',
        type: 'line',
        data: mappedData,
        smooth: false,
        symbol: 'circle',
        symbolSize: 4,
        connectNulls: false,
        lineStyle: {
          width: 2,
          color: '#5470c6'
        },
        itemStyle: {
          color: (params: any) => {
            if (params.value === null) return 'transparent';
            return params.value >= 0 ? '#cf1322' : '#3f8600';
          }
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
            { offset: 1, color: 'rgba(84, 112, 198, 0.05)' }
          ])
        },
        // Only add markLine on first load (it's static)
        markLine: isFirstLoad ? {
          silent: true,
          symbol: ['none', 'none'],
          lineStyle: {
            color: '#faad14',
            type: 'dashed',
            width: 1
          },
          data: [
            { xAxis: '11:30' },
            { xAxis: '13:00' }
          ]
        } : undefined
      }
    ];

    // Add Wind estimate line if available
    if (data.west_estimate !== undefined && data.west_estimate !== null) {
      series.push({
        name: 'Wind估算',
        type: 'line',
        data: TRADING_TIME_POINTS.map(time => {
          if (time > '11:30' && time < '13:00') {
            return null;
          }
          return data.west_estimate;
        }),
        lineStyle: {
          width: 2,
          color: '#ee6666',
          type: 'dashed'
        },
        symbol: 'none',
        tooltip: {
          formatter: `Wind估算: ${data.west_estimate?.toFixed(2)}%`
        }
      });
    }

    if (isFirstLoad) {
      // First load: set full option
      const option: any = {
        tooltip: {
          trigger: 'axis',
          formatter: (params: any[]) => {
            const p = params[0];
            if (p.value === null || p.value === undefined) {
              return `${p.axisValue}<br/>暂无数据`;
            }
            const color = p.value >= 0 ? '#cf1322' : '#3f8600';
            return `${p.axisValue}<br/>
              ${p.marker} 估算涨跌幅: <span style="color:${color}">${p.value >= 0 ? '+' : ''}${p.value.toFixed(2)}%</span>`;
          }
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
          data: TRADING_TIME_POINTS,
          min: 0,
          max: TRADING_TIME_POINTS.length - 1,
          axisLabel: {
            interval: 0,
            formatter: (value: string, index: number) => {
              if (X_AXIS_LABEL_INDICES.includes(index)) {
                return value;
              }
              return '';
            },
            rotate: 0,
            color: (value: string, index: number) => {
              if (LUNCH_BREAK_INDICES.includes(index)) {
                return '#faad14';
              }
              return '#666';
            }
          },
          axisTick: {
            alignWithLabel: true,
            interval: (index: number) => X_AXIS_LABEL_INDICES.includes(index),
            lineStyle: {
              color: (index: number) => {
                if (LUNCH_BREAK_INDICES.includes(index)) {
                  return '#faad14';
                }
                return '#ccc';
              }
            }
          },
          splitLine: {
            show: true,
            interval: (index: number) => X_AXIS_LABEL_INDICES.includes(index),
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '涨跌幅(%)',
          axisLabel: {
            formatter: '{value}%'
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0'
            }
          }
        },
        series
      };

      if (data.west_estimate !== undefined && data.west_estimate !== null) {
        option.legend = {
          data: ['估算涨跌幅', 'Wind估算'],
          bottom: 0
        };
      }

      chartInstance.current.setOption(option);
    } else {
      // Subsequent updates: only update series data (smooth animation)
      chartInstance.current.setOption({
        series: series.map(s => ({
          name: s.name,
          data: s.data
        }))
      });
    }

    // Handle resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    // Cleanup on unmount
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, [data, mapDataToTimeAxis]);

  // Get latest value
  const latestValue = data?.valuation_history?.[data.valuation_history.length - 1];
  const isPositive = (latestValue?.estimated_change_percent || 0) >= 0;

  // Card title with market status
  const cardTitle = (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span>实时估值</span>
      <Tag color={marketState.color}>{marketState.label}</Tag>
    </div>
  );

  // Non-trading day message
  if (marketState.status === 'non_trading_day' && !data?.valuation_history?.length) {
    return (
      <Card title={cardTitle} style={{ height: '100%' }}>
        <Empty
          description={
            <span>
              今日为非交易日（周末或节假日）
              <br />
              请在交易日（周一至周五）查看实时估值
            </span>
          }
        />
      </Card>
    );
  }

  if (loading && !data) {
    return (
      <Card title={cardTitle} style={{ height: '100%' }}>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">加载日内估值数据...</Text>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title={cardTitle} style={{ height: '100%' }}>
        <Empty description={error} />
      </Card>
    );
  }

  if (!data?.valuation_history?.length) {
    return (
      <Card title={cardTitle} style={{ height: '100%' }}>
        <Empty description="暂无日内估值数据（需要交易日持续采集）" />
      </Card>
    );
  }

  // Calculate colors based on positive/negative change
  const color = isPositive ? '#cf1322' : '#3f8600';
  const icon = isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />;

  return (
    <Card title={cardTitle} style={{ height: '100%' }}>
      {/* Large Number Display - Estimated NAV and Change Percent */}
      <Row gutter={24} justify="center" style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} style={{ textAlign: 'center' }}>
          <Statistic
            title="估算净值"
            value={latestValue?.estimated_nav || 0}
            precision={4}
            valueStyle={{ color, fontSize: '36px', fontWeight: 'bold' }}
            prefix={icon}
          />
        </Col>
        <Col xs={24} sm={12} style={{ textAlign: 'center' }}>
          <Statistic
            title="估算涨跌幅"
            value={latestValue?.estimated_change_percent || 0}
            precision={2}
            valueStyle={{ color, fontSize: '36px', fontWeight: 'bold' }}
            suffix="%"
            prefix={icon}
          />
        </Col>
      </Row>

      {/* Chart */}
      <div ref={chartRef} style={{ width: '100%', height: 260 }} />

      {/* Info Footer */}
      <div style={{ marginTop: 16, textAlign: 'center' }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {marketState.status === 'trading' ? (
            <>
              <Tag color="green" size="small">自动刷新中</Tag>
              {' '}数据每30秒更新 | {' '}
            </>
          ) : marketState.status === 'lunch_break' ? (
            <>
              <Tag color="orange" size="small">午间休市</Tag>
              {' '}暂停刷新 | {' '}
            </>
          ) : (
            <>
              <Tag size="small">{marketState.label}</Tag>
              {' '}暂停刷新 | {' '}
            </>
          )}
          样本数: {data.sample_count} | 最后更新: {data.last_update || 'N/A'}
        </Text>
      </div>
    </Card>
  );
};

export default IntradayValuationChart;
