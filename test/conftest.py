"""
Pytest configuration and fixtures
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing"""
    dates = pd.date_range('2024-01-01', periods=1000, freq='H')
    
    # Generate realistic price data with some trends
    base_prices = {
        'XAUUSD': 1800,
        'XAGUSD': 22,
        'USOIL': 75,
        'USTEC': 12000,
        'US30': 33000
    }
    
    data = {}
    for symbol, base_price in base_prices.items():
        # Random walk with drift
        returns = np.random.normal(0.0001, 0.002, 1000)  # 0.01% drift, 0.2% volatility
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Add some trends
        trend = np.sin(np.arange(1000) / 50) * base_price * 0.1
        
        data[symbol] = pd.DataFrame({
            'open': prices + trend + np.random.normal(0, 0.001 * base_price, 1000),
            'high': prices + trend + np.random.normal(0.001 * base_price, 0.002 * base_price, 1000),
            'low': prices + trend - np.random.normal(0.001 * base_price, 0.002 * base_price, 1000),
            'close': prices + trend,
            'tick_volume': np.random.randint(100, 10000, 1000)
        }, index=dates)
    
    return data

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'SYMBOL': 'XAUUSD',
        'RISK_PERCENT': 0.3,
        'MIN_LOT': 0.01,
        'MAX_LOT': 5.0,
        'EMA_FAST': 9,
        'EMA_SLOW': 21,
        'RSI_PERIOD': 9,
        'MIN_CONFIRMATIONS': 3
    }