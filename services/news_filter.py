"""
News impact analysis and trading filters - SCALPING DISABLED
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .economic_calendar import EconomicCalendar
import logging

logger = logging.getLogger("NewsFilter")

class NewsFilter:
    def __init__(self, economic_calendar: EconomicCalendar):
        self.calendar = economic_calendar
        self.impact_thresholds = {
            'scalping': 999.9,  # 🚨 EXTREMELY HIGH - effectively DISABLED for scalping
            'position': 0.3,    # Still active for position trading
            'default': 0.5
        }
        
    def should_avoid_trading(self, symbol: str, timestamp: datetime = None, 
                           trading_style: str = "position") -> bool:
        """
        Determine if trading should be avoided due to news events
        SCALPING: ALWAYS ALLOWED (news disabled)
        POSITION: Normal news filtering
        """
        # 🚨 SCALPING: NEVER avoid trading due to news
        if trading_style == "scalping":
            return False
            
        # For position trading, use normal news filtering
        if timestamp is None:
            timestamp = datetime.now()
        
        impact_score = self.calendar.get_event_impact_score(symbol, timestamp)
        threshold = self.impact_thresholds.get(trading_style, self.impact_thresholds['default'])
        
        # Debug logging
        if impact_score > 0.1:
            logger.debug(f"News impact for {symbol} ({trading_style}): {impact_score:.2f}/{
                threshold} - {'AVOID' if impact_score > threshold else 'OK'}")
        
        return impact_score > threshold
    
    def get_trading_recommendation(self, symbol: str, trading_style: str = "position") -> Dict[str, any]:
        """Get trading recommendation - ALWAYS OK for scalping"""
        if trading_style == "scalping":
            return {
                'avoid_trading': False, 
                'reason': 'News filtering disabled for scalping',
                'impact_score': 0.0,
                'threshold': 999.9,
                'trading_style': trading_style
            }
            
        events = self.calendar.get_events([symbol], days=1)
        now = datetime.now()
        threshold = self.impact_thresholds.get(trading_style, self.impact_thresholds['default'])
        
        # Find the next high-impact event
        next_event = None
        for event in events:
            if event.get('importance') == 'high' and event['date'] > now:
                if next_event is None or event['date'] < next_event['date']:
                    next_event = event
        
        if not next_event:
            return {
                'avoid_trading': False, 
                'reason': 'No high-impact events',
                'impact_score': 0.0,
                'threshold': threshold,
                'trading_style': trading_style
            }
        
        hours_until_event = (next_event['date'] - now).total_seconds() / 3600
        current_impact = self.calendar.get_event_impact_score(symbol, now)
        
        recommendation = {
            'avoid_trading': current_impact > threshold,
            'reason': f"{next_event['title']} in {hours_until_event:.1f}h",
            'event': next_event,
            'hours_until': hours_until_event,
            'current_impact': current_impact,
            'threshold': threshold,
            'trading_style': trading_style
        }
        
        recommendation['advice'] = 'Position trading sensitive to news events'
        
        return recommendation
    
    def adjust_risk_parameters(self, symbol: str, original_params: Dict, 
                             trading_style: str = "position") -> Dict:
        """Adjust risk parameters - NO adjustment for scalping"""
        if trading_style == "scalping":
            # 🚨 SCALPING: No risk adjustment for news
            return original_params
            
        # Position trading: normal risk adjustment
        impact_score = self.calendar.get_event_impact_score(symbol)
        threshold = self.impact_thresholds.get(trading_style, self.impact_thresholds['default'])
        
        adjusted_params = original_params.copy()
        
        if impact_score > threshold:
            # Position trading: significant reduction
            adjusted_params['RISK_PERCENT'] = original_params['RISK_PERCENT'] * 0.5
            adjusted_params['SL_ATR_MULTIPLIER'] = original_params['SL_ATR_MULTIPLIER'] * 1.5
            
            logger.info(f"Reduced risk for {symbol} due to news impact: {impact_score:.2f}")
            
        elif impact_score > threshold * 0.5:
            # Position trading: moderate adjustment
            adjusted_params['RISK_PERCENT'] = original_params['RISK_PERCENT'] * 0.8
            adjusted_params['SL_ATR_MULTIPLIER'] = original_params['SL_ATR_MULTIPLIER'] * 1.2
        
        return adjusted_params
    
    def get_news_summary(self, symbol: str, hours_ahead: int = 24) -> Dict[str, List]:
        """Get summary of upcoming news events"""
        events = self.calendar.get_events([symbol], days=2)
        now = datetime.now()
        
        upcoming = []
        recent = []
        
        for event in events:
            hours_diff = (event['date'] - now).total_seconds() / 3600
            
            if -2 <= hours_diff <= hours_ahead:
                event_info = {
                    'title': event.get('title', 'Unknown'),
                    'importance': event.get('importance', 'medium'),
                    'date': event['date'],
                    'hours_from_now': hours_diff,
                    'country': event.get('country', ''),
                    'previous': event.get('previous'),
                    'forecast': event.get('forecast')
                }
                
                if hours_diff >= 0:
                    upcoming.append(event_info)
                else:
                    recent.append(event_info)
        
        upcoming.sort(key=lambda x: x['hours_from_now'])
        
        return {
            'upcoming_events': upcoming,
            'recent_events': recent,
            'symbol': symbol,
            'current_time': now
        }
    
    def is_safe_to_trade(self, symbol: str, trading_style: str = "position", 
                       minutes_buffer: int = 30) -> bool:
        """
        Check if it's safe to trade - ALWAYS TRUE for scalping
        """
        if trading_style == "scalping":
            return True
            
        events = self.calendar.get_events([symbol], days=1)
        now = datetime.now()
        
        for event in events:
            if event.get('importance') in ['high', 'medium']:
                event_time = event['date']
                time_diff = (event_time - now).total_seconds() / 60
                
                buffer_minutes = minutes_buffer
                if event.get('importance') == 'high':
                    buffer_minutes = minutes_buffer * 2
                
                if abs(time_diff) <= buffer_minutes:
                    logger.debug(f"Near news event: {event.get('title')} ({
                        time_diff:.0f} minutes)")
                    return False
        
        return True
    
    def get_optimal_trading_windows(self, symbol: str, trading_style: str = "position",
                                  lookahead_hours: int = 6) -> List[Dict]:
        """
        Find optimal trading windows between news events
        Returns empty list for scalping (always optimal)
        """
        if trading_style == "scalping":
            return [{
                'start': datetime.now(),
                'end': datetime.now() + timedelta(hours=lookahead_hours),
                'duration_hours': lookahead_hours,
                'before_event': 'Always optimal for scalping'
            }]
            
        events = self.calendar.get_events([symbol], days=1)
        now = datetime.now()
        windows = []
        
        relevant_events = []
        for event in events:
            if event.get('importance') in ['high', 'medium']:
                event_time = event['date']
                hours_diff = (event_time - now).total_seconds() / 3600
                if -1 <= hours_diff <= lookahead_hours:
                    relevant_events.append({
                        'time': event_time,
                        'importance': event.get('importance'),
                        'title': event.get('title', ''),
                        'hours_from_now': hours_diff
                    })
        
        relevant_events.sort(key=lambda x: x['time'])
        
        previous_end = now
        for event in relevant_events:
            buffer_hours = 1.0 if event['importance'] == 'high' else 0.5
            
            window_start = previous_end
            window_end = event['time'] - timedelta(hours=buffer_hours)
            
            if window_start < window_end:
                window_duration = (window_end - window_start).total_seconds() / 3600
                if window_duration >= 0.5:
                    windows.append({
                        'start': window_start,
                        'end': window_end,
                        'duration_hours': window_duration,
                        'before_event': event['title']
                    })
            
            previous_end = event['time'] + timedelta(hours=buffer_hours)
        
        final_end = now + timedelta(hours=lookahead_hours)
        if previous_end < final_end:
            final_duration = (final_end - previous_end).total_seconds() / 3600
            if final_duration >= 0.5:
                windows.append({
                    'start': previous_end,
                    'end': final_end,
                    'duration_hours': final_duration,
                    'before_event': 'End of period'
                })
        
        return windows
    
    def is_scalping_allowed(self) -> bool:
        """Helper method to check if scalping is allowed (always True)"""
        return True
    
    def is_position_trading_allowed(self, symbol: str) -> bool:
        """Helper method to check if position trading is allowed"""
        return not self.should_avoid_trading(symbol, None, 'position')