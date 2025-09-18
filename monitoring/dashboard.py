"""
Dashboard for monitoring both scalping and position trading bots
"""

import time
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt

class TradingDashboard:
    def __init__(self):
        self.scalping_bots = []
        self.position_bots = []
        self.bot_status = {}
        self.history = []
        self.start_time = datetime.now()
    
    def add_bot(self, bot):
        """Add a bot to the dashboard"""
        if bot.trading_style == 'scalping':
            self.scalping_bots.append(bot)
        else:
            self.position_bots.append(bot)
        
        self.bot_status[bot.symbol] = {
            'style': bot.trading_style,
            'status': 'initialized',
            'trades': 0,
            'pnl': 0,
            'last_update': datetime.now()
        }
    
    def update_bot_status(self, bot):
        """Update status for a specific bot"""
        if bot.symbol not in self.bot_status:
            return
            
        # Get current performance data
        try:
            current_pnl = bot.performance_tracker.current_balance - bot.performance_tracker.initial_balance
            trade_count = len(bot.performance_tracker.trades)
            
            self.bot_status[bot.symbol].update({
                'status': 'active',
                'trades': trade_count,
                'pnl': current_pnl,
                'last_update': datetime.now(),
                'has_position': bot.has_open_position()
            })
            
            # Record history
            self.history.append({
                'timestamp': datetime.now(),
                'symbol': bot.symbol,
                'style': bot.trading_style,
                'trades': trade_count,
                'pnl': current_pnl
            })
            
        except Exception as e:
            self.bot_status[bot.symbol]['status'] = f'error: {str(e)}'
    
    def display_status(self):
        """Display current status of all bots"""
        print("\n" + "="*80)
        print(f"TRADING DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Scalping bots section
        if self.scalping_bots:
            print("\n🔴 SCALPING BOTS (Fast):")
            print("-" * 40)
            for bot in self.scalping_bots:
                status = self.bot_status.get(bot.symbol, {})
                position_indicator = "📈" if status.get('has_position') else "📉"
                print(f"{position_indicator} {bot.symbol}: {status.get('trades', 0)} trades | "
                      f"PnL: ${status.get('pnl', 0):.2f} | {status.get('status', 'unknown')}")
        
        # Position bots section
        if self.position_bots:
            print("\n🔵 POSITION BOTS (Slow):")
            print("-" * 40)
            for bot in self.position_bots:
                status = self.bot_status.get(bot.symbol, {})
                position_indicator = "📈" if status.get('has_position') else "📉"
                print(f"{position_indicator} {bot.symbol}: {status.get('trades', 0)} trades | "
                      f"PnL: ${status.get('pnl', 0):.2f} | {status.get('status', 'unknown')}")
        
        # Summary statistics
        total_trades = sum(status.get('trades', 0) for status in self.bot_status.values())
        total_pnl = sum(status.get('pnl', 0) for status in self.bot_status.values())
        
        print(f"\n📊 SUMMARY: {total_trades} trades | Total PnL: ${total_pnl:.2f}")
        print("="*80)
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        if not self.history:
            return "No trading data available"
        
        # Create DataFrame from history
        df = pd.DataFrame(self.history)
        
        # Calculate statistics
        summary = {
            'total_runtime': str(datetime.now() - self.start_time),
            'total_bots': len(self.scalping_bots) + len(self.position_bots),
            'scalping_bots': len(self.scalping_bots),
            'position_bots': len(self.position_bots),
            'total_trades': df['trades'].sum(),
            'total_pnl': df['pnl'].sum(),
        }
        
        # Style-specific statistics
        if not df.empty:
            scalping_data = df[df['style'] == 'scalping']
            position_data = df[df['style'] == 'position']
            
            if not scalping_data.empty:
                summary['scalping_trades'] = scalping_data['trades'].sum()
                summary['scalping_pnl'] = scalping_data['pnl'].sum()
                summary['scalping_avg_trade'] = scalping_data['pnl'].mean() if not scalping_data.empty else 0
            
            if not position_data.empty:
                summary['position_trades'] = position_data['trades'].sum()
                summary['position_pnl'] = position_data['pnl'].sum()
                summary['position_avg_trade'] = position_data['pnl'].mean() if not position_data.empty else 0
        
        # Generate report string
        report = ["="*60, "FINAL TRADING SUMMARY", "="*60]
        report.append(f"Runtime: {summary['total_runtime']}")
        report.append(f"Total Bots: {summary['total_bots']} ({summary['scalping_bots']} scalping, {summary['position_bots']} position)")
        report.append(f"Total Trades: {summary['total_trades']}")
        report.append(f"Total PnL: ${summary['total_pnl']:.2f}")
        
        if 'scalping_trades' in summary:
            report.append(f"\nScalping: {summary['scalping_trades']} trades | PnL: ${summary['scalping_pnl']:.2f} | Avg: ${summary['scalping_avg_trade']:.2f}")
        
        if 'position_trades' in summary:
            report.append(f"Position: {summary['position_trades']} trades | PnL: ${summary['position_pnl']:.2f} | Avg: ${summary['position_avg_trade']:.2f}")
        
        report.append("="*60)
        
        return "\n".join(report)
    
    def plot_performance_comparison(self, save_path: str = None):
        """Plot performance comparison between scalping and position trading"""
        if not self.history:
            return
            
        df = pd.DataFrame(self.history)
        
        # Group by style and time
        df['time_minutes'] = (df['timestamp'] - self.start_time).dt.total_seconds() / 60
        
        plt.figure(figsize=(12, 8))
        
        # Plot scalping performance
        scalping_data = df[df['style'] == 'scalping']
        if not scalping_data.empty:
            scalping_pnl = scalping_data.groupby('time_minutes')['pnl'].last()
            plt.plot(scalping_pnl.index, scalping_pnl.values, 'r-', label='Scalping', linewidth=2)
        
        # Plot position performance
        position_data = df[df['style'] == 'position']
        if not position_data.empty:
            position_pnl = position_data.groupby('time_minutes')['pnl'].last()
            plt.plot(position_pnl.index, position_pnl.values, 'b-', label='Position', linewidth=2)
        
        plt.title('Performance Comparison: Scalping vs Position Trading')
        plt.xlabel('Time (minutes)')
        plt.ylabel('PnL ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()