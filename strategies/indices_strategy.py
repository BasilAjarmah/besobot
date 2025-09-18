"""
Indices-specific trading strategy (US30, USTEC)
"""

import pandas as pd
from .base_strategy import BaseStrategy

class IndicesStrategy(BaseStrategy):
    """Trading strategy optimized for indices (US30, USTEC)"""
    
    def calculate_confirmations(self, df, fib_levels, daily_levels, weekly_bias):
        """Indices-specific confirmation calculation"""
        conf_buy = 0
        conf_sell = 0
        reasons = []
        current_price = df['close'].iloc[-1]
        
        # Weekly bias
        if weekly_bias == 'bull':
            conf_buy += 1
            reasons.append("weekly bull")
        elif weekly_bias == 'bear':
            conf_sell += 1
            reasons.append("weekly bear")
        
        # EMA crossover with tighter requirements for indices
        ema_fast = df['EMA_fast'].iloc[-1]
        ema_slow = df['EMA_slow'].iloc[-1]
        ema_diff_pct = abs(ema_fast - ema_slow) / current_price
        
        if ema_fast > ema_slow and ema_diff_pct > 0.001:  # Require meaningful difference
            conf_buy += 1
            reasons.append("EMA bull")
        elif ema_fast < ema_slow and ema_diff_pct > 0.001:
            conf_sell += 1
            reasons.append("EMA bear")
        
        # MACD histogram with strength consideration
        macd_value = df['MACD_HIST'].iloc[-1]
        if macd_value > 0.001:  # Meaningful positive value
            conf_buy += 1
            reasons.append("MACD hist +")
        elif macd_value < -0.001:  # Meaningful negative value
            conf_sell += 1
            reasons.append("MACD hist -")
        
        # RSI with indices-specific levels
        rsi_value = df['RSI'].iloc[-1]
        if rsi_value > 55:
            conf_buy += 1
            reasons.append("RSI>55")
        elif rsi_value < 45:
            conf_sell += 1
            reasons.append("RSI<45")
        
        # Price action confirmation (important for indices)
        previous_close = df['close'].iloc[-2]
        price_change_pct = (current_price - previous_close) / previous_close
        
        if abs(price_change_pct) > 0.003:  # 0.3% move
            if price_change_pct > 0 and weekly_bias == 'bull':
                conf_buy += 0.5
                reasons.append("strong move bull")
            elif price_change_pct < 0 and weekly_bias == 'bear':
                conf_sell += 0.5
                reasons.append("strong move bear")
        
        return {'buy': conf_buy, 'sell': conf_sell, 'reasons': reasons}
    
    def is_false_breakout(self, df_recent, level, direction):
        """Indices-specific false breakout detection"""
        if df_recent.empty:
            return False
            
        last_candle = df_recent.iloc[-1]
        
        # For indices, we look at closing price vs level
        if direction == 'buy':
            closed_above = last_candle['close'] > level
            body_above = (last_candle['open'] > level or last_candle['close'] > level)
        else:
            closed_below = last_candle['close'] < level
            body_below = (last_candle['open'] < level or last_candle['close'] < level)
        
        # Indices often have fake breakouts, so we require strong confirmation
        if direction == 'buy':
            if not closed_above or not body_above:
                return True
        else:
            if not closed_below or not body_below:
                return True
        
        # Check if this is a news-driven spike (large range candle)
        candle_range = last_candle['high'] - last_candle['low']
        avg_range = df_recent['high'].rolling(5).mean().iloc[-1] - df_recent['low'].rolling(5).mean().iloc[-1]
        
        if candle_range > avg_range * 2:
            return True  # Likely news spike, avoid
            
        return False