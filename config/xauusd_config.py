"""
XAUUSD (Gold) specific configuration
"""

from .base_config import BASE_CONFIG

XAUUSD_CONFIG = {
    **BASE_CONFIG,
    
    "SYMBOL": "XAUUSD",
    "DISPLAY_NAME": "Gold",
    
    # Trading style identification
    "TRADING_STYLE": "position",
    "STYLE_DESCRIPTION": "Swing trading with 2-5 day holds",
    
    # Gold-specific parameters
    "SL_ATR_MULTIPLIER": 1.5,
    "TP_RR": 1.5,
    "FIB_PROX_PCT": 0.008,
    "DAILY_SR_PROX_PCT": 0.006,
    "FALSE_BREAK_WICK_BODY_RATIO": 1.5,
    "FALSE_BREAK_MIN_ATR_RATIO": 0.5,
    "MAX_SPREAD_POINTS": 10,
    
    # Gold-specific session filters
    "SESSION_OPEN_FILTERS": [
        {"start_h": 11, "start_m": 0, "skip_minutes": 30},   # London
        {"start_h": 16, "start_m": 0, "skip_minutes": 30},  # New York
        {"start_h": 4, "start_m": 0, "skip_minutes": 15},   # Asia
        {"start_h": 1, "start_m": 0, "skip_minutes": 30},  # America/Asia overlap
    ],
    
    # Gold-specific economic events
    "ECONOMIC_EVENTS": [
        {"name": "NFP", "skip_hours": 2},
        {"name": "FOMC", "skip_hours": 4},
        {"name": "CPI", "skip_hours": 2},
        {"name": "PMI", "skip_hours": 1},
    ],
    
    # Gold-specific time filters
    "TRADING_HOURS": {
        "start_hour": 1,    # 1 AM UTC
        "end_hour": 22,     # 10 PM UTC
    },
    
    # Position trading specific parameters
    "MAX_TRADE_HOURS": 72,          # 3 days maximum trade duration
    "REQUIRED_CONFIDENCE": 0.8,     # High confidence required for entries
    "PARTIAL_PROFIT_LEVELS": [      # Partial profit taking levels (profit_pct, close_pct)
        (1.0, 0.3),  # At 1% profit, close 30% of position
        (2.0, 0.3),  # At 2% profit, close another 30%
        (3.0, 0.4),  # At 3% profit, close remaining 40%
    ]
}