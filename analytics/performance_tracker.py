"""
Comprehensive performance tracking and analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional
import json

class PerformanceTracker:
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.trades = []
        self.equity_curve = [{'timestamp': datetime.now(), 'equity': initial_balance}]
        self.performance_stats = {}
        
    def add_trade(self, trade_info: Dict[str, Any]):
        """Add a completed trade to the tracker"""
        self.trades.append(trade_info)
        self.current_balance += trade_info['pnl']
        
        self.equity_curve.append({
            'timestamp': trade_info['exit_time'],
            'equity': self.current_balance
        })
    
    def calculate_stats(self) -> Dict[str, Any]:
        """Calculate comprehensive performance statistics"""
        if not self.trades:
            return {}
            
        # Basic trade statistics
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        total_pnl = sum(t['pnl'] for t in self.trades)
        total_commission = sum(t.get('commission', 0) for t in self.trades)
        
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        # Profit/loss metrics
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 0
        profit_factor = abs(avg_win * len(winning_trades) / (avg_loss * len(losing_trades))) if losing_trades else float('inf')
        
        # Risk-adjusted metrics
        sharpe_ratio = self.calculate_sharpe_ratio()
        sortino_ratio = self.calculate_sortino_ratio()
        calmar_ratio = self.calculate_calmar_ratio()
        
        # Drawdown analysis
        drawdown_stats = self.calculate_drawdown_stats()
        
        # Trade duration analysis
        durations = self.calculate_trade_durations()
        
        # Monthly performance
        monthly_stats = self.calculate_monthly_performance()
        
        self.performance_stats = {
            'summary': {
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'total_pnl': total_pnl,
                'total_commission': total_commission,
                'net_profit': total_pnl - total_commission,
                'return_pct': (self.current_balance - self.initial_balance) / self.initial_balance * 100
            },
            'trade_stats': {
                'total_trades': len(self.trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate * 100,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'largest_win': max([t['pnl'] for t in winning_trades]) if winning_trades else 0,
                'largest_loss': min([t['pnl'] for t in losing_trades]) if losing_trades else 0,
                'profit_factor': profit_factor,
                'expectancy': (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            },
            'risk_metrics': {
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'max_drawdown': drawdown_stats['max_drawdown'],
                'max_drawdown_pct': drawdown_stats['max_drawdown_pct'],
                'avg_drawdown': drawdown_stats['avg_drawdown'],
                'drawdown_duration': drawdown_stats['max_drawdown_duration']
            },
            'time_metrics': {
                'avg_trade_duration': durations['avg_duration'],
                'max_trade_duration': durations['max_duration'],
                'min_trade_duration': durations['min_duration'],
                'profit_per_day': total_pnl / max(1, (self.equity_curve[-1]['timestamp'] - self.equity_curve[0]['timestamp']).days)
            },
            'monthly_performance': monthly_stats
        }
        
        return self.performance_stats
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio (annualized)"""
        if len(self.equity_curve) < 2:
            return 0
            
        # Calculate daily returns
        equities = [x['equity'] for x in self.equity_curve]
        daily_returns = np.diff(equities) / equities[:-1]
        
        if len(daily_returns) == 0 or np.std(daily_returns) == 0:
            return 0
            
        # Annualize
        sharpe = (np.mean(daily_returns) - risk_free_rate/252) / np.std(daily_returns) * np.sqrt(252)
        return sharpe
    
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (annualized)"""
        if len(self.equity_curve) < 2:
            return 0
            
        equities = [x['equity'] for x in self.equity_curve]
        daily_returns = np.diff(equities) / equities[:-1]
        
        # Only consider negative returns for downside deviation
        negative_returns = daily_returns[daily_returns < 0]
        
        if len(negative_returns) == 0 or np.std(negative_returns) == 0:
            return 0
            
        sortino = (np.mean(daily_returns) - risk_free_rate/252) / np.std(negative_returns) * np.sqrt(252)
        return sortino
    
    def calculate_calmar_ratio(self) -> float:
        """Calculate Calmar ratio (return vs max drawdown)"""
        if len(self.equity_curve) < 2:
            return 0
            
        drawdown_stats = self.calculate_drawdown_stats()
        total_return = (self.current_balance - self.initial_balance) / self.initial_balance
        
        if drawdown_stats['max_drawdown_pct'] == 0:
            return float('inf')
            
        # Annualize return
        days = (self.equity_curve[-1]['timestamp'] - self.equity_curve[0]['timestamp']).days
        annual_return = total_return * (365 / max(1, days))
        
        return annual_return / (drawdown_stats['max_drawdown_pct'] / 100)
    
    def calculate_drawdown_stats(self) -> Dict[str, float]:
        """Calculate comprehensive drawdown statistics"""
        equities = [x['equity'] for x in self.equity_curve]
        peaks = np.maximum.accumulate(equities)
        drawdowns = (peaks - equities) / peaks * 100
        
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        avg_drawdown = np.mean(drawdowns) if len(drawdowns) > 0 else 0
        
        # Calculate max drawdown duration
        drawdown_duration = self.calculate_max_drawdown_duration()
        
        return {
            'max_drawdown': np.max(peaks - equities) if len(equities) > 0 else 0,
            'max_drawdown_pct': max_drawdown,
            'avg_drawdown': avg_drawdown,
            'max_drawdown_duration': drawdown_duration
        }
    
    def calculate_max_drawdown_duration(self) -> timedelta:
        """Calculate duration of maximum drawdown"""
        if len(self.equity_curve) < 2:
            return timedelta(0)
            
        equities = [x['equity'] for x in self.equity_curve]
        peaks = np.maximum.accumulate(equities)
        drawdowns = peaks - equities
        
        max_drawdown_idx = np.argmax(drawdowns)
        max_drawdown_value = drawdowns[max_drawdown_idx]
        
        # Find start of drawdown
        start_idx = max_drawdown_idx
        while start_idx > 0 and drawdowns[start_idx] > 0:
            start_idx -= 1
        
        # Find recovery point
        recovery_idx = max_drawdown_idx
        while recovery_idx < len(equities) - 1 and equities[recovery_idx] < peaks[max_drawdown_idx]:
            recovery_idx += 1
        
        start_time = self.equity_curve[start_idx]['timestamp']
        end_time = self.equity_curve[recovery_idx]['timestamp'] if recovery_idx < len(self.equity_curve) else self.equity_curve[-1]['timestamp']
        
        return end_time - start_time
    
    def calculate_trade_durations(self) -> Dict[str, timedelta]:
        """Calculate trade duration statistics"""
        if not self.trades:
            return {'avg_duration': timedelta(0), 'max_duration': timedelta(0), 'min_duration': timedelta(0)}
        
        durations = []
        for trade in self.trades:
            duration = trade['exit_time'] - trade['entry_time']
            durations.append(duration)
        
        return {
            'avg_duration': sum(durations, timedelta(0)) / len(durations),
            'max_duration': max(durations) if durations else timedelta(0),
            'min_duration': min(durations) if durations else timedelta(0)
        }
    
    def calculate_monthly_performance(self) -> Dict[str, Dict[str, float]]:
        """Calculate monthly performance statistics"""
        monthly_stats = {}
        
        for trade in self.trades:
            month_key = trade['exit_time'].strftime('%Y-%m')
            
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'pnl': 0,
                    'trades': 0,
                    'winning_trades': 0,
                    'commission': 0
                }
            
            monthly_stats[month_key]['pnl'] += trade['pnl']
            monthly_stats[month_key]['trades'] += 1
            monthly_stats[month_key]['commission'] += trade.get('commission', 0)
            
            if trade['pnl'] > 0:
                monthly_stats[month_key]['winning_trades'] += 1
        
        # Calculate monthly percentages
        for month in monthly_stats:
            stats = monthly_stats[month]
            if stats['trades'] > 0:
                stats['win_rate'] = (stats['winning_trades'] / stats['trades']) * 100
                stats['net_pnl'] = stats['pnl'] - stats['commission']
            else:
                stats['win_rate'] = 0
                stats['net_pnl'] = 0
        
        return monthly_stats
    
    def generate_report(self, format: str = 'text') -> str:
        """Generate performance report in specified format"""
        stats = self.calculate_stats()
        
        if format == 'json':
            return json.dumps(stats, indent=2, default=str)
        else:
            # Text format
            report = []
            report.append("=" * 60)
            report.append("PERFORMANCE REPORT")
            report.append("=" * 60)
            
            # Summary section
            report.append("\nSUMMARY:")
            report.append(f"Initial Balance: ${stats['summary']['initial_balance']:,.2f}")
            report.append(f"Final Balance: ${stats['summary']['final_balance']:,.2f}")
            report.append(f"Net Profit: ${stats['summary']['net_profit']:,.2f}")
            report.append(f"Return: {stats['summary']['return_pct']:.2f}%")
            
            # Trade statistics
            report.append("\nTRADE STATISTICS:")
            report.append(f"Total Trades: {stats['trade_stats']['total_trades']}")
            report.append(f"Win Rate: {stats['trade_stats']['win_rate']:.2f}%")
            report.append(f"Profit Factor: {stats['trade_stats']['profit_factor']:.2f}")
            report.append(f"Expectancy: ${stats['trade_stats']['expectancy']:.2f}")
            
            # Risk metrics
            report.append("\nRISK METRICS:")
            report.append(f"Sharpe Ratio: {stats['risk_metrics']['sharpe_ratio']:.2f}")
            report.append(f"Sortino Ratio: {stats['risk_metrics']['sortino_ratio']:.2f}")
            report.append(f"Max Drawdown: {stats['risk_metrics']['max_drawdown_pct']:.2f}%")
            
            return "\n".join(report)
    
    def plot_equity_curve(self, save_path: Optional[str] = None):
        """Plot equity curve"""
        if len(self.equity_curve) < 2:
            return
            
        times = [x['timestamp'] for x in self.equity_curve]
        equities = [x['equity'] for x in self.equity_curve]
        
        plt.figure(figsize=(12, 6))
        plt.plot(times, equities, linewidth=2)
        plt.title('Equity Curve')
        plt.xlabel('Time')
        plt.ylabel('Equity ($)')
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()