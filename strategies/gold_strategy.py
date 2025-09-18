"""
Gold-specific trading strategy
"""

import pandas as pd
from .base_strategy import BaseStrategy

class GoldStrategy(BaseStrategy):
    """Trading strategy optimized for gold (XAUUSD, XAGUSD)"""
    
    def calculate_confirmations(self, df, fib_levels, daily_levels, weekly_bias):
        """Gold-specific confirmation calculation"""
        conf_buy = 0
        conf_sell = 0
        reasons = []
        current_price = df['close'].iloc[-1]
        
        # Weekly bias (gold places more weight on this)
        if weekly_bias == 'bull':
            conf_buy += 1.2  # Extra weight for gold
            reasons.append("weekly bull")
        elif weekly_bias == 'bear':
            conf_sell += 1.2
            reasons.append("weekly bear")
        
        # EMA crossover
        if df['EMA_fast'].iloc[-1] > df['EMA_slow'].iloc[-1]:
            conf_buy += 1
            reasons.append("EMA bull")
        else:
            conf_sell += 1
            reasons.append("EMA bear")
        
        # MACD histogram (gold is sensitive to momentum)
        macd_strength = min(abs(df['MACD_HIST'].iloc[-1]) / 0.001, 2.0)  # Scale to 0-2
        if df['MACD_HIST'].iloc[-1] > 0:
            conf_buy += macd_strength
            reasons.append(f"MACD hist + ({macd_strength:.1f})")
        else:
            conf_sell += macd_strength
            reasons.append(f"MACD hist - ({macd_strength:.1f})")
        
        # RSI with gold-specific levels
        rsi_value = df['RSI'].iloc[-1]
        if rsi_value > 55:  # Higher threshold for gold
            conf_buy += 1
            reasons.append("RSI>55")
        elif rsi_value < 45:  # Lower threshold for gold
            conf_sell += 1
            reasons.append("RSI<45")
        
        # Fibonacci levels (very important for gold)
        if fib_levels:
            nearest_fib = min(fib_levels.items(), key=lambda kv: abs(current_price - kv[1]))
            key, level = nearest_fib
            fib_prox_pct = self.config.get("FIB_PROX_PCT", 0.008)
            
            if abs(current_price - level) / current_price < fib_prox_pct:
                if weekly_bias == 'bull' and key >= 0.382:
                    conf_buy += 1.5  # Strong weight for fib confluence
                    reasons.append("near weekly fib support")
                elif weekly_bias == 'bear' and key <= 0.618:
                    conf_sell += 1.5
                    reasons.append("near weekly fib resistance")
        
        return {'buy': conf_buy, 'sell': conf_sell, 'reasons': reasons}
    
    def is_false_breakout(self, df_recent, level, direction):
        """Gold-specific false breakout detection"""
        if df_recent.empty:
            return False
            
        last_candle = df_recent.iloc[-1]
        body = abs(last_candle['close'] - last_candle['open'])
        wick = (last_candle['high'] - last_candle['low']) - body
        
        # Gold-specific wick ratio
        wick_ratio = self.config.get("FALSE_BREAK_WICK_BODY_RATIO", 1.5)
        if body > 0 and wick / body > wick_ratio:
            return True
            
        # For gold, we require stronger confirmation
        confirmation_candles = 2 if direction == 'buy' else 2
        lookback = min(len(df_recent), confirmation_candles)
        
        if direction == 'buy':
            confirmations = (df_recent['close'].iloc[-lookback:] > level).sum()
        else:
            confirmations = (df_recent['close'].iloc[-lookback:] < level).sum()
            
        if confirmations < 1:
            return True
            
        return False