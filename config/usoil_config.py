"""
USOIL (Crude Oil) specific configuration
"""

from .base_config import BASE_CONFIG

USOIL_CONFIG = {
    **BASE_CONFIG,
    
    "SYMBOL": "USOIL",
    "DISPLAY_NAME": "Crude Oil",
    "TRADING_STYLE": "position",
    "STYLE_DESCRIPTION": "Swing trading with 2-5 day holds",
    
    # Oil-specific parameters
    "SL_ATR_MULTIPLIER": 1.8,  # Wider stops for oil volatility
    "TP_RR": 1.8,              # Higher reward ratio for oil
    "FIB_PROX_PCT": 0.012,     # Larger proximity for oil
    "DAILY_SR_PROX_PCT": 0.009,
    "FALSE_BREAK_WICK_BODY_RATIO": 1.8,
    "FALSE_BREAK_MIN_ATR_RATIO": 0.6,
    "MAX_SPREAD_POINTS": 15,   # Higher spread tolerance for oil
    
    # Oil-specific session filters
    "SESSION_OPEN_FILTERS": [
        {"start_h": 13, "start_m": 30, "skip_minutes": 45},  # US energy market open
        {"start_h": 21, "start_m": 0, "skip_minutes": 30},   # API report times
    ],
    
    # Oil-specific economic events
    "ECONOMIC_EVENTS": [
        {"name": "EIA", "skip_hours": 3},
        {"name": "API", "skip_hours": 2},
        {"name": "OPEC", "skip_hours": 6},
        {"name": "Inventory", "skip_hours": 2},
    ],
    
    # Oil-specific time filters
    "TRADING_HOURS": {
        "start_hour": 3,    # 3 AM UTC
        "end_hour": 20,     # 8 PM UTC
    }
}