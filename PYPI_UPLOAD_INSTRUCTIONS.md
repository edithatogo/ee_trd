# TRD CEA Toolkit - PyPI Upload Instructions

This document outlines the steps for uploading the TRD CEA Toolkit to TestPyPI and eventually to PyPI.

## Preparing for PyPI Upload

### 1. Verify Package Contents
Before uploading, ensure that the package contains all necessary files:

```bash
# Check the contents of the wheel file
unzip -l dist/trd_cea_toolkit-0.1.0-py3-none-any.whl
```

### 2. Test Installation Locally
Always test the installation locally before uploading to PyPI:

```bash
# Install in a virtual environment for testing
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
pip install dist/trd_cea_toolkit-0.1.0-py3-none-any.whl
# Test importing the main modules
python -c "from trd_cea.core.utils import calculate_icer; print('Import successful')"
deactivate
```

## Uploading to TestPyPI

### 1. Install twine if not already installed
```bash
pip install twine
```

### 2. Upload to TestPyPI
```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/trd_cea_toolkit-0.1.0-py3-none-any.whl
```

You'll need your TestPyPI credentials. If you don't have an account, create one at https://test.pypi.org/account/register/

### 3. Test Installation from TestPyPI
```bash
pip install --index-url https://test.pypi.org/simple/ trd-cea-toolkit==0.1.0
```

## Uploading to PyPI

Once the package is verified on TestPyPI, you can upload to the real PyPI:

```bash
# Upload to PyPI (use with caution!)
twine upload dist/trd_cea_toolkit-0.1.0-py3-none-any.whl
```

## Verification Checklist

Before uploading, verify:

- [ ] Version number is correct in pyproject.toml and setup.py
- [ ] All necessary files are included in the package
- [ ] License information is correct and compatible
- [ ] README is properly formatted
- [ ] Installation works in a fresh environment
- [ ] Basic functionality tests pass after installation
- [ ] CITATION.cff file is included for proper citation

## Additional Notes

- Once uploaded to PyPI, the version cannot be changed or replaced
- If you need to make changes, you must bump the version number and upload again
- TestPyPI is cleared periodically, so use it only for testing
- It's important to test installation and basic functionality before the official upload to PyPI