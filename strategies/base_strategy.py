"""
Base strategy class that all instrument strategies inherit from
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, config: dict):
        self.config = config
        self.symbol = config["SYMBOL"]
        self.display_name = config.get("DISPLAY_NAME", self.symbol)
        
    @abstractmethod
    def calculate_confirmations(self, df: pd.DataFrame, 
                              fib_levels: dict, 
                              daily_levels: dict, 
                              weekly_bias: str) -> dict:
        """Calculate trading confirmations - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def is_false_breakout(self, df_recent: pd.DataFrame, 
                         level: float, direction: str) -> bool:
        """Check for false breakout - must be implemented by subclasses"""
        pass
    
    def calculate_sl_tp(self, current_price: float, atr_val: float, direction: str) -> tuple:
        """Calculate stop loss and take profit levels"""
        sl_multiplier = self.config.get("SL_ATR_MULTIPLIER", 1.5)
        tp_rr = self.config.get("TP_RR", 1.5)
        
        if direction == 'buy':
            sl_price = current_price - sl_multiplier * atr_val
            tp_price = current_price + tp_rr * (current_price - sl_price)
        else:
            sl_price = current_price + sl_multiplier * atr_val
            tp_price = current_price - tp_rr * (sl_price - current_price)
            
        return sl_price, tp_price
    
    def get_required_confirmations(self) -> int:
        """Get minimum required confirmations"""
        return self.config.get("MIN_CONFIRMATIONS", 3)