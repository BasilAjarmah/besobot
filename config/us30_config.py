"""
US30 (Dow Jones) specific configuration
"""

from .base_config import BASE_CONFIG

US30_CONFIG = {
    **BASE_CONFIG,
    
    "SYMBOL": "US30",
    "DISPLAY_NAME": "Dow Jones",
    "TRADING_STYLE": "position",
    "STYLE_DESCRIPTION": "Swing trading with 2-5 day holds",
    
    # Dow Jones-specific parameters
    "SL_ATR_MULTIPLIER": 1.4,
    "TP_RR": 1.4,
    "FIB_PROX_PCT": 0.006,
    "DAILY_SR_PROX_PCT": 0.005,
    "FALSE_BREAK_WICK_BODY_RATIO": 1.4,
    "FALSE_BREAK_MIN_ATR_RATIO": 0.45,
    "MAX_SPREAD_POINTS": 9,
    
    # Dow-specific session filters
    "SESSION_OPEN_FILTERS": [
        {"start_h": 13, "start_m": 30, "skip_minutes": 45},  # US market open
        {"start_h": 20, "start_m": 0, "skip_minutes": 30},   # After-hours
    ],
    
    # Dow-specific economic events
    "ECONOMIC_EVENTS": [
        {"name": "FOMC", "skip_hours": 4},
        {"name": "NFP", "skip_hours": 3},
        {"name": "CPI", "skip_hours": 2},
        {"name": "Manufacturing Data", "skip_hours": 1},
    ],
    
    # Dow-specific time filters
    "TRADING_HOURS": {
        "start_hour": 13,   # 1 PM UTC (9 AM EST)
        "end_hour": 20,     # 8 PM UTC (4 PM EST)
    }
}