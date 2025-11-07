"""
Testing, Benchmarking and Quality Assurance Module

Comprehensive testing framework for health economic evaluation models including
unit tests, integration tests, performance benchmarks, and quality assurance tools.
"""

import unittest
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import time
import statistics
from typing import Dict, List, Any, Callable
import warnings
import logging
from datetime import datetime
import os
from contextlib import contextmanager

# Import core modules we're testing
from scripts.models import *
from scripts.core import *

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HEATestSuite(unittest.TestCase):
    """
    Comprehensive test suite for Health Economic Analysis tools.
    """
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data_dir = Path("tests/data")
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Create sample data for testing
        self.sample_params = {
            'treatment_effects': [0.6, 0.75, 0.7],
            'treatment_costs': [5000, 7000, 6000],
            'time_horizon': 10,
            'discount_rate': 0.035
        }
    
    def test_cea_engine_basic(self):
        """Test basic functionality of CEA engine."""
        from scripts.models.cea_engine import CEAEngine
        
        # Create a basic CEA engine
        cea = CEAEngine()
        
        # Test with minimal parameters
        params = {
            'strategies': ['A', 'B'],
            'costs': [1000, 1200],
            'effects': [0.5, 0.6],
            'wtp_threshold': 50000
        }
        
        # Run analysis
        result = cea.analyze(params)
        
        # Check results structure
        self.assertIn('icers', result)
        self.assertIn('cost_effectiveness', result)
        self.assertIsInstance(result['icers'], list)
        self.assertIsInstance(result['cost_effectiveness'], list)
    
    def test_dcea_engine_basic(self):
        """Test basic functionality of DCEA engine."""
        # Implementation would go here
        pass
    
    def test_voi_engine_basic(self):
        """Test basic functionality of VOI engine."""
        # Implementation would go here
        pass


class PerformanceBenchmark:
    """
    Performance benchmarking for health economic models.
    """
    
    def __init__(self):
        self.benchmark_results = {}
        self.performance_thresholds = {
            'cea_analysis': 5.0,  # seconds
            'psa_analysis': 60.0,  # seconds 
            'voi_analysis': 300.0,  # seconds
            'model_initialization': 1.0  # seconds
        }
    
    def time_function(self, func: Callable, *args, warmup_runs: int = 3, test_runs: int = 10, **kwargs) -> Dict[str, Any]:
        """Time a function and return statistical results."""
        # Warmup runs
        for _ in range(warmup_runs):
            func(*args, **kwargs)
        
        # Actual timing runs
        times = []
        for _ in range(test_runs):
            start = time.time()
            func(*args, **kwargs)
            end = time.time()
            times.append(end - start)
        
        return {
            'mean_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'std_time': statistics.stdev(times) if len(times) > 1 else 0,
            'min_time': min(times),
            'max_time': max(times),
            'all_times': times,
            'runs': test_runs
        }
    
    def benchmark_cea_performance(self, num_strategies: int = 5) -> Dict[str, Any]:
        """Benchmark CEA engine performance with varying numbers of strategies."""
        from scripts.models.cea_engine import CEAEngine
        
        # Generate synthetic data
        strategies = [f"Strategy_{i}" for i in range(num_strategies)]
        costs = np.random.uniform(1000, 10000, num_strategies)
        effects = np.random.uniform(0.1, 1.0, num_strategies)
        
        params = {
            'strategies': strategies,
            'costs': costs.tolist(),
            'effects': effects.tolist(),
            'wtp_threshold': 50000
        }
        
        # Time the analysis
        cea = CEAEngine()
        timing_results = self.time_function(cea.analyze, params)
        
        # Check against threshold
        threshold = self.performance_thresholds.get('cea_analysis', 5.0)
        timing_results['within_threshold'] = timing_results['mean_time'] <= threshold
        timing_results['threshold'] = threshold
        
        return timing_results
    
    def benchmark_psa_performance(self, num_params: int = 50, num_simulations: int = 1000) -> Dict[str, Any]:
        """Benchmark PSA performance."""
        from scripts.models.psa_cea_model import run_probabilistic_sa
        
        # Create parameters for PSA
        base_params = {
            'costs': [5000, 7000, 6000],
            'effects': [0.5, 0.7, 0.6],
            'num_simulations': num_simulations
        }
        
        # Add PSA distributions for parameters
        psa_params = {
            'costs': [{'mean': c, 'sd': c*0.1, 'dist': 'gamma'} for c in base_params['costs']],
            'effects': [{'mean': e, 'sd': e*0.1, 'dist': 'beta'} for e in base_params['effects']]
        }
        
        params = {**base_params, 'psa_params': psa_params}
        
        timing_results = self.time_function(run_probabilistic_sa, params)
        
        threshold = self.performance_thresholds.get('psa_analysis', 60.0)
        timing_results['within_threshold'] = timing_results['mean_time'] <= threshold
        timing_results['threshold'] = threshold
        
        return timing_results
    
    def generate_benchmark_report(self) -> str:
        """Generate a comprehensive benchmark report."""
        report_parts = [
            "# Performance Benchmark Report",
            f"Generated at: {datetime.now().isoformat()}",
            "",
            "## Thresholds",
            ""
        ]
        
        for test_name, threshold in self.performance_thresholds.items():
            report_parts.append(f"- {test_name}: {threshold}s")
        
        report_parts.extend([
            "",
            "## Results",
            ""
        ])
        
        for test_name, result in self.benchmark_results.items():
            report_parts.extend([
                f"### {test_name}",
                f"- Mean time: {result['mean_time']:.4f}s",
                f"- Median time: {result['median_time']:.4f}s", 
                f"- Std dev: {result['std_time']:.4f}s",
                f"- Within threshold: {'YES' if result.get('within_threshold', False) else 'NO'}",
                ""
            ])
        
        return "\n".join(report_parts)


class QualityAssuranceFramework:
    """
    Comprehensive quality assurance framework for health economic models.
    """
    
    def __init__(self):
        self.qa_checks = []
        self.validation_results = {}
        self.compliance_status = {}
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def add_validation_check(self, name: str, check_function: Callable[[], bool], description: str = ""):
        """Add a validation check to the framework."""
        self.qa_checks.append({
            'name': name,
            'function': check_function,
            'description': description,
            'executed': False,
            'result': None,
            'timestamp': None
        })
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all registered validation checks."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks_executed': 0,
            'checks_passed': 0,
            'checks_failed': 0,
            'details': []
        }
        
        for check in self.qa_checks:
            try:
                start_time = time.time()
                result = check['function']()
                execution_time = time.time() - start_time
                
                check['result'] = result
                check['executed'] = True
                check['timestamp'] = datetime.now().isoformat()
                
                status = 'PASS' if result else 'FAIL'
                results['details'].append({
                    'name': check['name'],
                    'status': status,
                    'description': check['description'],
                    'execution_time': execution_time
                })
                
                if result:
                    results['checks_passed'] += 1
                else:
                    results['checks_failed'] += 1
                
                results['checks_executed'] += 1
                
                self.logger.info(f"Validation {check['name']}: {status}")
                
            except Exception as e:
                check['result'] = False
                check['executed'] = True
                check['timestamp'] = datetime.now().isoformat()
                
                results['details'].append({
                    'name': check['name'],
                    'status': 'ERROR',
                    'description': check['description'],
                    'error': str(e),
                    'execution_time': time.time() - start_time
                })
                results['checks_failed'] += 1
                results['checks_executed'] += 1
                
                self.logger.error(f"Validation {check['name']} ERROR: {str(e)}")
        
        return results
    
    def check_model_convergence(self, model_output: Dict[str, Any], tolerance: float = 1e-5) -> bool:
        """Check if model has converged properly."""
        # Check if ICERs are stable
        if 'icers' in model_output:
            icer_values = [icer for icer in model_output['icers'] if not (np.isnan(icer) or np.isinf(icer))]
            if len(icer_values) > 0:
                # Check if there are reasonable ICER values (not extremely large)
                return all(abs(icer) < 1e10 for icer in icer_values)
        
        # Check if probabilistic results have converged (if applicable)
        if 'probabilistic_results' in model_output:
            # Check if CEAC curves are smooth
            ceac_values = model_output.get('ceac_values', [])
            if len(ceac_values) > 1:
                # Check for extreme fluctuations
                diffs = np.diff(ceac_values)
                return np.max(np.abs(diffs)) < 0.5  # CEAC shouldn't jump more than 0.5 per WTP unit
        
        return True  # If no specific checks apply, assume OK
    
    def check_parameter_validity(self, parameters: Dict[str, Any]) -> bool:
        """Check if model parameters are within reasonable bounds."""
        required_keys = ['costs', 'effects']
        if not all(key in parameters for key in required_keys):
            return False
        
        # Check that costs are positive
        if 'costs' in parameters:
            costs = parameters['costs']
            if not all(c >= 0 for c in costs):
                self.logger.warning(f"Invalid costs found: {costs}")
                return False
        
        # Check that effects are positive
        if 'effects' in parameters:
            effects = parameters['effects']
            if not all(e >= 0 for e in effects):
                self.logger.warning(f"Invalid effects found: {effects}")
                return False
        
        return True
    
    def check_result_consistency(self, results1: Dict[str, Any], results2: Dict[str, Any], tolerance: float = 1e-6) -> bool:
        """Check if two result sets are consistent (e.g., for regression testing)."""
        # Compare key metrics between two result sets
        keys_to_compare = ['icers', 'cost_effectiveness_ratios', 'net_monetary_benefits']
        
        for key in keys_to_compare:
            if key in results1 and key in results2:
                val1, val2 = results1[key], results2[key]
                
                if isinstance(val1, list) and isinstance(val2, list):
                    if len(val1) != len(val2):
                        return False
                    if not all(abs(a - b) < tolerance for a, b in zip(val1, val2)):
                        return False
                elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    if abs(val1 - val2) > tolerance:
                        return False
                else:
                    if val1 != val2:
                        return False
        
        return True
    
    def run_regression_tests(self, base_results: Dict[str, Any], new_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run regression tests comparing new results to baseline."""
        consistency_check = self.check_result_consistency(base_results, new_results)
        
        return {
            'regression_test_passed': consistency_check,
            'comparing': {
                'baseline_timestamp': base_results.get('timestamp'),
                'new_timestamp': new_results.get('timestamp', datetime.now().isoformat())
            }
        }


class AutomatedTestRunner:
    """
    Automated test runner with configuration for different test suites.
    """
    
    def __init__(self, config_path: str = "tests/config/test_config.json"):
        self.config_path = config_path
        self.test_config = self.load_test_config()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def load_test_config(self) -> Dict[str, Any]:
        """Load test configuration from file."""
        default_config = {
            "test_suites": {
                "unit": {
                    "enabled": True,
                    "pattern": "test_*.py",
                    "directory": "tests/unit"
                },
                "integration": {
                    "enabled": True,
                    "pattern": "test_integration_*.py", 
                    "directory": "tests/integration"
                },
                "performance": {
                    "enabled": True,
                    "pattern": "test_performance_*.py",
                    "directory": "tests/performance"
                },
                "regression": {
                    "enabled": False,
                    "pattern": "test_regression_*.py",
                    "directory": "tests/regression"
                }
            },
            "coverage": {
                "enabled": True,
                "min_coverage": 80.0,
                "report_format": ["html", "xml", "term-missing"]
            },
            "performance_thresholds": {
                "cea_analysis_max_time": 10.0,
                "psa_analysis_max_time": 120.0,
                "model_initialization_max_time": 2.0
            }
        }
        
        config_path = Path(self.config_path)
        if config_path.exists():
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in default_config:
                    if isinstance(default_config[key], dict):
                        default_config[key].update(loaded_config.get(key, {}))
                    else:
                        default_config[key] = loaded_config.get(key, default_config[key])
            return default_config
        else:
            # Create default config file if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def run_tests(self, test_suite: str = "all") -> Dict[str, Any]:
        """Run tests for specified suite."""
        start_time = time.time()
        
        if test_suite == "all":
            suites_to_run = [suite_name for suite_name, config in self.test_config['test_suites'].items() 
                           if config['enabled']]
        elif test_suite in self.test_config['test_suites']:
            if self.test_config['test_suites'][test_suite]['enabled']:
                suites_to_run = [test_suite]
            else:
                raise ValueError(f"Test suite '{test_suite}' is not enabled in config")
        else:
            raise ValueError(f"Unknown test suite: {test_suite}")
        
        results = {
            'test_suite': test_suite,
            'suites_run': suites_to_run,
            'timestamp': datetime.now().isoformat(),
            'execution_time': 0,
            'test_results': {},
            'overall_success': True,
            'coverage_results': None
        }
        
        for suite in suites_to_run:
            suite_config = self.test_config['test_suites'][suite]
            suite_dir = Path(suite_config['directory'])
            
            if not suite_dir.exists():
                self.logger.warning(f"Test suite directory does not exist: {suite_dir}")
                continue
            
            # Build pytest command
            cmd_parts = ["python", "-m", "pytest", str(suite_dir)]
            
            # Add pattern if specified
            if 'pattern' in suite_config:
                cmd_parts.extend(["-k", suite_config['pattern']])
            
            # Add coverage if enabled
            if self.test_config['coverage']['enabled'] and suite == 'unit':
                cmd_parts.append("--cov=scripts")
                cmd_parts.append(f"--cov-report={' --cov-report='.join(self.test_config['coverage']['report_format'])}")
                cmd_parts.append(f"--cov-fail-under={self.test_config['coverage']['min_coverage']}")
            
            cmd_parts.extend(["-v", "--tb=short"])
            
            try:
                result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=300)
                
                suite_result = {
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': result.returncode == 0
                }
                
                results['test_results'][suite] = suite_result
                if not suite_result['success']:
                    results['overall_success'] = False
                    
            except subprocess.TimeoutExpired:
                suite_result = {
                    'return_code': -1,
                    'stdout': '',
                    'stderr': 'Test timed out after 300 seconds',
                    'success': False
                }
                results['test_results'][suite] = suite_result
                results['overall_success'] = False
        
        results['execution_time'] = time.time() - start_time
        return results
    
    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        benchmark_runner = PerformanceBenchmark()
        
        # Run specific benchmarks
        cea_benchmark = benchmark_runner.benchmark_cea_performance(num_strategies=3)
        psa_benchmark = benchmark_runner.benchmark_psa_performance(num_params=20, num_simulations=1000)
        
        # Check against thresholds
        thresholds = self.test_config['performance_thresholds']
        performance_results = {
            'cea_analysis': {
                'result': cea_benchmark,
                'pass': cea_benchmark['mean_time'] <= thresholds['cea_analysis_max_time'],
                'threshold': thresholds['cea_analysis_max_time']
            },
            'psa_analysis': {
                'result': psa_benchmark,
                'pass': psa_benchmark['mean_time'] <= thresholds['psa_analysis_max_time'],
                'threshold': thresholds['psa_analysis_max_time']
            }
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'performance_results': performance_results,
            'all_pass': all(res['pass'] for res in performance_results.values())
        }
    
    def generate_test_report(self, test_results: Dict[str, Any], perf_results: Dict[str, Any] = None) -> str:
        """Generate a comprehensive test report."""
        report_parts = [
            "# Test Report",
            f"Generated at: {test_results['timestamp']}",
            f"Execution time: {test_results['execution_time']:.2f}s",
            f"Overall Success: {'YES' if test_results['overall_success'] else 'NO'}",
            "",
            "## Test Suites Run",
        ]
        
        for suite, result in test_results['test_results'].items():
            status = "PASS" if result['success'] else "FAIL"
            report_parts.append(f"- {suite}: {status} (return code: {result['return_code']})")
        
        if perf_results:
            report_parts.extend([
                "",
                "## Performance Benchmarks",
            ])
            for test_name, result in perf_results['performance_results'].items():
                status = "PASS" if result['pass'] else "FAIL"
                report_parts.append(f"- {test_name}: {status} ({result['result']['mean_time']:.4f}s, threshold: {result['threshold']}s)")
        
        return "\n".join(report_parts)


# Context manager for measuring execution time
@contextmanager
def timer(description: str):
    """Context manager to time execution of code blocks."""
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        logger.info(f"{description} took {end_time - start_time:.4f} seconds")


# Example validation functions
def validate_cea_results(results: Dict[str, Any]) -> bool:
    """Validate CEA results structure and values."""
    required_keys = ['strategies', 'costs', 'effects', 'icers', 'cost_effectiveness']
    if not all(key in results for key in required_keys):
        logger.error("CEA results missing required keys")
        return False
    
    # Check that lengths match
    expected_len = len(results['strategies'])
    if not all(len(results[key]) == expected_len for key in ['costs', 'effects']):
        logger.error("CEA results have inconsistent lengths")
        return False
    
    # Check that values are valid numbers
    for key in ['costs', 'effects']:
        if not all(isinstance(val, (int, float)) and not (np.isnan(val) or np.isinf(val)) for val in results[key]):
            logger.error(f"Invalid values found in {key}")
            return False
    
    # Check ICER validity (should have n-1 values for n strategies)
    if len(results['icers']) != expected_len - 1:
        logger.error(f"Unexpected number of ICERs: expected {expected_len-1}, got {len(results['icers'])}")
        return False
    
    return True


def validate_psa_results(results: Dict[str, Any]) -> bool:
    """Validate PSA results structure and values."""
    # Implementation would check PSA results validity
    required_keys = ['strategy', 'cost', 'effect', 'nmb']
    if 'psa_df' in results:
        df = results['psa_df']
        return all(key in df.columns for key in required_keys)
    else:
        return 'probabilities' in results


# Example usage
def run_quality_assurance_pipeline():
    """
    Run the complete quality assurance pipeline.
    """
    print("Starting Quality Assurance Pipeline...")
    
    # Initialize QA framework
    qaf = QualityAssuranceFramework()
    
    # Add validation checks
    qaf.add_validation_check(
        "parameter_validity", 
        lambda: qaf.check_parameter_validity({'costs': [1000, 2000], 'effects': [0.5, 0.6]}),
        "Validate model parameters are reasonable"
    )
    
    # Run validations
    validation_results = qaf.run_all_validations()
    
    # Initialize test runner
    test_runner = AutomatedTestRunner()
    
    # Run tests
    test_results = test_runner.run_tests("unit")
    
    # Run performance benchmarks
    perf_results = test_runner.run_performance_benchmarks()
    
    # Generate reports
    test_report = test_runner.generate_test_report(test_results, perf_results)
    
    # Print summary
    print(f"Validations: {validation_results['checks_executed']} executed, "
          f"{validation_results['checks_passed']} passed, "
          f"{validation_results['checks_failed']} failed")
    
    print(f"Tests: {'PASSED' if test_results['overall_success'] else 'FAILED'}")
    print(f"Performance: {'PASSED' if perf_results['all_pass'] else 'FAILED'}")
    
    return {
        'validations': validation_results,
        'tests': test_results,
        'performance': perf_results,
        'report': test_report
    }


if __name__ == "__main__":
    # Run the QA pipeline
    results = run_quality_assurance_pipeline()
    
    # Optionally save results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("Quality assurance pipeline completed. Results saved to test_results.json")