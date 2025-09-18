"""
Advanced exit strategies for position management
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class ExitStrategies:
    @staticmethod
    def trailing_stop_atr(current_price: float, position: Dict, atr_value: float, 
                         multiplier: float = 1.5) -> float:
        """ATR-based trailing stop loss"""
        if position['direction'] == 'buy':
            new_sl = current_price - (atr_value * multiplier)
            current_sl = position.get('sl_price', 0)
            # Only move stop loss up (for long positions)
            return max(new_sl, current_sl)
        else:
            new_sl = current_price + (atr_value * multiplier)
            current_sl = position.get('sl_price', float('inf'))
            # Only move stop loss down (for short positions)
            return min(new_sl, current_sl)
    
    @staticmethod
    def time_based_exit(position: Dict, current_time: datetime, 
                       max_hours: int = 48) -> bool:
        """Exit based on maximum time in trade"""
        entry_time = position['entry_time']
        hours_in_trade = (current_time - entry_time).total_seconds() / 3600
        return hours_in_trade >= max_hours
    
    @staticmethod
    def partial_profit_taking(position: Dict, current_price: float, 
                             levels: List[Tuple[float, float]]) -> float:
        """Take partial profits at specified levels"""
        if position['direction'] == 'buy':
            profit_pct = (current_price - position['entry_price']) / position['entry_price'] * 100
        else:
            profit_pct = (position['entry_price'] - current_price) / position['entry_price'] * 100
        
        # Check if we hit any profit taking levels
        for level_pct, close_pct in levels:
            level_key = f'taken_{level_pct}'
            
            if (profit_pct >= level_pct and not position.get(level_key, False)):
                position[level_key] = True  # Mark this level as taken
                return close_pct  # Percentage of position to close
        
        return 0  # No profit taking at this time
    
    @staticmethod
    def volatility_expansion_exit(df: pd.DataFrame, position: Dict, 
                                 threshold: float = 2.0) -> bool:
        """Exit when volatility expands beyond threshold"""
        if len(df) < 20:
            return False
            
        recent_atr = df['ATR'].iloc[-1]
        avg_atr = df['ATR'].rolling(20).mean().iloc[-1]
        
        if recent_atr > avg_atr * threshold:
            return True
        return False
    
    @staticmethod
    def chandelier_exit(position: Dict, highest_high: float, lowest_low: float, 
                       atr_value: float, multiplier: float = 3.0) -> float:
        """Chandelier exit based on highest high/lowest low"""
        if position['direction'] == 'buy':
            return highest_high - (atr_value * multiplier)
        else:
            return lowest_low + (atr_value * multiplier)
    
    @staticmethod
    def moving_average_exit(df: pd.DataFrame, position: Dict, 
                           ma_period: int = 20) -> bool:
        """Exit when price crosses moving average"""
        if len(df) < ma_period:
            return False
            
        current_price = df['close'].iloc[-1]
        ma = df['close'].rolling(ma_period).mean().iloc[-1]
        
        if position['direction'] == 'buy':
            return current_price < ma
        else:
            return current_price > ma
    
    @staticmethod
    def rsi_extreme_exit(df: pd.DataFrame, position: Dict, 
                        rsi_period: int = 14, 
                        exit_level: float = 70) -> bool:
        """Exit when RSI reaches extreme levels"""
        if len(df) < rsi_period:
            return False
            
        rsi_value = df['RSI'].iloc[-1]
        
        if position['direction'] == 'buy':
            return rsi_value > exit_level  # Exit long if overbought
        else:
            return rsi_value < (100 - exit_level)  # Exit short if oversold

    @staticmethod
    def multi_timeframe_exit(df_daily: pd.DataFrame, df_hourly: pd.DataFrame, 
                            position: Dict) -> bool:
        """Exit based on multi-timeframe analysis"""
        if len(df_daily) < 5 or len(df_hourly) < 20:
            return False
            
        # Daily trend reversal
        daily_trend_bullish = (df_daily['close'].iloc[-1] > df_daily['close'].iloc[-5] and
                              df_daily['close'].iloc[-1] > df_daily['EMA_fast'].iloc[-1])
        daily_trend_bearish = (df_daily['close'].iloc[-1] < df_daily['close'].iloc[-5] and
                              df_daily['close'].iloc[-1] < df_daily['EMA_fast'].iloc[-1])
        
        if position['direction'] == 'buy' and daily_trend_bearish:
            return True
        elif position['direction'] == 'sell' and daily_trend_bullish:
            return True
            
        return False