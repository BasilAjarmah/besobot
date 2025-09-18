"""
Main entry point for multi-instrument trading bot with dual mode support
"""

import logging
import time
import argparse
from datetime import datetime
import pandas as pd
import numpy as np

# Import configurations
from config.xauusd_config import XAUUSD_CONFIG
from config.xagusd_config import XAGUSD_CONFIG
from config.usoil_config import USOIL_CONFIG
from config.ustec_config import USTEC_CONFIG
from config.us30_config import US30_CONFIG
from config.scalping_config import XAUUSD_SCALPING, USOIL_SCALPING, EURUSD_SCALPING

# Import strategies
from strategies.gold_strategy import GoldStrategy
from strategies.oil_strategy import OilStrategy
from strategies.indices_strategy import IndicesStrategy
from strategies.scalping_strategy import ScalpingStrategy

# Import core components
from core.bot_core import MultiInstrumentBot
from backtesting.backtest_engine import BacktestEngine
from services.economic_calendar import EconomicCalendar
from services.news_filter import NewsFilter
from analytics.performance_tracker import PerformanceTracker
from monitoring.dashboard import TradingDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('multi_instrument_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Main")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Multi-Instrument Trading Bot')
    parser.add_argument('--mode', choices=['live', 'backtest', 'scalping', 'position', 'both'], 
                       default='both', help='Trading mode: live trading, backtesting, or specific style')
    parser.add_argument('--symbols', nargs='+', 
                       default=['XAUUSD', 'XAGUSD', 'USOIL', 'USTEC', 'US30', 'EURUSD'],
                       help='Symbols to trade')
    parser.add_argument('--data-file', help='CSV file with historical data for backtesting')
    parser.add_argument('--days', type=int, default=365, help='Days of historical data for backtest')
    parser.add_argument('--initial-balance', type=float, default=10000, help='Initial balance for backtest')
    parser.add_argument('--max-scalping-bots', type=int, default=3, help='Maximum scalping bots to run')
    parser.add_argument('--max-position-bots', type=int, default=2, help='Maximum position bots to run')
    return parser.parse_args()

def main():
    """Main function to run the trading bot"""
    args = parse_arguments()
    
    # Initialize economic calendar (shared across all bots)
    economic_calendar = EconomicCalendar()
    news_filter = NewsFilter(economic_calendar)
    
    # Initialize dashboard for monitoring
    dashboard = TradingDashboard()
    
    if args.mode in ['live', 'scalping', 'position', 'both']:
        run_live_mode(args, news_filter, dashboard)
    elif args.mode == 'backtest':
        run_backtest_mode(args)
    else:
        logger.error(f"Unknown mode: {args.mode}")

def run_live_mode(args, news_filter, dashboard):
    """Run bot in live trading mode with dual style support"""
    logger.info(f"Starting live trading mode: {args.mode}")
    
    # Define all available instrument profiles
    instrument_profiles = {
        # Position trading instruments
        'XAUUSD_POSITION': {'config': XAUUSD_CONFIG, 'strategy': GoldStrategy, 'style': 'position'},
        'XAGUSD_POSITION': {'config': XAGUSD_CONFIG, 'strategy': GoldStrategy, 'style': 'position'},
        'USOIL_POSITION': {'config': USOIL_CONFIG, 'strategy': OilStrategy, 'style': 'position'},
        'USTEC_POSITION': {'config': USTEC_CONFIG, 'strategy': IndicesStrategy, 'style': 'position'},
        'US30_POSITION': {'config': US30_CONFIG, 'strategy': IndicesStrategy, 'style': 'position'},
        
        # Scalping instruments
        'XAUUSD_SCALPING': {'config': XAUUSD_SCALPING, 'strategy': ScalpingStrategy, 'style': 'scalping'},
        'USOIL_SCALPING': {'config': USOIL_SCALPING, 'strategy': ScalpingStrategy, 'style': 'scalping'},
        'EURUSD_SCALPING': {'config': EURUSD_SCALPING, 'strategy': ScalpingStrategy, 'style': 'scalping'},
    }

    # Filter instruments based on mode and requested symbols
    selected_instruments = select_instruments(args, instrument_profiles)
    
    if not selected_instruments:
        logger.error("No instruments selected for trading")
        return

    # Initialize bots
    bots = initialize_bots(selected_instruments, news_filter, dashboard)
    
    if not bots:
        logger.error("No bots initialized successfully")
        return
    
    # Main trading loop
    logger.info(f"Started {len(bots)} bots: {[b.symbol for b in bots]}")
    
    try:
        cycle_count = 0
        while True:
            cycle_start = time.time()
            
            for bot in bots:
                try:
                    bot.run_single_cycle()
                    
                    # Update dashboard every 10 cycles
                    if cycle_count % 10 == 0:
                        dashboard.update_bot_status(bot)
                        
                except Exception as e:
                    logger.error(f"Error in {bot.symbol} ({bot.trading_style}) cycle: {e}")
            
            # Display dashboard every 30 cycles
            if cycle_count % 30 == 0:
                dashboard.display_status()
                cycle_count = 0
            
            cycle_count += 1
            cycle_time = time.time() - cycle_start
            
            # Adaptive sleep based on bot types
            sleep_time = calculate_sleep_time(bots, cycle_time)
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("Stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        # Cleanup and generate final report
        cleanup(bots, dashboard)

def select_instruments(args, instrument_profiles):
    """Select instruments based on mode and symbols"""
    selected = {}
    
    for inst_name, profile in instrument_profiles.items():
        base_symbol = inst_name.split('_')[0]  # Extract XAUUSD from XAUUSD_POSITION
        
        # Check if symbol is requested
        if base_symbol not in args.symbols:
            continue
            
        # Check if style matches mode
        if args.mode == 'both' or args.mode == profile['style']:
            selected[inst_name] = profile
    
    # Apply limits
    if args.mode == 'scalping' or args.mode == 'both':
        scalping_count = sum(1 for p in selected.values() if p['style'] == 'scalping')
        if scalping_count > args.max_scalping_bots:
            # Keep only the first N scalping bots
            scalping_keys = [k for k, v in selected.items() if v['style'] == 'scalping']
            for key in scalping_keys[args.max_scalping_bots:]:
                del selected[key]
    
    if args.mode == 'position' or args.mode == 'both':
        position_count = sum(1 for p in selected.values() if p['style'] == 'position')
        if position_count > args.max_position_bots:
            # Keep only the first N position bots
            position_keys = [k for k, v in selected.items() if v['style'] == 'position']
            for key in position_keys[args.max_position_bots:]:
                del selected[key]
    
    return selected

def initialize_bots(instrument_profiles, news_filter, dashboard):
    """Initialize trading bots"""
    bots = []
    
    for inst_name, profile in instrument_profiles.items():
        try:
            config = profile['config'].copy()
            config['INSTANCE_NAME'] = inst_name  # Add unique identifier
            
            strategy = profile['strategy'](config)
            bot = MultiInstrumentBot(strategy, config, news_filter)
            
            if bot.initialize():
                bots.append(bot)
                dashboard.add_bot(bot)
                logger.info(f"Successfully initialized {inst_name} ({profile['style']}) bot")
            else:
                logger.error(f"Failed to initialize {inst_name} bot")
                
        except Exception as e:
            logger.error(f"Error initializing {inst_name}: {e}")
    
    return bots

def calculate_sleep_time(bots, cycle_time):
    """Calculate adaptive sleep time based on bot types"""
    has_scalping = any(bot.trading_style == 'scalping' for bot in bots)
    has_position = any(bot.trading_style == 'position' for bot in bots)
    
    if has_scalping and has_position:
        # Mixed mode: balance between speed and resource usage
        return max(5 - cycle_time, 2)  # 2-5 seconds
    elif has_scalping:
        # Scalping only: faster cycles
        return max(2 - cycle_time, 1)  # 1-2 seconds
    else:
        # Position only: slower cycles
        return max(10 - cycle_time, 5)  # 5-10 seconds

def cleanup(bots, dashboard):
    """Cleanup and generate final reports"""
    logger.info("Shutting down bots and generating reports...")
    
    for bot in bots:
        try:
            # Generate performance report
            report = bot.get_performance_report()
            filename = f"report_{bot.symbol}_{bot.trading_style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(report)
            
            # Save equity curve plot
            plot_filename = f"equity_{bot.symbol}_{bot.trading_style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            bot.plot_equity_curve(plot_filename)
            
            bot.shutdown()
            
        except Exception as e:
            logger.error(f"Error during cleanup for {bot.symbol}: {e}")
    
    # Generate overall dashboard report
    dashboard.generate_summary_report()
    logger.info("Cleanup completed")

def run_backtest_mode(args):
    """Run backtest mode (simplified)"""
    logger.info("Backtest mode not implemented for dual mode yet")
    # Would require separate backtest logic for each style

def generate_sample_data(symbol, days):
    """Generate sample data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days*24, freq='H')
    returns = np.random.normal(0, 0.001, len(dates))
    prices = 1000 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'open': prices * 0.999,
        'high': prices * 1.001,
        'low': prices * 0.999,
        'close': prices,
        'tick_volume': np.random.randint(100, 1000, len(dates))
    }, index=dates)
    
    return data

if __name__ == "__main__":
    main()