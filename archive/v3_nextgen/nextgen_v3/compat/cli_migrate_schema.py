#!/usr/bin/env python3
"""
CLI tool to migrate v1/v2 CSV files to v3 schema.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple


def detect_schema_version(headers: List[str]) -> str:
    """Detect the schema version from CSV headers."""
    header_str = ' '.join(headers).lower()

    # V1 indicators
    if 'iter' in header_str and 'inc_cost' in header_str:
        return 'v1'

    # V2 indicators
    if 'total_cost' in header_str or 'arm' in header_str:
        return 'v2'

    # Default to v1 if unclear
    return 'v1'


def map_v1_psa_schema(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map v1 PSA results schema to v3 format."""
    v3_row = {}

    # Core columns (should exist in v1)
    v3_row['iteration'] = row.get('iter', row.get('iteration', row.get('draw', 0)))
    v3_row['strategy'] = row.get('strategy', 'unknown')
    v3_row['cost'] = float(row.get('cost', 0))
    v3_row['qalys'] = float(row.get('qalys', row.get('effect', 0)))
    v3_row['incremental_cost'] = float(row.get('inc_cost', 0))
    v3_row['incremental_qalys'] = float(row.get('inc_qalys', 0))
    v3_row['nmb'] = float(row.get('nmb', 0))

    # Add v3-specific columns
    v3_row['perspective'] = row.get('perspective', 'health_system')
    v3_row['jurisdiction'] = 'AU'  # Default, can be overridden
    v3_row['willingness_to_pay'] = 50000  # Default lambda
    v3_row['icer'] = (v3_row['incremental_cost'] / v3_row['incremental_qalys']
                     if v3_row['incremental_qalys'] != 0 else float('inf'))

    # Add metadata columns
    v3_row['source_version'] = 'v1'
    v3_row['schema_version'] = '3.0'

    return v3_row


def map_v2_pipeline_schema(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map v2 pipeline results schema to v3 format."""
    v3_row = {}

    # Map common columns
    v3_row['iteration'] = row.get('iteration', row.get('iter', 0))
    v3_row['strategy'] = row.get('strategy', row.get('arm', 'unknown'))
    v3_row['cost'] = float(row.get('total_cost', row.get('cost', 0)))
    v3_row['qalys'] = float(row.get('total_qalys', row.get('qalys', 0)))

    # Calculate incremental values if not present
    if 'incremental_cost' not in row and 'incremental_qalys' not in row:
        # Assume first strategy is baseline
        baseline_cost = 0  # Would need to be calculated from actual data
        baseline_qalys = 0
        v3_row['incremental_cost'] = v3_row['cost'] - baseline_cost
        v3_row['incremental_qalys'] = v3_row['qalys'] - baseline_qalys
    else:
        v3_row['incremental_cost'] = float(row.get('incremental_cost', 0))
        v3_row['incremental_qalys'] = float(row.get('incremental_qalys', 0))

    v3_row['nmb'] = float(row.get('nmb', 0))

    # Add v3-specific columns
    v3_row['perspective'] = row.get('perspective', 'health_system')
    v3_row['jurisdiction'] = row.get('jurisdiction', row.get('country', 'AU'))
    v3_row['willingness_to_pay'] = int(row.get('lambda', 50000))

    # Calculate ICER
    if v3_row['incremental_qalys'] != 0:
        v3_row['icer'] = v3_row['incremental_cost'] / v3_row['incremental_qalys']
    else:
        v3_row['icer'] = float('inf')

    # Add metadata
    v3_row['source_version'] = 'v2'
    v3_row['schema_version'] = '3.0'

    return v3_row


def map_csv_row(row: Dict[str, Any], schema_version: str) -> Dict[str, Any]:
    """Map a CSV row based on detected schema version."""
    if schema_version == 'v1':
        return map_v1_psa_schema(row)
    elif schema_version == 'v2':
        return map_v2_pipeline_schema(row)
    else:
        # Default mapping
        return map_v1_psa_schema(row)


def migrate_csv_file(input_path: Path, output_path: Path) -> Tuple[int, List[str], str]:
    """Migrate a CSV file from v1/v2 schema to v3 schema."""
    rows_migrated = 0
    v3_headers = []
    schema_version = 'unknown'

    try:
        # Read input CSV
        with open(input_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            input_rows = list(reader)

        if not input_rows:
            return 0, [], 'unknown'

        # Detect schema version from headers
        schema_version = detect_schema_version(list(input_rows[0].keys()))
        print(f"Detected schema version: {schema_version}")

        # Map all rows
        v3_rows = []
        for row in input_rows:
            v3_row = map_csv_row(row, schema_version)
            v3_rows.append(v3_row)
            rows_migrated += 1

        # Get v3 headers from first mapped row
        if v3_rows:
            v3_headers = list(v3_rows[0].keys())

        # Write output CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=v3_headers)
            writer.writeheader()
            writer.writerows(v3_rows)

    except Exception as e:
        print(f"Warning: Failed to migrate {input_path}: {e}")
        return 0, [], schema_version

    return rows_migrated, v3_headers, schema_version


def main():
    parser = argparse.ArgumentParser(
        description="Convert v1/v2 CSV files to v3 schema"
    )
    parser.add_argument(
        'input_csv',
        help='Path to v1/v2 CSV file to convert'
    )
    parser.add_argument(
        '--out',
        help='Output CSV path (default: <input>_to_v3.csv)'
    )

    args = parser.parse_args()

    # Determine output path
    input_path = Path(args.input_csv)
    if args.out:
        output_path = Path(args.out)
    else:
        output_path = input_path.parent / f"{input_path.stem}_to_v3.csv"

    try:
        print(f"Converting {input_path} to v3 schema...")

        # Migrate the CSV
        rows_migrated, v3_headers, schema_version = migrate_csv_file(input_path, output_path)

        if rows_migrated > 0:
            print(f"✅ Migrated {rows_migrated} rows from {schema_version} to v3 schema")
            print(f"📄 Output written to {output_path}")
            print("📋 Migration steps:")
            print(f"  1. Detected schema version: {schema_version}")
            print("  2. Mapped columns to v3 naming convention")
            print("  3. Added v3-specific columns (perspective, jurisdiction, WTP, ICER)")
            print("  4. Added metadata columns (source_version, schema_version)")
            print(f"  5. Generated {len(v3_headers)} v3 columns: {', '.join(v3_headers[:5])}{'...' if len(v3_headers) > 5 else ''}")
        else:
            print("❌ No rows were migrated")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during schema migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()