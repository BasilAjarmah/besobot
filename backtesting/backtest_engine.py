"""
Advanced backtesting engine with realistic fill simulation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("BacktestEngine")

class BacktestEngine:
    def __init__(self, strategy, config, initial_balance=10000):
        self.strategy = strategy
        self.config = config
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.trades = []
        self.equity_curve = []
        self.position = None
        
    def run_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run complete backtest on historical data"""
        logger.info(f"Starting backtest for {self.config['SYMBOL']}")
        
        self.current_balance = self.initial_balance
        self.equity_curve = [{'timestamp': data.index[0], 'equity': self.initial_balance}]
        self.trades = []
        self.position = None
        
        # Pre-calculate indicators
        data = self.calculate_indicators(data)
        
        # Main backtest loop
        for i in range(100, len(data)):
            current_bar = data.iloc[i]
            previous_bars = data.iloc[:i+1]  # All data up to current bar
            
            # Check exit conditions first
            if self.position:
                exit_signal = self.check_exit_conditions(current_bar, previous_bars, i)
                if exit_signal:
                    self.exit_trade(current_bar, i, exit_signal)
            
            # Check entry conditions (if no position)
            if not self.position:
                self.check_entry_conditions(current_bar, previous_bars, i)
            
            # Update equity curve
            self.update_equity_curve(current_bar, i)
        
        # Generate performance report
        report = self.generate_report()
        logger.info(f"Backtest completed. Total trades: {len(self.trades)}")
        return report
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for backtest data"""
        df = data.copy()
        
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
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.rolling(window=period, min_periods=1).mean()
        ma_down = down.rolling(window=period, min_periods=1).mean()
        rs = ma_up / (ma_down + 1e-12)
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self, series: pd.Series, fast: int, slow: int, signal: int) -> tuple:
        """Calculate MACD indicator"""
        fast_ema = series.ewm(span=fast, adjust=False).mean()
        slow_ema = series.ewm(span=slow, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line
        return macd_line, signal_line, hist
    
    def calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate ATR indicator"""
        high = df['high']
        low = df['low']
        close = df['close']
        prev_close = close.shift(1)
        tr = pd.concat([high - low, (high - prev_close).abs(), 
                       (low - prev_close).abs()], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def check_entry_conditions(self, current_bar: pd.Series, previous_bars: pd.DataFrame, index: int):
        """Check if entry conditions are met"""
        # Get market context
        fib_levels, weekly_bias = self.get_fibonacci_levels(previous_bars)
        daily_levels = self.get_daily_levels(previous_bars)
        
        # Calculate confirmations using strategy
        confirmations = self.strategy.calculate_confirmations(
            previous_bars, fib_levels, daily_levels, weekly_bias
        )
        
        # Check if we should enter
        min_confirmations = self.config['MIN_CONFIRMATIONS']
        
        if confirmations['buy'] >= min_confirmations and confirmations['buy'] > confirmations['sell']:
            self.enter_trade('buy', current_bar, index, previous_bars)
        elif confirmations['sell'] >= min_confirmations and confirmations['sell'] > confirmations['buy']:
            self.enter_trade('sell', current_bar, index, previous_bars)
    
    def enter_trade(self, direction: str, current_bar: pd.Series, index: int, previous_bars: pd.DataFrame):
        """Enter a trade with realistic fill simulation"""
        # Calculate SL/TP
        atr_val = current_bar['ATR'] if not pd.isna(current_bar['ATR']) else 0.1 * current_bar['close']
        sl_price, tp_price = self.strategy.calculate_sl_tp(current_bar['close'], atr_val, direction)
        
        # Simulate fill price (include spread and slippage)
        spread = self.config.get('SPREAD_SIMULATION', 0.0002)  # 2 pips for gold
        slippage = np.random.normal(0, spread / 2)  # Random slippage
        
        if direction == 'buy':
            fill_price = current_bar['close'] + spread / 2 + slippage
        else:
            fill_price = current_bar['close'] - spread / 2 + slippage
        
        # Calculate position size
        risk_amount = self.current_balance * (self.config['RISK_PERCENT'] / 100)
        distance = abs(fill_price - sl_price)
        
        # Different risk calculation per instrument type
        if 'XAU' in self.config['SYMBOL'] or 'XAG' in self.config['SYMBOL']:
            risk_per_lot = (distance / 0.01) * 1.0  # $1 per 0.01 movement
        else:
            # For other instruments, use point value
            point_value = 1.0  # Simplified
            risk_per_lot = distance * point_value
        
        if risk_per_lot <= 0:
            return
            
        lots = risk_amount / risk_per_lot
        lots = round(lots, 2)
        lots = max(self.config['MIN_LOT'], min(self.config['MAX_LOT'], lots))
        
        # Calculate commission
        commission = self.config['COMMISSION_PER_LOT'] * lots
        
        # Create position
        self.position = {
            'entry_time': current_bar.name,
            'direction': direction,
            'entry_price': fill_price,
            'sl_price': sl_price,
            'tp_price': tp_price,
            'lots': lots,
            'commission': commission,
            'entry_index': index
        }
        
        logger.debug(f"Entered {direction} trade at {fill_price:.3f}, SL: {sl_price:.3f}, TP: {tp_price:.3f}")
    
    def check_exit_conditions(self, current_bar: pd.Series, previous_bars: pd.DataFrame, index: int) -> Optional[str]:
        """Check if exit conditions are met"""
        if not self.position:
            return None
            
        direction = self.position['direction']
        entry_price = self.position['entry_price']
        current_price = current_bar['close']
        
        # Check SL/TP
        if direction == 'buy':
            if current_price <= self.position['sl_price']:
                return 'sl'
            elif current_price >= self.position['tp_price']:
                return 'tp'
        else:  # sell
            if current_price >= self.position['sl_price']:
                return 'sl'
            elif current_price <= self.position['tp_price']:
                return 'tp'
        
        # Check time-based exit
        hours_in_trade = (current_bar.name - self.position['entry_time']).total_seconds() / 3600
        if hours_in_trade >= self.config.get('MAX_TRADE_HOURS', 72):
            return 'time'
        
        return None
    
    def exit_trade(self, current_bar: pd.Series, index: int, exit_reason: str):
        """Exit the current trade"""
        direction = self.position['direction']
        entry_price = self.position['entry_price']
        exit_price = current_bar['close']
        
        # Calculate PnL
        if direction == 'buy':
            pnl = (exit_price - entry_price) * self.position['lots'] * 100  # For gold
        else:
            pnl = (entry_price - exit_price) * self.position['lots'] * 100
        
        # Subtract commission
        pnl -= self.position['commission']
        
        # Update balance
        self.current_balance += pnl
        
        # Record trade
        trade_info = {
            'entry_time': self.position['entry_time'],
            'exit_time': current_bar.name,
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'lots': self.position['lots'],
            'pnl': pnl,
            'commission': self.position['commission'],
            'exit_reason': exit_reason,
            'symbol': self.config['SYMBOL']
        }
        
        self.trades.append(trade_info)
        self.position = None
        
        logger.debug(f"Exited trade: {exit_reason.upper()}, PnL: ${pnl:.2f}")
    
    def update_equity_curve(self, current_bar: pd.Series, index: int):
        """Update equity curve with current balance"""
        self.equity_curve.append({
            'timestamp': current_bar.name,
            'equity': self.current_balance
        })
    
    def get_fibonacci_levels(self, df: pd.DataFrame) -> tuple:
        """Calculate Fibonacci levels from weekly data"""
        # Resample to weekly for Fibonacci calculation
        weekly_df = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        })
        
        if len(weekly_df) < 10:
            return {}, "neutral"
            
        highest = weekly_df['high'].max()
        lowest = weekly_df['low'].min()
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
        bias = "bull" if weekly_df['close'].iloc[-1] > weekly_df['close'].rolling(window=4).mean().iloc[-1] else "bear"
        
        return levels, bias
    
    def get_daily_levels(self, df: pd.DataFrame) -> Dict[str, list]:
        """Identify daily support and resistance levels"""
        # Resample to daily
        daily_df = df.resample('D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last'
        })
        
        if len(daily_df) < 20:
            return {'res': [], 'sup': []}
            
        # Find significant highs and lows
        highs = daily_df['high'].nlargest(5).tolist()
        lows = daily_df['low'].nsmallest(5).tolist()
        
        return {'res': sorted(highs, reverse=True), 'sup': sorted(lows)}
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive backtest report"""
        if not self.trades:
            return {'error': 'No trades executed'}
        
        # Calculate performance metrics
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        total_pnl = sum(t['pnl'] for t in self.trades)
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if losing_trades else float('inf')
        
        # Drawdown calculation
        equity_values = [x['equity'] for x in self.equity_curve]
        drawdown = self.calculate_drawdown(equity_values)
        
        return {
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance,
            'total_pnl': total_pnl,
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': drawdown['max_drawdown'],
            'max_drawdown_pct': drawdown['max_drawdown_pct'],
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def calculate_drawdown(self, equity_curve: List[float]) -> Dict[str, float]:
        """Calculate maximum drawdown from equity curve"""
        peak = equity_curve[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak) * 100
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct
        }