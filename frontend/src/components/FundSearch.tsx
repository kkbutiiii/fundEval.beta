/**
 * Fund search component with autocomplete.
 */
import React, { useState, useCallback, useRef } from 'react';
import { AutoComplete, Input, Spin } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { FundInfo } from '../types';
import api from '../services/api';

interface FundSearchProps {
  onSelect: (fund: FundInfo) => void;
  placeholder?: string;
  style?: React.CSSProperties;
}

interface Option {
  value: string;
  label: React.ReactNode;
  fund: FundInfo;
}

const FundSearch: React.FC<FundSearchProps> = ({
  onSelect,
  placeholder = '输入基金代码或名称搜索',
  style,
}) => {
  const [options, setOptions] = useState<Option[]>([]);
  const [loading, setLoading] = useState(false);
  const searchTimeout = useRef<NodeJS.Timeout | null>(null);

  const handleSearch = useCallback(async (value: string) => {
    if (!value || value.length < 2) {
      setOptions([]);
      return;
    }

    // Debounce search
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }

    searchTimeout.current = setTimeout(async () => {
      setLoading(true);
      try {
        const funds = await api.searchFunds(value, 20);
        const newOptions: Option[] = funds.map((fund) => ({
          value: fund.fund_code,
          label: (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>
                <strong>{fund.fund_code}</strong> - {fund.fund_name}
              </span>
              {fund.fund_type && (
                <span style={{ color: '#999', fontSize: '12px' }}>{fund.fund_type}</span>
              )}
            </div>
          ),
          fund,
        }));
        setOptions(newOptions);
      } catch (error) {
        console.error('Search error:', error);
        setOptions([]);
      } finally {
        setLoading(false);
      }
    }, 300);
  }, []);

  const handleSelect = useCallback((value: string, option: Option) => {
    onSelect(option.fund);
    setOptions([]);
  }, [onSelect]);

  return (
    <AutoComplete
      options={options}
      onSearch={handleSearch}
      onSelect={handleSelect}
      style={{ width: '100%', ...style }}
      notFoundContent={loading ? <Spin size="small" /> : '无搜索结果'}
    >
      <Input
        size="large"
        placeholder={placeholder}
        prefix={<SearchOutlined />}
        suffix={loading && <Spin size="small" />}
      />
    </AutoComplete>
  );
};

export default FundSearch;
