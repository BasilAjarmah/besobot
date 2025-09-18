"""
Base configuration for all instruments
"""

# Base trading parameters
BASE_CONFIG = {
    "RUN_BACKTEST": False,
    "BACKTEST_FROM": "2024-01-01",
    "BACKTEST_TO": "2024-12-31",
    
    # Risk management
    "RISK_PERCENT": 0.3,
    "MIN_LOT": 0.01,
    "MAX_LOT": 5.0,
    "COMMISSION_PER_LOT": 3.5,
    "DAILY_LOSS_LIMIT": 2.0,
    "MAX_DRAWDOWN": 10.0,
    "MAX_OPEN_POSITIONS": 1,
    
    # Execution settings
    "DEVIATION": 50,
    "MAGIC_NUMBER": 20250917,
    "SLEEP_SECONDS": 30,
    "MAX_RECONNECT_ATTEMPTS": 5,
    "RECONNECT_DELAY": 10,
    
    # Logging
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "trading_bot.log",
    
    # Common indicator periods
    "EMA_FAST": 9,
    "EMA_SLOW": 21,
    "RSI_PERIOD": 9,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "ATR_PERIOD": 14,
    "BB_PERIOD": 20,
    
    # Common trading rules
    "FALSE_BREAK_CANDLES": 3,
    "MIN_CONFIRMATIONS": 3,
}