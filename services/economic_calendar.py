"""
Economic calendar API integration
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("EconomicCalendar")

class EconomicCalendar:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://economic-calendar.tradingview.com/events"
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache
        
    def get_events(self, symbols: List[str], days: int = 7) -> List[Dict]:
        """Get economic events for specified symbols"""
        events = []
        current_time = datetime.now()
        
        for symbol in symbols:
            cache_key = f"{symbol}_{days}_{current_time.strftime('%Y%m%d')}"
            
            # Check cache first
            if cache_key in self.cache:
                cached_events, timestamp = self.cache[cache_key]
                if (current_time - timestamp).total_seconds() < self.cache_duration:
                    events.extend(cached_events)
                    continue
            
            # Fetch events from API
            symbol_events = self.fetch_events(symbol, days)
            self.cache[cache_key] = (symbol_events, current_time)
            events.extend(symbol_events)
        
        return self.filter_relevant_events(events)
    
    def fetch_events(self, symbol: str, days: int) -> List[Dict]:
        """Fetch events from economic calendar API"""
        # Map trading symbol to economic calendar symbol
        calendar_symbol = self.map_symbol_to_calendar(symbol)
        
        if not calendar_symbol:
            return []
        
        try:
            # This is a simplified version - would use real API in production
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            params = {
                'country': calendar_symbol,
                'days': days
            }
            
            # response = requests.get(self.base_url, headers=headers, params=params)
            # response.raise_for_status()
            # events = response.json()
            
            # Simulated response for development
            events = self.get_simulated_events(calendar_symbol, days)
            return events
            
        except Exception as e:
            logger.error(f"Error fetching economic events: {e}")
            return []
    
    def map_symbol_to_calendar(self, symbol: str) -> Optional[str]:
        """Map trading symbol to economic calendar country code"""
        mapping = {
            'XAUUSD': 'US',    # Gold primarily affected by US events
            'XAGUSD': 'US',    # Silver primarily affected by US events
            'USOIL': 'US',     # Oil affected by US events and OPEC
            'USTEC': 'US',     # Nasdaq affected by US events
            'US30': 'US',      # Dow Jones affected by US events
        }
        return mapping.get(symbol, None)
    
    def get_simulated_events(self, country: str, days: int) -> List[Dict]:
        """Generate simulated economic events for testing"""
        events = []
        now = datetime.now()
        
        if country == 'US':
            # US economic events
            event_templates = [
                {
                    'title': 'Non-Farm Payrolls',
                    'importance': 'high',
                    'date': now + timedelta(hours=2),
                    'country': 'US',
                    'previous': 200,
                    'forecast': 180,
                    'actual': None
                },
                {
                    'title': 'CPI (YoY)',
                    'importance': 'high',
                    'date': now + timedelta(days=1, hours=10),
                    'country': 'US',
                    'previous': 3.2,
                    'forecast': 3.0,
                    'actual': None
                },
                {
                    'title': 'FOMC Statement',
                    'importance': 'high',
                    'date': now + timedelta(days=3, hours=14),
                    'country': 'US',
                    'previous': None,
                    'forecast': None,
                    'actual': None
                }
            ]
            
            for template in event_templates:
                if template['date'] <= now + timedelta(days=days):
                    events.append(template)
        
        return events
    
    def filter_relevant_events(self, events: List[Dict]) -> List[Dict]:
        """Filter events to only include relevant ones for trading decisions"""
        relevant_events = []
        now = datetime.now()
        
        for event in events:
            # Only include future events and recent past events
            event_time = event['date']
            hours_until_event = (event_time - now).total_seconds() / 3600
            
            if -2 <= hours_until_event <= 48:  # 2 hours past to 48 hours future
                relevant_events.append(event)
        
        return relevant_events
    
    def is_high_impact_event_soon(self, symbol: str, hours_ahead: int = 4) -> bool:
        """Check if high impact event is coming soon for a symbol"""
        events = self.get_events([symbol], days=2)
        now = datetime.now()
        
        for event in events:
            if event.get('importance') == 'high':
                event_time = event['date']
                hours_until_event = (event_time - now).total_seconds() / 3600
                
                if 0 < hours_until_event <= hours_ahead:
                    return True
        
        return False
    
    def get_event_impact_score(self, symbol: str, timestamp: datetime) -> float:
        """Calculate event impact score for a specific time"""
        events = self.get_events([symbol], days=1)
        impact_score = 0.0
        now = datetime.now()
        
        for event in events:
            event_time = event['date']
            hours_diff = abs((event_time - timestamp).total_seconds() / 3600)
            
            # Event impact decreases with time distance
            time_factor = max(0, 1 - (hours_diff / 6))  # 6-hour window
            
            importance_factor = {
                'high': 1.0,
                'medium': 0.5,
                'low': 0.2
            }.get(event.get('importance', 'low'), 0.1)
            
            impact_score += time_factor * importance_factor
        
        return min(impact_score, 1.0)  # Cap at 1.0