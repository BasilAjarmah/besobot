"""
Scalping-specific strategy with fast entries/exits
"""

import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy

class ScalpingStrategy(BaseStrategy):
    """Ultra-fast scalping strategy optimized for 1-minute charts"""
    
    def calculate_confirmations(self, df, fib_levels, daily_levels, weekly_bias):
        """Fast scalping confirmation calculation"""
        conf_buy = 0
        conf_sell = 0
        reasons = []
        
        # Use only the most recent 5-10 candles for scalping
        recent = df.tail(10)
        
        # 1. Price action (most important for scalping)
        current_close = recent['close'].iloc[-1]
        prev_close = recent['close'].iloc[-2]
        
        if current_close > prev_close:
            conf_buy += 1
            reasons.append("price up")
        else:
            conf_sell += 1
            reasons.append("price down")
        
        # 2. Very fast EMA crossover (3/8 instead of 9/21)
        ema3 = recent['close'].ewm(span=3).mean().iloc[-1]
        ema8 = recent['close'].ewm(span=8).mean().iloc[-1]
        
        if ema3 > ema8:
            conf_buy += 1
            reasons.append("fast EMA bull")
        else:
            conf_sell += 1
            reasons.append("fast EMA bear")
        
        # 3. Volume spike (critical for scalping)
        avg_volume = recent['tick_volume'].rolling(5).mean().iloc[-1]
        current_volume = recent['tick_volume'].iloc[-1]
        
        if current_volume > avg_volume * 1.5:
            # Volume confirms direction
            if current_close > prev_close:
                conf_buy += 0.5
                reasons.append("volume bull")
            else:
                conf_sell += 0.5
                reasons.append("volume bear")
        
        # 4. Simple RSI for overbought/oversold
        rsi = self.calculate_fast_rsi(recent['close'], 6)
        if rsi < 30:
            conf_buy += 1
            reasons.append("RSI oversold")
        elif rsi > 70:
            conf_sell += 1
            reasons.append("RSI overbought")
        
        return {'buy': conf_buy, 'sell': conf_sell, 'reasons': reasons}
    
    def calculate_fast_rsi(self, series, period):
        """Faster RSI calculation for scalping"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    def is_false_breakout(self, df_recent, level, direction):
        """Simplified false breakout detection for scalping"""
        # For scalping, we're less concerned about false breakouts
        # and more concerned about immediate price action
        return False
    
    def calculate_sl_tp(self, current_price, atr_val, direction):
        """Tighter SL/TP for scalping"""
        sl_multiplier = self.config.get("SL_ATR_MULTIPLIER", 0.5)
        tp_rr = self.config.get("TP_RR", 1.0)
        
        if direction == 'buy':
            sl_price = current_price - (sl_multiplier * atr_val)
            tp_price = current_price + (tp_rr * (current_price - sl_price))
        else:
            sl_price = current_price + (sl_multiplier * atr_val)
            tp_price = current_price - (tp_rr * (sl_price - current_price))
            
        return sl_price, tp_price