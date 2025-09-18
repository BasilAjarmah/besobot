"""
Enhanced core trading bot functionality with new features
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from services.news_filter import NewsFilter
from strategies.exit_strategies import ExitStrategies
from analytics.performance_tracker import PerformanceTracker

logger = logging.getLogger("MultiInstrumentBot")

class MultiInstrumentBot:
    """Enhanced trading bot with news filtering and advanced exits"""
    
    def __init__(self, strategy, config, news_filter: Optional[NewsFilter] = None):
        self.strategy = strategy
        self.config = config
        self.symbol = config["SYMBOL"]
        self.news_filter = news_filter
        self.exit_strategies = ExitStrategies()
        self.performance_tracker = PerformanceTracker()
        self.equity_peak = 0
        self.daily_equity_start = 0
        self.connection_attempts = 0
        self.open_positions = {}
        self.data_cache = {}
        self.cache_timeout = 300
        self.trading_style = config.get("TRADING_STYLE", "position")
        
    def initialize(self):
        """Initialize MT5 connection and bot state"""
        if self.mt5_connect():
            account = mt5.account_info()
            self.equity_peak = account.equity
            self.daily_equity_start = account.equity
            logger.info(f"Initialized for {self.symbol}. Equity: ${account.equity:.2f}")
            return True
        return False
    
    def mt5_connect(self) -> bool:
        """Connect to MT5 with reconnection logic"""
        try:
            if mt5.initialize():
                account = mt5.account_info()
                if account:
                    logger.info(f"Connected to MT5. Account: {account.login}")
                    self.connection_attempts = 0
                    return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
        
        self.connection_attempts += 1
        if self.connection_attempts <= self.config.get("MAX_RECONNECT_ATTEMPTS", 5):
            time.sleep(self.config.get("RECONNECT_DELAY", 10))
            return self.mt5_connect()
        return False
    
    def shutdown(self):
        """Shutdown MT5 connection"""
        try:
            mt5.shutdown()
            logger.info("MT5 connection closed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def check_connection(self) -> bool:
        """Check if MT5 is connected and reconnect if needed"""
        try:
            account = mt5.account_info()
            if account is None:
                logger.warning("MT5 connection lost, attempting to reconnect")
                return self.mt5_connect()
            return True
        except Exception:
            logger.warning("MT5 connection check failed, attempting to reconnect")
            return self.mt5_connect()
    
    def run_single_cycle(self):
        """Run a single evaluation cycle with enhanced features"""
        try:
            # Check connection first
            if not self.check_connection():
                return
                
            # Check news filter with trading style parameter
            if self.news_filter and self.news_filter.should_avoid_trading(self.symbol, None, self.trading_style):
                logger.info(f"Skipping {self.symbol} due to news event")
                return
                
            # Check risk limits
            if not self.check_risk_limits():
                return
                
            # Check if market is open for this instrument
            if not self.is_market_open():
                return
                
            # Check spread
            if not self.check_spread():
                return
                
            # Fetch data and calculate indicators
            df = self.fetch_data()
            if df.empty:
                return
                
            # Check exit conditions for open positions first
            self.check_exit_conditions(df)
            
            # Only check entry if we don't have a position
            if not self.has_open_position():
                # Get market context
                fib_levels, weekly_bias = self.get_fibonacci_levels()
                daily_levels = self.get_daily_levels()
                
                # Calculate signals
                confirmations = self.strategy.calculate_confirmations(df, fib_levels, daily_levels, weekly_bias)
                
                # Execute if signals are strong enough
                self.execute_if_qualified(df, confirmations, fib_levels, weekly_bias)
            
        except Exception as e:
            logger.error(f"Error in cycle for {self.symbol}: {e}")
    
    def check_risk_limits(self) -> bool:
        """Check if we've hit any risk limits"""
        try:
            account = mt5.account_info()
            if not account:
                return False
                
            equity = account.equity
            balance = account.balance
            
            # Update equity peak
            self.equity_peak = max(self.equity_peak, equity)
            
            # Check daily loss limit
            daily_pnl_pct = ((equity - self.daily_equity_start) / self.daily_equity_start) * 100
            if daily_pnl_pct <= -self.config.get("DAILY_LOSS_LIMIT", 2.0):
                logger.warning(f"Daily loss limit reached: {daily_pnl_pct:.2f}%")
                return False
                
            # Check max drawdown
            drawdown_pct = ((self.equity_peak - equity) / self.equity_peak) * 100
            if drawdown_pct >= self.config.get("MAX_DRAWDOWN", 10.0):
                logger.warning(f"Max drawdown reached: {drawdown_pct:.2f}%")
                return False
                
            # Check maximum open positions
            positions = mt5.positions_get(symbol=self.symbol)
            if positions is None:
                current_positions = 0
            else:
                current_positions = len(positions)
                
            if current_positions >= self.config.get("MAX_OPEN_POSITIONS", 1):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return False
    
    def is_market_open(self) -> bool:
        """Check if market is open based on symbol and session filters"""
        now = datetime.utcnow()
        hour = now.hour
        
        # Check session open filters
        for session in self.config.get("SESSION_OPEN_FILTERS", []):
            start_time = now.replace(hour=session['start_h'], minute=session['start_m'], second=0, microsecond=0)
            time_diff = (now - start_time).total_seconds() / 60.0
            if 0 <= time_diff < session['skip_minutes']:
                logger.info(f"Within session open skip window ({session})")
                return False
        
        # Symbol-specific time filters
        trading_hours = self.config.get("TRADING_HOURS", {})
        start_hour = trading_hours.get("start_hour", 0)
        end_hour = trading_hours.get("end_hour", 24)
        
        if not (start_hour <= hour < end_hour):
            return False
            
        return True
    
    def check_spread(self) -> bool:
        """Check if spread is acceptable for trading"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                return False
                
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                return False
                
            spread_points = (tick.ask - tick.bid) / symbol_info.point
            max_spread = self.config.get("MAX_SPREAD_POINTS", 10)
            
            if spread_points > max_spread:
                logger.info(f"Spread too high: {spread_points:.1f} points (max: {max_spread})")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking spread: {e}")
            return False
    
    def fetch_data(self, timeframe: int = mt5.TIMEFRAME_M5, count: int = 200) -> pd.DataFrame:
        """Fetch market data with caching"""
        cache_key = f"{self.symbol}_{timeframe}_{count}"
        current_time = datetime.now()
        
        # Check cache first
        if cache_key in self.data_cache:
            cached_data, timestamp = self.data_cache[cache_key]
            if (current_time - timestamp).total_seconds() < self.cache_timeout:
                return cached_data
        
        # Fetch new data
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.warning(f"No data for {self.symbol}")
                return pd.DataFrame()
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Cache the data
            self.data_cache[cache_key] = (df, current_time)
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {self.symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        if df.empty:
            return df
            
        df = df.copy()
        
        # EMA
        df['EMA_fast'] = df['close'].ewm(span=self.config['EMA_FAST'], adjust=False).mean()
        df['EMA_slow'] = df['close'].ewm(span=self.config['EMA_SLOW'], adjust=False).mean()
        
        # RSI
        df['RSI'] = self.calculate_rsi(df['close'], self.config['RSI_PERIOD'])
        
        # MACD
        macd_line, signal_line, hist = self.calculate_macd(
            df['close'], self.config['MACD_FAST'], self.config['MACD_SLOW'], self.config['MACD_SIGNAL']
        )
        df['MACD_HIST'] = hist
        
        # ATR
        df['ATR'] = self.calculate_atr(df, self.config['ATR_PERIOD'])
        
        return df
    
    def calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator"""
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
    
    def calculate_macd(self, series: pd.Series, fast: int, slow: int, signal: int) -> tuple:
        """Calculate MACD indicator"""
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
    
    def calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate ATR indicator"""
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
    
    def get_fibonacci_levels(self, lookback_weeks: int = 52) -> Tuple[Dict[float, float], str]:
        """Calculate weekly Fibonacci levels"""
        try:
            # Fetch weekly data
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_W1, 0, lookback_weeks)
            if rates is None or len(rates) == 0:
                return {}, "neutral"
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            highest = df['high'].max()
            lowest = df['low'].min()
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
            bias = "bull" if df['close'].iloc[-1] > df['close'].rolling(window=4).mean().iloc[-1] else "bear"
            return levels, bias
            
        except Exception as e:
            logger.error(f"Error calculating Fibonacci levels: {e}")
            return {}, "neutral"
    
    def get_daily_levels(self, lookback_days: int = 60) -> Dict[str, List[float]]:
        """Identify daily support and resistance levels"""
        try:
            # Fetch daily data
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_D1, 0, lookback_days + 1)
            if rates is None or len(rates) == 0:
                return {'res': [], 'sup': []}
                
            df = pd.DataFrame(rates)
            
            # Find significant highs and lows
            highs = df['high'].nlargest(5).tolist()
            lows = df['low'].nsmallest(5).tolist()
            return {'res': sorted(highs, reverse=True), 'sup': sorted(lows)}
            
        except Exception as e:
            logger.error(f"Error calculating daily levels: {e}")
            return {'res': [], 'sup': []}
    
    def has_open_position(self) -> bool:
        """Check if we have an open position for this symbol"""
        return self.symbol in self.open_positions
    
    def check_exit_conditions(self, df: pd.DataFrame):
        """Check exit conditions for open positions"""
        if not self.has_open_position():
            return
            
        position = self.open_positions[self.symbol]
        
        # Get the current price as a scalar value (not Series)
        current_price = self.get_current_price()
        if current_price is None:
            return
            
        current_time = datetime.now()
        
        # Check standard SL/TP first
        exit_reason = self.check_sl_tp(position, current_price)
        
        # Check advanced exit strategies
        if not exit_reason:
            exit_reason = self.check_advanced_exits(df, position, current_time)
        
        if exit_reason:
            self.exit_position(current_price, exit_reason)
    
    def get_current_price(self) -> Optional[float]:
        """Get current price as a scalar value"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                return tick.last  # Use last price instead of close from DataFrame
            return None
        except Exception:
            return None
    
    def check_sl_tp(self, position: Dict, current_price: float) -> Optional[str]:
        """Check if SL or TP has been hit - FIXED Series comparison"""
        if current_price is None:
            return None
            
        if position['direction'] == 'buy':
            if current_price <= position['sl_price']:
                return 'sl'
            elif current_price >= position['tp_price']:
                return 'tp'
        else:  # sell
            if current_price >= position['sl_price']:
                return 'sl'
            elif current_price <= position['tp_price']:
                return 'tp'
        return None
    
    def check_advanced_exits(self, df: pd.DataFrame, position: Dict, current_time: datetime) -> Optional[str]:
        """Check advanced exit conditions"""
        current_price = self.get_current_price()
        if current_price is None:
            return None
            
        # Trailing stop
        if 'ATR' in df and not df['ATR'].isnull().all():
            atr_val = df['ATR'].iloc[-1]  # Get scalar value
            new_sl = self.exit_strategies.trailing_stop_atr(current_price, position, atr_val)
            
            if ((position['direction'] == 'buy' and new_sl > position['sl_price']) or
                (position['direction'] == 'sell' and new_sl < position['sl_price'])):
                position['sl_price'] = new_sl
                logger.debug(f"Updated trailing SL to {new_sl:.3f}")
        
        # Time-based exit
        if self.exit_strategies.time_based_exit(position, current_time, self.config.get("MAX_TRADE_HOURS", 48)):
            return 'time'
            
        # Volatility expansion exit
        if self.exit_strategies.volatility_expansion_exit(df, position):
            return 'volatility'
            
        # RSI extreme exit
        if 'RSI' in df and self.exit_strategies.rsi_extreme_exit(df, position):
            return 'rsi_extreme'
            
        return None
    
    def exit_position(self, exit_price: float, exit_reason: str):
        """Exit the current position"""
        if not self.has_open_position():
            return
            
        position = self.open_positions[self.symbol]
        
        # Close position via MT5
        order_type = mt5.ORDER_TYPE_SELL if position['direction'] == 'buy' else mt5.ORDER_TYPE_BUY
        result = mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": position['lots'],
            "type": order_type,
            "price": exit_price,
            "deviation": self.config.get("DEVIATION", 50),
            "magic": self.config.get("MAGIC_NUMBER", 20250917),
            "comment": f"Exit: {exit_reason}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        })
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            # Calculate PnL
            if position['direction'] == 'buy':
                pnl = (exit_price - position['entry_price']) * position['lots'] * 100
            else:
                pnl = (position['entry_price'] - exit_price) * position['lots'] * 100
            
            # Record trade
            trade_info = {
                'entry_time': position['entry_time'],
                'exit_time': datetime.now(),
                'direction': position['direction'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'lots': position['lots'],
                'pnl': pnl,
                'exit_reason': exit_reason,
                'symbol': self.symbol
            }
            
            self.performance_tracker.add_trade(trade_info)
            del self.open_positions[self.symbol]
            
            logger.info(f"Exited position: {exit_reason.upper()}, PnL: ${pnl:.2f}")
    
    def execute_if_qualified(self, df: pd.DataFrame, confirmations: Dict, 
                           fib_levels: Dict, weekly_bias: str):
        """Execute trade if all conditions are met"""
        min_confirmations = self.config['MIN_CONFIRMATIONS']
        
        if (confirmations['buy'] >= min_confirmations and 
            confirmations['buy'] > confirmations['sell']):
            self.execute_trade('buy', df, fib_levels)
        elif (confirmations['sell'] >= min_confirmations and 
              confirmations['sell'] > confirmations['buy']):
            self.execute_trade('sell', df, fib_levels)
    
    def execute_trade(self, direction: str, df: pd.DataFrame, fib_levels: Dict):
        """Execute a trade with enhanced risk management"""
        current_price = self.get_current_price()
        if current_price is None:
            return
            
        # Adjust parameters based on news impact
        adjusted_config = self.config
        if self.news_filter:
            adjusted_config = self.news_filter.adjust_risk_parameters(self.symbol, self.config, self.trading_style)
        
        # Calculate SL/TP
        atr_val = df['ATR'].iloc[-1] if not df['ATR'].isnull().all() else 0.1 * current_price
        sl_price, tp_price = self.strategy.calculate_sl_tp(current_price, atr_val, direction)
        
        # Calculate position size with adjusted risk
        lots = self.calculate_position_size(sl_price, direction, adjusted_config['RISK_PERCENT'])
        
        if lots <= 0:
            return
            
        # Execute order
        result = self.send_order(direction, lots, sl_price, tp_price)
        
        if result and hasattr(result, 'retcode') and result.retcode == mt5.TRADE_RETCODE_DONE:
            # Record position
            self.open_positions[self.symbol] = {
                'ticket': result.order,
                'direction': direction,
                'entry_price': result.price,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'lots': lots,
                'entry_time': datetime.now()
            }
            
            logger.info(f"Executed {direction} {lots} lots at {result.price:.3f}")
    
    def calculate_position_size(self, stop_loss_price: float, side: str, risk_percent: float) -> float:
        """Calculate position size with proper risk management"""
        try:
            account = mt5.account_info()
            if not account:
                return self.config['MIN_LOT']
                
            equity = account.equity
            risk_amount = equity * (risk_percent / 100.0)
            
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                return self.config['MIN_LOT']
                
            price = tick.ask if side == 'buy' else tick.bid
            distance = abs(price - stop_loss_price)
            
            if distance <= 0:
                return self.config['MIN_LOT']
                
            # Different calculation for different instrument types
            if 'XAU' in self.symbol or 'XAG' in self.symbol:
                # Metals: 1 lot = 100 oz, 0.01 movement = $1
                risk_per_lot = (distance / 0.01) * 1.0
            elif 'USOIL' in self.symbol:
                # Oil: different calculation
                contract_size = mt5.symbol_info(self.symbol).trade_contract_size
                risk_per_lot = distance * contract_size
            else:
                # Indices and others
                contract_size = mt5.symbol_info(self.symbol).trade_contract_size
                risk_per_lot = distance * contract_size
                
            if risk_per_lot <= 0:
                return self.config['MIN_LOT']
                
            # Adjust for commission
            estimated_lots = risk_amount / risk_per_lot
            commission = self.config["COMMISSION_PER_LOT"] * estimated_lots
            risk_amount = max(0, risk_amount - commission)
            
            lots = risk_amount / risk_per_lot
            lots = round(lots, 2)
            lots = max(self.config['MIN_LOT'], min(self.config['MAX_LOT'], lots))
            
            return lots
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return self.config['MIN_LOT']
    
    def send_order(self, side: str, lots: float, sl: float, tp: float, 
                  comment: str = "GoldBot Signal") -> Optional[Any]:
        """Send order with enhanced error handling"""
        try:
            # Check symbol info
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                logger.error(f"Symbol {self.symbol} not found")
                return None
                
            if not symbol_info.visible:
                mt5.symbol_select(self.symbol, True)
            
            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": lots,
                "type": mt5.ORDER_TYPE_BUY if side == 'buy' else mt5.ORDER_TYPE_SELL,
                "price": mt5.symbol_info_tick(self.symbol).ask if side == 'buy' else mt5.symbol_info_tick(self.symbol).bid,
                "sl": sl,
                "tp": tp,
                "deviation": self.config.get("DEVIATION", 50),
                "magic": self.config.get("MAGIC_NUMBER", 20250917),
                "comment": f"{comment} | Commission: ${self.config['COMMISSION_PER_LOT'] * lots:.2f}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.retcode} - {result.comment}")
                return None
                
            logger.info(f"Order executed: {side.upper()} {lots} lots, SL: {sl:.3f}, TP: {tp:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending order: {e}")
            return None
    
    def get_performance_report(self) -> str:
        """Get performance report"""
        return self.performance_tracker.generate_report()
    
    def plot_equity_curve(self, save_path: Optional[str] = None):
        """Plot equity curve"""
        self.performance_tracker.plot_equity_curve(save_path)