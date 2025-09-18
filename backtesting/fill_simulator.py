"""
Realistic fill simulation for backtesting
"""

import numpy as np
import pandas as pd
from datetime import time

class FillSimulator:
    def __init__(self, config):
        self.config = config
        self.symbol = config['SYMBOL']
        
    def simulate_entry_fill(self, bar: pd.Series, direction: str, symbol: str) -> float:
        """Simulate realistic entry fill with spread and slippage"""
        # Base spread based on symbol type
        if 'XAU' in symbol or 'XAG' in symbol:
            base_spread = 0.0002  # 2 pips for metals
        elif 'USOIL' in symbol:
            base_spread = 0.003  # 3 cents for oil
        else:
            base_spread = 0.0001  # 1 pip for indices
            
        # Increase spread during volatile times
        volatility_factor = self.calculate_volatility_factor(bar)
        spread = base_spread * volatility_factor
        
        # Add random slippage (normal distribution)
        slippage = np.random.normal(0, spread / 3)
        
        if direction == 'buy':
            fill_price = bar['close'] + (spread / 2) + slippage
        else:
            fill_price = bar['close'] - (spread / 2) + slippage
            
        return fill_price
    
    def simulate_exit_fill(self, bar: pd.Series, direction: str, symbol: str) -> float:
        """Simulate realistic exit fill"""
        return self.simulate_entry_fill(bar, direction, symbol)
    
    def calculate_volatility_factor(self, bar: pd.Series) -> float:
        """Calculate volatility factor for spread adjustment"""
        # Use ATR or price range to determine volatility
        if 'ATR' in bar and not pd.isna(bar['ATR']):
            atr_ratio = bar['ATR'] / bar['close']
            volatility = min(max(atr_ratio * 1000, 1.0), 3.0)  # 1x to 3x
        else:
            # Fallback: use price range
            price_range = (bar['high'] - bar['low']) / bar['close']
            volatility = min(max(price_range * 100, 1.0), 3.0)
            
        return volatility
    
    def is_market_open(self, timestamp) -> bool:
        """Check if market is open based on symbol"""
        hour = timestamp.hour
        
        if 'XAU' in self.symbol or 'XAG' in self.symbol:
            # Gold/silver: mostly 24/5 but with lower liquidity periods
            return not (2 <= hour <= 5)  # Avoid early Asia session
        elif 'USOIL' in self.symbol:
            # Oil: main trading hours
            return 3 <= hour <= 20
        else:
            # Indices: exchange hours
            return 13 <= hour <= 20  # 9AM-4PM EST