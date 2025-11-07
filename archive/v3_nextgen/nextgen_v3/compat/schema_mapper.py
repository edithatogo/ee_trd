#!/usr/bin/env python3
"""
Schema mapper for v1/v2 compatibility.
Maps legacy CSV schemas to v3 format with column additions/modifications.
"""

import csv
from pathlib import Path
from typing import Dict, List, Any, Tuple

def map_v1_psa_schema(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map v1 PSA results schema to v3 format."""
    v3_row = {}

    # Core columns (should exist in v1)
    v3_row['iteration'] = row.get('iter', row.get('iteration', 0))
    v3_row['strategy'] = row.get('strategy', 'unknown')
    v3_row['cost'] = float(row.get('cost', 0))
    v3_row['qalys'] = float(row.get('qalys', 0))
    v3_row['incremental_cost'] = float(row.get('inc_cost', 0))
    v3_row['incremental_qalys'] = float(row.get('inc_qalys', 0))
    v3_row['nmb'] = float(row.get('nmb', 0))

    # Add v3-specific columns
    v3_row['perspective'] = 'health_system'  # Default, can be overridden
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

def map_csv_row(row: Dict[str, Any], schema_version: str) -> Dict[str, Any]:
    """Map a CSV row based on detected schema version."""
    if schema_version == 'v1':
        return map_v1_psa_schema(row)
    elif schema_version == 'v2':
        return map_v2_pipeline_schema(row)
    else:
        # Default mapping
        return map_v1_psa_schema(row)

def migrate_csv_file(input_path: Path, output_path: Path) -> Tuple[int, List[str]]:
    """Migrate a CSV file from v1/v2 schema to v3 schema."""
    rows_migrated = 0
    v3_headers = []

    try:
        # Read input CSV
        with open(input_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            input_rows = list(reader)

        if not input_rows:
            return 0, []

        # Detect schema version from headers
        schema_version = detect_schema_version(list(input_rows[0].keys()))

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
        return 0, []

    return rows_migrated, v3_headers

def create_v3_schema_template() -> Dict[str, Any]:
    """Create a template for v3 schema definition."""
    return {
        'version': '3.0',
        'columns': {
            'iteration': {'type': 'integer', 'description': 'PSA iteration number'},
            'strategy': {'type': 'string', 'description': 'Treatment strategy name'},
            'cost': {'type': 'float', 'description': 'Total costs'},
            'qalys': {'type': 'float', 'description': 'Quality-adjusted life years'},
            'incremental_cost': {'type': 'float', 'description': 'Incremental costs vs baseline'},
            'incremental_qalys': {'type': 'float', 'description': 'Incremental QALYs vs baseline'},
            'nmb': {'type': 'float', 'description': 'Net monetary benefit'},
            'icer': {'type': 'float', 'description': 'Incremental cost-effectiveness ratio'},
            'perspective': {'type': 'string', 'description': 'Analysis perspective'},
            'jurisdiction': {'type': 'string', 'description': 'Country/region'},
            'willingness_to_pay': {'type': 'integer', 'description': 'WTP threshold'},
            'source_version': {'type': 'string', 'description': 'Original schema version'},
            'schema_version': {'type': 'string', 'description': 'Target schema version'}
        },
        'required_columns': ['iteration', 'strategy', 'cost', 'qalys'],
        'optional_columns': ['incremental_cost', 'incremental_qalys', 'nmb', 'icer',
                           'perspective', 'jurisdiction', 'willingness_to_pay',
                           'source_version', 'schema_version']
    }

def demo() -> Dict[str, Any]:
    """Demo function showing example schema mappings."""
    examples = {}

    # Example v1 PSA row
    v1_psa_row = {
        'iter': 1,
        'strategy': 'ECT',
        'cost': 15000.50,
        'qalys': 0.85,
        'inc_cost': 5000.25,
        'inc_qalys': 0.15,
        'nmb': 2500.00
    }

    examples['v1_psa_mapped'] = map_v1_psa_schema(v1_psa_row)

    # Example v2 pipeline row
    v2_pipeline_row = {
        'iteration': 1,
        'arm': 'Ketamine (IV)',
        'total_cost': 25000.75,
        'total_qalys': 0.92,
        'perspective': 'societal',
        'country': 'NZ',
        'lambda': 45000
    }

    examples['v2_pipeline_mapped'] = map_v2_pipeline_schema(v2_pipeline_row)

    # Schema template
    examples['v3_schema_template'] = create_v3_schema_template()

    return examples

if __name__ == "__main__":
    # Demo when run directly
    examples = demo()
    print("Schema Mapper Examples:")
    for name, result in examples.items():
        print(f"\n{name}:")
        if isinstance(result, dict):
            if 'columns' in result:
                print("  Schema with columns:", list(result['columns'].keys()))
            else:
                # Print as key-value pairs
                for key, value in result.items():
                    print(f"  {key}: {value}")
        else:
            print(f"  {result}")