"""
Strategy parameter optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Callable
from backtesting.backtest_engine import BacktestEngine
from strategies.base_strategy import BaseStrategy

class StrategyOptimizer:
    def __init__(self, strategy_class: Callable, config: Dict, data: pd.DataFrame):
        self.strategy_class = strategy_class
        self.base_config = config
        self.data = data
        self.results = []
        
    def optimize_parameters(self, param_grid: Dict[str, List[Any]], 
                          metric: str = 'sharpe_ratio') -> Dict[str, Any]:
        """Optimize strategy parameters using grid search"""
        best_score = -float('inf')
        best_params = None
        best_result = None
        
        # Generate all parameter combinations
        param_combinations = self.generate_parameter_combinations(param_grid)
        
        print(f"Testing {len(param_combinations)} parameter combinations...")
        
        for i, params in enumerate(param_combinations):
            # Update config with current parameters
            current_config = self.base_config.copy()
            current_config.update(params)
            
            # Run backtest
            strategy = self.strategy_class(current_config)
            engine = BacktestEngine(strategy, current_config)
            result = engine.run_backtest(self.data)
            
            if 'error' in result:
                continue
                
            # Calculate performance metric
            score = self.calculate_metric(result, metric)
            
            # Store result
            self.results.append({
                'params': params,
                'score': score,
                'result': result
            })
            
            # Update best parameters
            if score > best_score:
                best_score = score
                best_params = params
                best_result = result
            
            print(f"Combination {i+1}/{len(param_combinations)}: {score:.3f}")
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'best_result': best_result,
            'all_results': self.results
        }
    
    def generate_parameter_combinations(self, param_grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """Generate all combinations of parameters"""
        from itertools import product
        
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        combinations = []
        for combination in product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
            
        return combinations
    
    def calculate_metric(self, result: Dict[str, Any], metric: str) -> float:
        """Calculate specified performance metric"""
        if metric == 'sharpe_ratio':
            return result.get('sharpe_ratio', 0)
        elif metric == 'profit_factor':
            return result.get('profit_factor', 0)
        elif metric == 'win_rate':
            return result.get('win_rate', 0)
        elif metric == 'total_pnl':
            return result.get('total_pnl', 0)
        elif metric == 'calmar_ratio':
            return result.get('calmar_ratio', 0)
        else:
            return result.get(metric, 0)
    
    def walk_forward_optimization(self, param_grid: Dict[str, List[Any]], 
                                train_ratio: float = 0.7,
                                n_windows: int = 5,
                                metric: str = 'sharpe_ratio') -> Dict[str, Any]:
        """Perform walk-forward optimization"""
        total_length = len(self.data)
        train_length = int(total_length * train_ratio)
        window_size = train_length // n_windows
        
        results = []
        
        for i in range(n_windows):
            # Split data into train and test
            train_start = i * window_size
            train_end = train_start + train_length
            test_start = train_end
            test_end = min(test_start + window_size, total_length)
            
            train_data = self.data.iloc[train_start:train_end]
            test_data = self.data.iloc[test_start:test_end]
            
            if len(train_data) == 0 or len(test_data) == 0:
                continue
            
            # Optimize on training data
            optimizer = StrategyOptimizer(self.strategy_class, self.base_config, train_data)
            optimization_result = optimizer.optimize_parameters(param_grid, metric)
            
            # Test on out-of-sample data
            best_params = optimization_result['best_params']
            test_config = self.base_config.copy()
            test_config.update(best_params)
            
            test_strategy = self.strategy_class(test_config)
            test_engine = BacktestEngine(test_strategy, test_config)
            test_result = test_engine.run_backtest(test_data)
            
            results.append({
                'window': i,
                'train_period': (train_start, train_end),
                'test_period': (test_start, test_end),
                'best_params': best_params,
                'train_score': optimization_result['best_score'],
                'test_score': self.calculate_metric(test_result, metric),
                'test_result': test_result
            })
        
        return results
