"""
Pytest configuration for TRD CEA Toolkit

This file contains configuration and fixtures for the test suite.
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys
import pandas as pd
import numpy as np


# Add the main scripts directory to Python path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))


@pytest.fixture(scope="session")
def temp_test_dir():
    """Create a temporary directory for the test session."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup will happen after test session completes


@pytest.fixture
def sample_cost_data():
    """Provide sample cost data for testing."""
    return pd.DataFrame({
        'strategy': ['ECT', 'IV-KA', 'PO-KA'],
        'cost': [10000, 8000, 6000],
        'cost_lower': [9000, 7000, 5000],
        'cost_upper': [11000, 9000, 7000]
    })


@pytest.fixture
def sample_effect_data():
    """Provide sample effectiveness data for testing."""
    return pd.DataFrame({
        'strategy': ['ECT', 'IV-KA', 'PO-KA'],
        'effect': [0.60, 0.75, 0.68],
        'effect_lower': [0.55, 0.70, 0.63],
        'effect_upper': [0.65, 0.80, 0.73]
    })


@pytest.fixture
def sample_analysis_parameters():
    """Provide sample parameters for analysis engines."""
    return {
        'strategies': ['ECT', 'IV-KA', 'PO-KA'],
        'costs': [10000, 8000, 6000],
        'effects': [0.60, 0.75, 0.68],
        'wtp_threshold': 50000,
        'time_horizon': 10,
        'discount_rate_costs': 0.035,
        'discount_rate_effects': 0.035
    }


@pytest.fixture
def mock_psa_data(sample_analysis_parameters):
    """Provide mock PSA data for testing."""
    n_simulations = 100
    strategies = sample_analysis_parameters['strategies']
    
    # Generate correlated PSA samples
    rng = np.random.RandomState(42)
    
    psa_data = []
    for i in range(n_simulations):
        for idx, strategy in enumerate(strategies):
            # Add some correlation between costs and effects
            cost_noise = rng.normal(0, 0.1 * sample_analysis_parameters['costs'][idx])
            effect_noise = rng.normal(0, 0.05 * sample_analysis_parameters['effects'][idx])
            
            # Ensure positive values
            cost = max(100, sample_analysis_parameters['costs'][idx] + cost_noise)
            effect = max(0.01, sample_analysis_parameters['effects'][idx] + effect_noise)
            
            psa_data.append({
                'simulation': i,
                'strategy': strategy,
                'cost': cost,
                'effect': effect
            })
    
    return pd.DataFrame(psa_data)


@pytest.fixture
def test_config():
    """Provide a test configuration."""
    return {
        'analysis': {
            'time_horizon': 10,
            'discount_rate_costs': 0.035,
            'discount_rate_effects': 0.035,
            'wtp_threshold': 50000,
            'perspective': 'healthcare'
        },
        'strategies': {
            'ECT': {'name': 'Electroconvulsive Therapy', 'abbreviation': 'ECT'},
            'IV-KA': {'name': 'Intravenous Ketamine', 'abbreviation': 'IV-KA'},
            'PO-KA': {'name': 'Oral Ketamine', 'abbreviation': 'PO-KA'}
        }
    }


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "voi: marks tests as value of information tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


def pytest_addoption(parser):
    """Add command-line options to pytest."""
    parser.addoption(
        "--runslow", 
        action="store_true", 
        default=False,
        help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    """Skip slow tests unless --runslow option is passed."""
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return

    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)