"""
Build an enhanced subgroup_comparison_enhanced.csv by merging available subgroup files
(found under an outputs directory). This script is idempotent and safe to call from
`generate_all_v4_figures.py`.

It will look for common subgroup files like:
- subgroup_comparison.csv
- subgroup_age.csv
- subgroup_severity.csv
- subgroup_combined.csv

and merge them into a deduplicated combined CSV with columns: strategy, subgroup, effect, cost, icer

Usage:
    python scripts/build_enhanced_subgroup.py /path/to/outputs_dir /path/to/out_dir

If run without args it will attempt to find outputs_v4/run_latest under the project root.
"""
from pathlib import Path
import sys
import pandas as pd


def find_subgroup_files(outputs_dir: Path):
    candidates = []
    names = [
        'subgroup_comparison_enhanced.csv',
        'subgroup_comparison.csv',
        'subgroup_combined.csv',
        'subgroup_age.csv',
        'subgroup_severity.csv'
    ]
    for p in outputs_dir.rglob('*.csv'):
        if p.name in names:
            candidates.append(p)
    return sorted(set(candidates))


def build_enhanced(outputs_dir: Path, out_path: Path):
    files = find_subgroup_files(outputs_dir)
    if not files:
        print('No subgroup CSVs found under', outputs_dir)
        return None

    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            # Only keep expected columns
            expected = ['strategy', 'subgroup', 'effect', 'cost', 'icer']
            present = [c for c in expected if c in df.columns]
            if not present:
                continue
            dfs.append(df[[c for c in present]])
        except Exception as e:
            print('Skipping', f, 'due to error:', e)

    if not dfs:
        print('No readable subgroup dataframes found')
        return None

    combined = pd.concat(dfs, ignore_index=True, sort=False)
    # Standardize columns, fill missing with NaN
    for c in ['strategy', 'subgroup', 'effect', 'cost', 'icer']:
        if c not in combined.columns:
            combined[c] = pd.NA

    # Drop exact duplicate rows
    combined = combined.drop_duplicates()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False)
    print('Wrote enhanced subgroup file to', out_path)
    return out_path


if __name__ == '__main__':
    project_root = Path(__file__).resolve().parents[1]
    if len(sys.argv) >= 3:
        outputs_dir = Path(sys.argv[1])
        out_path = Path(sys.argv[2])
    else:
        outputs_dir = project_root / 'outputs_v4' / 'run_latest'
        out_path = project_root / 'outputs_v4' / 'run_latest' / 'subgroup_comparison_enhanced.csv'

    build_enhanced(outputs_dir, out_path)
