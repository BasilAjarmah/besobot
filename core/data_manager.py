"""
Data management component
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import logging

logger = logging.getLogger("DataManager")

class DataManager:
    """Handles data retrieval and processing for all instruments"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes cache timeout
    
    def get_rates(self, symbol, timeframe, count):
        """Get rates with caching"""
        cache_key = f"{symbol}_{timeframe}_{count}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < self.cache_timeout:
                return cached_data
        
        # Fetch new data
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"No data for {symbol} timeframe {timeframe}")
                return pd.DataFrame()
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Cache the data
            self.cache[cache_key] = (df, datetime.now())
            return df
            
        except Exception as e:
            logger.error(f"Error fetching rates for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_rates_range(self, symbol, timeframe, from_dt, to_dt):
        """Get rates for a specific date range"""
        try:
            utc_from = int(from_dt.replace(tzinfo=timezone.utc).timestamp())
            utc_to = int(to_dt.replace(tzinfo=timezone.utc).timestamp())
            
            rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
            if rates is None or len(rates) == 0:
                logger.warning(f"No range data for {symbol}")
                return pd.DataFrame()
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            logger.error(f"Error fetching range rates for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df, config):
        """Calculate technical indicators based on config"""
        if df.empty:
            return df
            
        df = df.copy()
        
        # EMA
        df['EMA_fast'] = df['close'].ewm(span=config.get("EMA_FAST", 9), adjust=False).mean()
        df['EMA_slow'] = df['close'].ewm(span=config.get("EMA_SLOW", 21), adjust=False).mean()
        
        # RSI
        df['RSI'] = self.calculate_rsi(df['close'], config.get("RSI_PERIOD", 9))
        
        # MACD
        macd_line, signal_line, hist = self.calculate_macd(
            df['close'], 
            config.get("MACD_FAST", 12),
            config.get("MACD_SLOW", 26),
            config.get("MACD_SIGNAL", 9)
        )
        df['MACD_HIST'] = hist
        
        # ATR
        df['ATR'] = self.calculate_atr(df, config.get("ATR_PERIOD", 14))
        
        # OBV
        df['OBV'] = self.calculate_obv(df)
        
        return df
    
    def calculate_rsi(self, series, period):
        """Calculate RSI"""
        try:
            delta = series.diff()
            up = delta.clip(lower=0)
            down = -delta.clip(upper=0)
            ma_up = up.rolling(window=period, min_periods=1).mean()
            ma_down = down.rolling(window=period, min_periods=1).mean()
            rs = ma_up / (ma_down + 1e-12)
            return 100 - (100 / (1 + rs))
        except Exception:
            return pd.Series([50] * len(series), index=series.index)
    
    def calculate_macd(self, series, fast, slow, signal):
        """Calculate MACD"""
        try:
            fast_ema = series.ewm(span=fast, adjust=False).mean()
            slow_ema = series.ewm(span=slow, adjust=False).mean()
            macd_line = fast_ema - slow_ema
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            hist = macd_line - signal_line
            return macd_line, signal_line, hist
        except Exception:
            empty = pd.Series([0] * len(series), index=series.index)
            return empty, empty, empty
    
    def calculate_atr(self, df, period):
        """Calculate ATR"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            prev_close = close.shift(1)
            tr = pd.concat([high - low, (high - prev_close).abs(), 
                           (low - prev_close).abs()], axis=1).max(axis=1)
            return tr.rolling(window=period).mean()
        except Exception:
            return pd.Series([0] * len(df), index=df.index)
    
    def calculate_obv(self, df):
        """Calculate OBV"""
        try:
            obv_values = [0]
            for i in range(1, len(df)):
                if df['close'].iat[i] > df['close'].iat[i-1]:
                    obv_values.append(obv_values[-1] + df['tick_volume'].iat[i])
                elif df['close'].iat[i] < df['close'].iat[i-1]:
                    obv_values.append(obv_values[-1] - df['tick_volume'].iat[i])
                else:
                    obv_values.append(obv_values[-1])
            return pd.Series(obv_values, index=df.index)
        except Exception:
            return pd.Series([0] * len(df), index=df.index)
    
    def get_fibonacci_levels(self, symbol, lookback_weeks=52):
        """Calculate weekly Fibonacci levels"""
        dfw = self.get_rates(symbol, mt5.TIMEFRAME_W1, lookback_weeks)
        if dfw.empty:
            return {}, "neutral"
            
        try:
            highest = dfw['high'].max()
            lowest = dfw['low'].min()
            diff = highest - lowest
            if diff <= 0:
                return {}, "neutral"
                
            levels = {
                0.0: highest,
                0.236: highest - 0.236 * diff,
                0.382: highest - 0.382 * diff,
                0.5: highest - 0.5 * diff,
                0.618: highest - 0.618 * diff,
                1.0: lowest
            }
            
            # Simple trend bias
            bias = "bull" if dfw['close'].iloc[-1] > dfw['close'].rolling(window=4).mean().iloc[-1] else "bear"
            return levels, bias
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci for {symbol}: {e}")
            return {}, "neutral"
    
    def get_daily_levels(self, symbol, lookback_days=60):
        """Identify daily support and resistance levels"""
        dfd = self.get_rates(symbol, mt5.TIMEFRAME_D1, lookback_days + 1)
        if dfd.empty:
            return {'res': [], 'sup': []}
            
        try:
            # Find significant highs and lows
            highs = dfd['high'].nlargest(10).tolist()
            lows = dfd['low'].nsmallest(10).tolist()
            return {'res': sorted(highs, reverse=True)[:5], 'sup': sorted(lows)[:5]}
        except Exception as e:
            logger.error(f"Error calculating S/R for {symbol}: {e}")
            return {'res': [], 'sup': []}
    
    def clear_cache(self):
        """Clear the data cache"""
        self.cache = {}