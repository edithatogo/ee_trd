#!/usr/bin/env python3
"""Check that seaborn is not used in analysis_core/ or analysis_v2/."""
import sys
from pathlib import Path

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

def main():
    """Check for seaborn usage in core analysis directories."""
    directories = ["analysis_core", "analysis_v2"]
    found_seaborn = False
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            continue
            
        for py_file in dir_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "seaborn" in content or "import seaborn" in content or "from seaborn" in content:
                    print(f"Found seaborn usage in {py_file}")
                    found_seaborn = True
            except Exception as e:
                print(f"Error reading {py_file}: {e}")
                found_seaborn = True
    
    if found_seaborn:
        print("ERROR: seaborn found in analysis_core/ or analysis_v2/")
        sys.exit(1)
    else:
        print("No seaborn usage found in analysis_core/ or analysis_v2/")
        sys.exit(0)

if __name__ == "__main__":
    main()
