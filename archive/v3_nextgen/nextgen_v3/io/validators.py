import yaml

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_columns(df, required_columns):
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

def validate_arms(df, config_arms):
    if 'arm' in df.columns:
        invalid = set(df['arm']) - set(config_arms)
        if invalid:
            raise ValueError(f"Invalid arms: {invalid}")

def validate_ranges(df):
    if 'relapse_rate' in df.columns:
        if not df['relapse_rate'].between(0, 1).all():
            raise ValueError("relapse_rate not in [0,1]")
    if 'rate' in df.columns:
        if not df['rate'].between(0, 1).all():
            raise ValueError("rate not in [0,1]")
    if 'cost_aud' in df.columns:
        if (df['cost_aud'] < 0).any():
            raise ValueError("cost_aud < 0")
    if 'cost_nzd' in df.columns:
        if (df['cost_nzd'] < 0).any():
            raise ValueError("cost_nzd < 0")
    if 'utility' in df.columns:
        if not df['utility'].between(0, 1).all():
            raise ValueError("utility not in [0,1]")
    if 'weight' in df.columns:
        if not df['weight'].between(0, 1).all():
            raise ValueError("weight not in [0,1]")
    if 'sessions_required' in df.columns:
        if (df['sessions_required'] < 0).any():
            raise ValueError("sessions_required < 0")
    if 'operations_per_session' in df.columns:
        if (df['operations_per_session'] < 0).any():
            raise ValueError("operations_per_session < 0")

def validate_provenance(df, provenance_df):
    if 'source_id' in df.columns:
        invalid = set(df['source_id']) - set(provenance_df['source_id'])
        if invalid:
            raise ValueError(f"Invalid source_ids: {invalid}")

def validate_clinical_induction(df, config, provenance_df):
    required = ['arm', 'parameter', 'value', 'source_id']
    validate_columns(df, required)
    validate_arms(df, config['arms'])
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_durability_relapse(df, config, provenance_df):
    required = ['arm', 'time', 'relapse_rate', 'source_id']
    validate_columns(df, required)
    validate_arms(df, config['arms'])
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_cognition_ae_seizure(df, config, provenance_df):
    required = ['arm', 'adverse_event', 'rate', 'source_id']
    validate_columns(df, required)
    validate_arms(df, config['arms'])
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_sessions(df, config, provenance_df):
    required = ['arm', 'sessions_required', 'source_id']
    validate_columns(df, required)
    validate_arms(df, config['arms'])
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_operations_per_session(df, config, provenance_df):
    required = ['arm', 'operations_per_session', 'source_id']
    validate_columns(df, required)
    validate_arms(df, config['arms'])
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_cost_inputs_au(df, config, provenance_df):
    required = ['item', 'cost_aud', 'source_id']
    validate_columns(df, required)
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_cost_inputs_nz(df, config, provenance_df):
    required = ['item', 'cost_nzd', 'source_id']
    validate_columns(df, required)
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_utilities(df, config, provenance_df):
    required = ['state', 'utility', 'source_id']
    validate_columns(df, required)
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_parameters_psa(df, config, provenance_df):
    required = ['parameter', 'distribution', 'mean', 'std', 'source_id']
    validate_columns(df, required)
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_mcda_weights(df, config, provenance_df):
    required = ['criterion', 'weight', 'source_id']
    validate_columns(df, required)
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_mcda_value_functions(df, config, provenance_df):
    required = ['criterion', 'value_function', 'source_id']
    validate_columns(df, required)
    validate_provenance(df, provenance_df)

def validate_dcea_groups(df, config, provenance_df):
    required = ['group', 'criteria', 'source_id']
    validate_columns(df, required)
    validate_provenance(df, provenance_df)

def validate_dcea_weights(df, config, provenance_df):
    required = ['group', 'weight', 'source_id']
    validate_columns(df, required)
    validate_ranges(df)
    validate_provenance(df, provenance_df)

def validate_provenance_sources(df, config, provenance_df):
    required = ['source_id', 'citation']
    validate_columns(df, required)

def validate_all_inputs(inputs, config_path):
    config = load_config(config_path)
    provenance_df = inputs.provenance_sources
    validate_clinical_induction(inputs.clinical_induction, config, provenance_df)
    validate_durability_relapse(inputs.durability_relapse, config, provenance_df)
    validate_cognition_ae_seizure(inputs.cognition_ae_seizure, config, provenance_df)
    validate_sessions(inputs.sessions, config, provenance_df)
    validate_operations_per_session(inputs.operations_per_session, config, provenance_df)
    validate_cost_inputs_au(inputs.cost_inputs_au, config, provenance_df)
    validate_cost_inputs_nz(inputs.cost_inputs_nz, config, provenance_df)
    validate_utilities(inputs.utilities, config, provenance_df)
    validate_parameters_psa(inputs.parameters_psa, config, provenance_df)
    validate_mcda_weights(inputs.mcda_weights, config, provenance_df)
    validate_mcda_value_functions(inputs.mcda_value_functions, config, provenance_df)
    validate_dcea_groups(inputs.dcea_groups, config, provenance_df)
    validate_dcea_weights(inputs.dcea_weights, config, provenance_df)
    validate_provenance_sources(inputs.provenance_sources, config, provenance_df)