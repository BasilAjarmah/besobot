"""
Oil-specific trading strategy
"""

import pandas as pd
from .base_strategy import BaseStrategy

class OilStrategy(BaseStrategy):
    """Trading strategy optimized for oil (USOIL)"""
    
    def calculate_confirmations(self, df, fib_levels, daily_levels, weekly_bias):
        """Oil-specific confirmation calculation"""
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
        
        # EMA crossover (oil responds well to trends)
        ema_fast = df['EMA_fast'].iloc[-1]
        ema_slow = df['EMA_slow'].iloc[-1]
        
        if ema_fast > ema_slow:
            conf_buy += 1.2  # Extra weight for oil trends
            reasons.append("EMA bull")
        else:
            conf_sell += 1.2
            reasons.append("EMA bear")
        
        # MACD histogram
        if df['MACD_HIST'].iloc[-1] > 0:
            conf_buy += 1
            reasons.append("MACD hist +")
        else:
            conf_sell += 1
            reasons.append("MACD hist -")
        
        # RSI with oil-specific levels
        rsi_value = df['RSI'].iloc[-1]
        if rsi_value > 60:  # Higher threshold for oil momentum
            conf_buy += 1
            reasons.append("RSI>60")
        elif rsi_value < 40:  # Lower threshold for oil
            conf_sell += 1
            reasons.append("RSI<40")
        
        # Volume confirmation (important for oil)
        volume_avg = df['tick_volume'].rolling(20).mean().iloc[-1]
        current_volume = df['tick_volume'].iloc[-1]
        
        if current_volume > volume_avg * 1.5:
            if weekly_bias == 'bull':
                conf_buy += 0.5
                reasons.append("high volume bull")
            else:
                conf_sell += 0.5
                reasons.append("high volume bear")
        
        return {'buy': conf_buy, 'sell': conf_sell, 'reasons': reasons}
    
    def is_false_breakout(self, df_recent, level, direction):
        """Oil-specific false breakout detection"""
        if df_recent.empty:
            return False
            
        last_candle = df_recent.iloc[-1]
        body = abs(last_candle['close'] - last_candle['open'])
        
        # Oil can have large wicks, so we're more tolerant
        wick_ratio = self.config.get("FALSE_BREAK_WICK_BODY_RATIO", 1.8)
        if body > 0:
            wick = (last_candle['high'] - last_candle['low']) - body
            if wick / body > wick_ratio:
                return True
        
        # For oil, we require volume confirmation
        current_volume = df_recent['tick_volume'].iloc[-1]
        volume_avg = df_recent['tick_volume'].rolling(5).mean().iloc[-1]
        
        if current_volume < volume_avg * 0.7:
            return True  # Low volume breakout is suspicious for oil
            
        return False