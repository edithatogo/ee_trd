import pandas as pd
from types import SimpleNamespace
import yaml

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_clinical_induction(path):
    return pd.read_csv(path, dtype={'arm': str, 'parameter': str, 'value': float, 'source_id': str})

def load_durability_relapse(path):
    return pd.read_csv(path, dtype={'arm': str, 'time': int, 'relapse_rate': float, 'source_id': str})

def load_cognition_ae_seizure(path):
    return pd.read_csv(path, dtype={'arm': str, 'adverse_event': str, 'rate': float, 'source_id': str})

def load_sessions(path):
    return pd.read_csv(path, dtype={'arm': str, 'sessions_required': int, 'source_id': str})

def load_operations_per_session(path):
    return pd.read_csv(path, dtype={'arm': str, 'operations_per_session': int, 'source_id': str})

def load_cost_inputs_au(path):
    return pd.read_csv(path, dtype={'item': str, 'cost_aud': float, 'source_id': str})

def load_cost_inputs_nz(path):
    return pd.read_csv(path, dtype={'item': str, 'cost_nzd': float, 'source_id': str})

def load_utilities(path):
    return pd.read_csv(path, dtype={'state': str, 'utility': float, 'source_id': str})

def load_parameters_psa(path):
    return pd.read_csv(path, dtype={'parameter': str, 'distribution': str, 'mean': float, 'std': float, 'source_id': str})

def load_mcda_weights(path):
    return pd.read_csv(path, dtype={'criterion': str, 'weight': float, 'source_id': str})

def load_mcda_value_functions(path):
    return pd.read_csv(path, dtype={'criterion': str, 'value_function': str, 'source_id': str})

def load_dcea_groups(path):
    return pd.read_csv(path, dtype={'group': str, 'criteria': str, 'source_id': str})

def load_dcea_weights(path):
    return pd.read_csv(path, dtype={'group': str, 'weight': float, 'source_id': str})

def load_provenance_sources(path):
    return pd.read_csv(path, dtype={'source_id': str, 'citation': str})

def load_grade_certainty(path):
    return pd.read_csv(path, dtype={'Criterion': str, 'Certainty': str})

def load_opportunity_cost_shares(path):
    return pd.read_csv(path, dtype={'jurisdiction': str, 'group': str, 'share': float})

def load_ecea_oop_inputs(path):
    return pd.read_csv(path, dtype={'Arm': str, 'Jurisdiction': str, 'Group': str, 'Mean_OoP_per_patient': float, 'OoP_SD': float, 'PrivateShare': float, 'Travel_OoP_per_patient': float})

def load_income_quintiles(path):
    return pd.read_csv(path, dtype={'Jurisdiction': str, 'Group': str, 'Quintile': int, 'Mean_Income': float, 'HH_Size': float, 'Catastrophic_Threshold': float})

def load_evsi_config(path):
    return load_config(path)

def load_all_inputs(config_path):
    config = load_config(config_path)
    inputs = SimpleNamespace()
    inputs.clinical_induction = load_clinical_induction(config['data_schemas']['clinical_induction'])
    inputs.durability_relapse = load_durability_relapse(config['data_schemas']['durability_relapse'])
    inputs.cognition_ae_seizure = load_cognition_ae_seizure(config['data_schemas']['cognition_ae_seizure'])
    inputs.sessions = load_sessions(config['data_schemas']['sessions'])
    inputs.operations_per_session = load_operations_per_session(config['data_schemas']['operations_per_session'])
    inputs.cost_inputs_au = load_cost_inputs_au(config['data_schemas']['cost_inputs_au'])
    inputs.cost_inputs_nz = load_cost_inputs_nz(config['data_schemas']['cost_inputs_nz'])
    inputs.utilities = load_utilities(config['data_schemas']['utilities'])
    inputs.parameters_psa = load_parameters_psa(config['data_schemas']['parameters_psa'])
    inputs.mcda_weights = load_mcda_weights(config['data_schemas']['mcda_weights'])
    inputs.mcda_value_functions = load_mcda_value_functions(config['data_schemas']['mcda_value_functions'])
    inputs.dcea_groups = load_dcea_groups(config['data_schemas']['dcea_groups'])
    inputs.dcea_weights = load_dcea_weights(config['data_schemas']['dcea_weights'])
    inputs.provenance_sources = load_provenance_sources(config['data_schemas']['provenance_sources'])
    inputs.grade_certainty = load_grade_certainty(config['data_schemas']['grade_certainty'])
    if 'opportunity_cost_shares' in config['data_schemas']:
        inputs.opportunity_cost_shares = load_opportunity_cost_shares(config['data_schemas']['opportunity_cost_shares'])
    inputs.ecea_oop_inputs = load_ecea_oop_inputs(config['data_schemas']['ecea_oop_inputs'])
    inputs.income_quintiles = load_income_quintiles(config['data_schemas']['income_quintiles'])
    inputs.evsi_config = load_evsi_config('nextgen_v3/config/evsi.yaml')
    return inputs