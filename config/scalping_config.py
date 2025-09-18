"""
Scalping-specific configurations for various instruments
"""

from config.base_config import BASE_CONFIG

# Base scalping configuration
SCALPING_BASE = {
    **BASE_CONFIG,
    
    # Ultra-fast settings
    "SLEEP_SECONDS": 2,           # Check every 2 seconds instead of 30
    "TIMEFRAME": "M1",           # Use 1-minute charts instead of M5
    "TRADING_STYLE": "scalping",
    "STYLE_DESCRIPTION": "1-5 minute scalps with tight stops",
    
    # Tight risk management
    "RISK_PERCENT": 0.5,         # Slightly higher risk for scalping
    "SL_ATR_MULTIPLIER": 0.5,    # Tighter stops (0.5x ATR instead of 1.5)
    "TP_RR": 1.0,                # 1:1 risk-reward for scalping
    
    # Faster entry requirements
    "MIN_CONFIRMATIONS": 2,      # Fewer confirmations needed
    
    # Short trade duration
    "MAX_TRADE_HOURS": 0.5,      # 30 minutes max trade duration
    "QUICK_EXIT_THRESHOLD": 0.3, # Take quick profits at 30%
    
    # Scalping-specific filters
    "MIN_VOLUME": 1000,          # Minimum volume requirement
    "MAX_SPREAD_POINTS": 5,      # Tighter spread requirement
    "REQUIRED_CONFIDENCE": 0.6,  # Lower confidence threshold for faster entries
}

# Gold scalping configuration
XAUUSD_SCALPING = {
    **SCALPING_BASE,
    "SYMBOL": "XAUUSD",
    "DISPLAY_NAME": "Gold Scalping",
    "SL_ATR_MULTIPLIER": 0.3,    # Even tighter stops for gold
    "TP_RR": 0.8,                # Smaller targets for gold scalping
    "MIN_VOLUME": 1500,          # Higher volume requirement for gold
    "MAX_SPREAD_POINTS": 8,      # Slightly higher spread tolerance for gold
}

# Oil scalping configuration
USOIL_SCALPING = {
    **SCALPING_BASE,
    "SYMBOL": "USOIL",
    "DISPLAY_NAME": "Oil Scalping",
    "SL_ATR_MULTIPLIER": 0.4,
    "TP_RR": 1.0,
    "MIN_VOLUME": 2000,          # Oil typically has higher volume
    "MAX_SPREAD_POINTS": 10,     # Higher spread tolerance for oil
}

# EURUSD scalping configuration
EURUSD_SCALPING = {
    **SCALPING_BASE,
    "SYMBOL": "EURUSD",
    "DISPLAY_NAME": "EURUSD Scalping",
    "SL_ATR_MULTIPLIER": 0.2,    # Very tight stops for forex
    "TP_RR": 1.2,                # Better risk-reward for forex
    "MIN_VOLUME": 3000,          # High volume requirement for major forex
    "MAX_SPREAD_POINTS": 2,      # Very tight spread requirement
    "SESSION_OPEN_FILTERS": [    # Forex-specific sessions
        {"start_h": 10, "start_m": 0, "skip_minutes": 30},   # London open
        {"start_h": 16, "start_m": 0, "skip_minutes": 30},  # New York open
        {"start_h": 1, "start_m": 0, "skip_minutes": 30},  # Asia open
    ],
}