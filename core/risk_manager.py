"""
Risk management component
"""

import MetaTrader5 as mt5
import logging
from datetime import datetime

logger = logging.getLogger("RiskManager")

class RiskManager:
    """Handles risk management across all instruments"""
    
    def __init__(self, global_daily_loss_limit=3.0, global_max_drawdown=15.0):
        self.global_daily_loss_limit = global_daily_loss_limit
        self.global_max_drawdown = global_max_drawdown
        self.global_equity_peak = 0
        self.global_daily_start = 0
        self.position_count = 0
        
    def initialize(self):
        """Initialize risk manager with current account values"""
        try:
            account = mt5.account_info()
            if account:
                self.global_equity_peak = account.equity
                self.global_daily_start = account.equity
                return True
        except Exception as e:
            logger.error(f"Risk manager initialization error: {e}")
        return False
    
    def check_global_limits(self):
        """Check global risk limits across all instruments"""
        try:
            account = mt5.account_info()
            if not account:
                return False
                
            equity = account.equity
            
            # Update global equity peak
            self.global_equity_peak = max(self.global_equity_peak, equity)
            
            # Check global daily loss limit
            daily_pnl_pct = ((equity - self.global_daily_start) / self.global_daily_start) * 100
            if daily_pnl_pct <= -self.global_daily_loss_limit:
                logger.warning(f"GLOBAL daily loss limit reached: {daily_pnl_pct:.2f}%")
                return False
                
            # Check global max drawdown
            drawdown_pct = ((self.global_equity_peak - equity) / self.global_equity_peak) * 100
            if drawdown_pct >= self.global_max_drawdown:
                logger.warning(f"GLOBAL max drawdown reached: {drawdown_pct:.2f}%")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking global limits: {e}")
            return False
    
    def check_instrument_limits(self, config):
        """Check instrument-specific risk limits"""
        try:
            account = mt5.account_info()
            if not account:
                return False
                
            # Check maximum open positions for this instrument
            positions = mt5.positions_get(symbol=config["SYMBOL"])
            if positions is None:
                current_positions = 0
            else:
                current_positions = len(positions)
                
            if current_positions >= config.get("MAX_OPEN_POSITIONS", 1):
                return False
                
            # Check spread
            tick = mt5.symbol_info_tick(config["SYMBOL"])
            if tick:
                spread_points = (tick.ask - tick.bid) / mt5.symbol_info(config["SYMBOL"]).point
                if spread_points > config.get("MAX_SPREAD_POINTS", 10):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error checking instrument limits: {e}")
            return False
    
    def calculate_position_size(self, symbol, stop_loss_price, side, risk_percent):
        """Calculate position size with risk management"""
        try:
            account = mt5.account_info()
            if not account:
                return 0.01
                
            equity = account.equity
            risk_amount = equity * (risk_percent / 100.0)
            
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return 0.01
                
            price = tick.ask if side == 'buy' else tick.bid
            distance = abs(price - stop_loss_price)
            
            if distance <= 0:
                return 0.01
                
            # Calculate lot size
            contract_size = mt5.symbol_info(symbol).trade_contract_size
            tick_value = 1.0  # Default for most forex symbols
            
            # Adjust for different instruments
            if "XAU" in symbol or "XAG" in symbol:
                # Gold/Silver: 1 lot = 100 oz, 0.01 movement = $1
                risk_per_lot = (distance / 0.01) * 1.0
            elif "USOIL" in symbol:
                # Oil: different calculation needed
                risk_per_lot = distance * contract_size
            else:
                # Indices and others
                risk_per_lot = distance * contract_size
                
            if risk_per_lot <= 0:
                return 0.01
                
            lots = risk_amount / risk_per_lot
            lots = round(lots, 2)
            
            # Apply min/max limits
            min_lot = 0.01
            max_lot = 5.0
            lots = max(min_lot, min(max_lot, lots))
            
            return lots
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01
    
    def reset_daily(self):
        """Reset daily values at the start of a new trading day"""
        try:
            account = mt5.account_info()
            if account:
                self.global_daily_start = account.equity
        except Exception as e:
            logger.error(f"Error resetting daily values: {e}")