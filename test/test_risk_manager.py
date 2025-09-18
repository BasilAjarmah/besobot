"""
Unit tests for risk management
"""

import pytest
from core.risk_manager import RiskManager

class TestRiskManager:
    @pytest.fixture
    def risk_manager(self):
        return RiskManager()
    
    def test_calculate_position_size(self, risk_manager):
        # Test position size calculation
        pass
    
    def test_check_global_limits(self, risk_manager):
        # Test global risk limits
        pass