import pandas as pd
import os

def load_utilities_from_trials(path, source_id='trials', region=None, ethnicity=None, payer=None):
    """Load utilities from trial/meta-analytic data."""
    df = pd.read_csv(path)
    # Assume df has 'state', 'utility', optionally 'lower_ci', 'upper_ci', 'region', 'ethnicity', 'payer', 'source_id'
    required_cols = ['state', 'utility']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must have columns: {required_cols}")
    
    # Filter by subgroups if provided
    if region and 'region' in df.columns:
        df = df[df['region'] == region]
    if ethnicity and 'ethnicity' in df.columns:
        df = df[df['ethnicity'] == ethnicity]
    if payer and 'payer' in df.columns:
        df = df[df['payer'] == payer]
    
    # Add missing columns
    if 'source_id' not in df.columns:
        df['source_id'] = source_id
    if 'region' not in df.columns:
        df['region'] = region if region else 'NEEDS_DATA'
    if 'ethnicity' not in df.columns:
        df['ethnicity'] = ethnicity if ethnicity else 'NEEDS_DATA'
    if 'payer' not in df.columns:
        df['payer'] = payer if payer else 'NEEDS_DATA'
    
    # Add Group column
    df['Group'] = df.apply(lambda row: f"{row['payer']}_{row['region']}_{row['ethnicity']}".replace('NEEDS_DATA', 'general'), axis=1)
    
    # Other columns
    df['state_value'] = df['utility']
    df['cognitive_disutility'] = 'NEEDS_DATA'
    df['subgroup'] = df['Group']  # or specific
    df['modifier_value'] = 1.0
    df['notes'] = 'NEEDS_DATA: Cognitive disutility and modifiers not available'
    
    return df

def apply_subgroup_modifiers(df, modifiers_path):
    """Apply subgroup modifiers (e.g., rural/urban, Māori/Indigenous)."""
    if os.path.exists(modifiers_path):
        _modifiers = pd.read_csv(modifiers_path)
        # TODO: Implement modifier application logic
        # For now, add placeholder modifiers
        df['subgroup'] = 'general'
        df['modifier_value'] = 1.0
        df['notes'] = 'NEEDS_DATA: Subgroup modifiers not applied'
    else:
        df['subgroup'] = 'NA'
        df['modifier_value'] = 1.0
        df['notes'] = 'NEEDS_DATA: Modifiers file not provided'
    return df

def write_utilities(df, output_path='data_schemas/utilities.csv'):
    """Write utilities to CSV with confidence bounds."""
    df.to_csv(output_path, index=False)