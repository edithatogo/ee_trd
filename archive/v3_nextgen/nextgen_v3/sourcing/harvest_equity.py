import pandas as pd

def build_dcea_groups(jurisdictions=['AU', 'NZ'], region=None, ethnicity=None, payer=None):
    """Build dcea_groups.csv with Group, Jurisdiction, PopShare, PriorityFlag."""
    groups = []
    # Define possible subgroups
    regions = [region] if region else ['metro', 'rural']
    ethnicities = [ethnicity] if ethnicity else ['Māori', 'Aboriginal & Torres Strait Islander', 'Pacific', 'Other']
    payers = [payer] if payer else ['public', 'private']
    
    for jur in jurisdictions:
        for r in regions:
            for e in ethnicities:
                for p in payers:
                    group_name = f"{jur}_{p}_{r}_{e}".replace(' ', '_')
                    # Stub pop_share, etc.
                    pop_share = 0.1  # stub, should sum to 1
                    priority_flag = 1 if e in ['Māori', 'Aboriginal & Torres Strait Islander'] else 0
                    atkinson_epsilon = 1 if priority_flag else 0
                    groups.append({
                        'Group': group_name,
                        'jurisdiction': jur,
                        'pop_share': pop_share,
                        'priority_flag': priority_flag,
                        'atkinson_epsilon': atkinson_epsilon,
                        'source_id': 'equity_data',
                        'notes': 'NEEDS_DATA: Actual subgroup populations and priorities'
                    })
    df = pd.DataFrame(groups)
    return df

def build_dcea_weights(epsilon_grid=[0, 0.5, 1, 2]):
    """Build dcea_weights.csv with Atkinson ε grid and explicit weights."""
    weights = []
    for eps in epsilon_grid:
        weights.append({'group': 'atkinson', 'weight': eps, 'source_id': 'atkinson', 'notes': 'Atkinson epsilon defaults'})
    # Add explicit subgroup weights
    weights.extend([
        {'group': 'AU_general', 'weight': 1.0, 'source_id': 'explicit', 'notes': 'NEEDS_DATA: Explicit weights for subgroups'},
        {'group': 'AU_priority', 'weight': 1.5, 'source_id': 'explicit', 'notes': 'NEEDS_DATA: Explicit weights for subgroups'},
        {'group': 'NZ_general', 'weight': 1.0, 'source_id': 'explicit', 'notes': 'NEEDS_DATA: Explicit weights for subgroups'},
        {'group': 'NZ_priority', 'weight': 1.5, 'source_id': 'explicit', 'notes': 'NEEDS_DATA: Explicit weights for subgroups'}
    ])
    df = pd.DataFrame(weights)
    return df

def write_dcea_groups(df, output_path='data_schemas/dcea_groups.csv'):
    df.to_csv(output_path, index=False)

def write_dcea_weights(df, output_path='data_schemas/dcea_weights.csv'):
    df.to_csv(output_path, index=False)

# Optional opportunity_cost_shares.csv - not in data_schemas, so skip or add if needed