"""
XAGUSD (Silver) specific configuration
"""

from .base_config import BASE_CONFIG

XAGUSD_CONFIG = {
    **BASE_CONFIG,
    
    "SYMBOL": "XAGUSD",
    "DISPLAY_NAME": "Silver",
    "TRADING_STYLE": "position",
    "STYLE_DESCRIPTION": "Swing trading with 2-5 day holds",
    
    # Silver-specific parameters (more volatile than gold)
    "SL_ATR_MULTIPLIER": 1.7,
    "TP_RR": 1.7,
    "FIB_PROX_PCT": 0.01,
    "DAILY_SR_PROX_PCT": 0.008,
    "FALSE_BREAK_WICK_BODY_RATIO": 1.7,
    "FALSE_BREAK_MIN_ATR_RATIO": 0.6,
    "MAX_SPREAD_POINTS": 12,
    
    # Silver-specific session filters
    "SESSION_OPEN_FILTERS": [
        {"start_h": 11, "start_m": 0, "skip_minutes": 30},   # London
        {"start_h": 16, "start_m": 0, "skip_minutes": 30},  # New York
        {"start_h": 4, "start_m": 0, "skip_minutes": 15},   # Asia
        {"start_h": 1, "start_m": 0, "skip_minutes": 30},  # America/Asia overlap
    ],
    
    # Silver-specific economic events
    "ECONOMIC_EVENTS": [
        {"name": "NFP", "skip_hours": 2},
        {"name": "FOMC", "skip_hours": 4},
        {"name": "CPI", "skip_hours": 2},
        {"name": "Industrial Production", "skip_hours": 1},
    ],
    
    # Silver-specific time filters
    "TRADING_HOURS": {
        "start_hour": 1,    # 1 AM UTC
        "end_hour": 22,     # 10 PM UTC
    }
}