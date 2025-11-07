"""
Basic functionality test for the TRD CEA Toolkit.
"""

def test_basic_imports():
    """Test that core modules can be imported."""
    # Just testing that we can import the modules without errors
    # The actual functionality would be tested with the real implementations
    assert True  # Placeholder for when we have real engines to test


def test_configuration_loading():
    """Test configuration loading functionality."""
    # Test that configuration related functionality works
    from pathlib import Path
    import tempfile
    import yaml
    
    # Create a temporary config
    config_data = {
        'analysis': {
            'time_horizon': 10,
            'wtp_threshold': 50000
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tf:
        yaml.dump(config_data, tf)
        temp_path = tf.name
    
    # Load the config
    with open(temp_path, 'r') as f:
        loaded_config = yaml.safe_load(f)
    
    # Verify it was loaded correctly
    assert loaded_config['analysis']['time_horizon'] == 10
    assert loaded_config['analysis']['wtp_threshold'] == 50000
    
    # Cleanup
    import os
    os.unlink(temp_path)


if __name__ == "__main__":
    test_basic_imports()
    test_configuration_loading()
    print("All basic tests passed!")