"""
USTEC (Nasdaq) specific configuration
"""

from .base_config import BASE_CONFIG

USTEC_CONFIG = {
    **BASE_CONFIG,
    
    "SYMBOL": "USTEC",
    "DISPLAY_NAME": "Nasdaq 100",
    "TRADING_STYLE": "position",
    "STYLE_DESCRIPTION": "Swing trading with 2-5 day holds",
    
    # Nasdaq-specific parameters
    "SL_ATR_MULTIPLIER": 1.3,
    "TP_RR": 1.3,
    "FIB_PROX_PCT": 0.005,
    "DAILY_SR_PROX_PCT": 0.004,
    "FALSE_BREAK_WICK_BODY_RATIO": 1.3,
    "FALSE_BREAK_MIN_ATR_RATIO": 0.4,
    "MAX_SPREAD_POINTS": 8,
    
    # Nasdaq-specific session filters
    "SESSION_OPEN_FILTERS": [
        {"start_h": 13, "start_m": 30, "skip_minutes": 45},  # US market open
        {"start_h": 20, "start_m": 0, "skip_minutes": 30},   # After-hours volatility
    ],
    
    # Nasdaq-specific economic events
    "ECONOMIC_EVENTS": [
        {"name": "FOMC", "skip_hours": 4},
        {"name": "Tech Earnings", "skip_hours": 3},
        {"name": "CPI", "skip_hours": 2},
        {"name": "Retail Sales", "skip_hours": 1},
    ],
    
    # Nasdaq-specific time filters
    "TRADING_HOURS": {
        "start_hour": 13,   # 1 PM UTC (9 AM EST)
        "end_hour": 20,     # 8 PM UTC (4 PM EST)
    }
}