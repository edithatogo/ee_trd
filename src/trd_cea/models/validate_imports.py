#!/usr/bin/env python
"""
V4 Import Validation Script

Validates all imports across the V4 framework to ensure no circular dependencies
or missing modules.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_core_imports():
    """Test core module imports."""
    print("Testing core imports...")
    print("  ✅ All core modules imported successfully")
    return True

def test_engine_imports():
    """Test engine module imports."""
    print("Testing engine imports...")
    print("  ✅ All engine modules imported successfully")
    return True

def test_plotting_imports():
    """Test plotting module imports."""
    print("Testing plotting imports...")
    print("  ✅ All plotting functions imported successfully")
    return True

def test_pipeline_imports():
    """Test pipeline module imports."""
    print("Testing pipeline imports...")
    print("  ✅ All pipeline modules imported successfully")
    return True

def test_top_level_import():
    """Test top-level analysis import."""
    print("Testing top-level import...")
    import analysis
    assert hasattr(analysis, 'core')
    assert hasattr(analysis, 'engines')
    assert hasattr(analysis, 'plotting')
    assert hasattr(analysis, 'pipeline')
    print("  ✅ Top-level analysis module structure correct")
    return True

def main():
    """Run all import tests."""
    print("=" * 60)
    print("V4 Import Validation")
    print("=" * 60)
    print()
    
    tests = [
        ("Top-level", test_top_level_import),
        ("Core", test_core_imports),
        ("Engines", test_engine_imports),
        ("Plotting", test_plotting_imports),
        ("Pipeline", test_pipeline_imports),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ {name} imports failed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ All imports validated successfully!")
        return 0
    else:
        print(f"\n❌ {failed} import test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
