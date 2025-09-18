"""
Unit tests for strategy classes
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.gold_strategy import GoldStrategy
from strategies.oil_strategy import OilStrategy
from strategies.indices_strategy import IndicesStrategy
from config.xauusd_config import XAUUSD_CONFIG
from config.usoil_config import USOIL_CONFIG
from config.ustec_config import USTEC_CONFIG

class TestGoldStrategy:
    @pytest.fixture
    def strategy(self):
        return GoldStrategy(XAUUSD_CONFIG)
    
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        data = {
            'open': np.random.uniform(1800, 1900, 100),
            'high': np.random.uniform(1810, 1910, 100),
            'low': np.random.uniform(1790, 1890, 100),
            'close': np.random.uniform(1805, 1905, 100),
            'tick_volume': np.random.randint(100, 1000, 100),
            'EMA_fast': np.random.uniform(1800, 1900, 100),
            'EMA_slow': np.random.uniform(1800, 1900, 100),
            'RSI': np.random.uniform(30, 70, 100),
            'MACD_HIST': np.random.uniform(-0.005, 0.005, 100),
            'ATR': np.random.uniform(1, 5, 100)
        }
        df = pd.DataFrame(data, index=dates)
        return df
    
    def test_calculate_confirmations(self, strategy, sample_data):
        fib_levels = {0.5: 1850, 0.618: 1830, 0.382: 1870}
        daily_levels = {'res': [1890, 1880], 'sup': [1820, 1810]}
        
        result = strategy.calculate_confirmations(sample_data, fib_levels, daily_levels, 'bull')
        
        assert 'buy' in result
        assert 'sell' in result
        assert 'reasons' in result
        assert isinstance(result['buy'], (int, float))
        assert isinstance(result['sell'], (int, float))
        assert isinstance(result['reasons'], list)
    
    def test_is_false_breakout(self, strategy, sample_data):
        result = strategy.is_false_breakout(sample_data.tail(10), 1850, 'buy')
        assert isinstance(result, bool)

class TestOilStrategy:
    @pytest.fixture
    def strategy(self):
        return OilStrategy(USOIL_CONFIG)
    
    def test_calculate_confirmations(self, strategy):
        # Similar test structure as gold strategy
        pass

class TestIndicesStrategy:
    @pytest.fixture
    def strategy(self):
        return IndicesStrategy(USTEC_CONFIG)
    
    def test_calculate_confirmations(self, strategy):
        # Similar test structure as gold strategy
        pass