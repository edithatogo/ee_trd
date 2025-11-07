import numpy as np
import pandas as pd
from types import SimpleNamespace
import itertools
import os
import yaml

# States - Semi-Markov with tunnels for time-since-response
STATES = [
    'Depressed',  # Non-response state
    'PartialResponse',  # Response but not remission
    'Remission_0_3m',  # Remission tunnel: 0-3 months
    'Remission_4_6m',  # 4-6 months
    'Remission_7_12m',  # 7-12 months
    'Remission_12m_plus',  # >12 months
    'Relapse',  # Relapsed from remission
    'Post_AE',  # Post-adverse event
    'Death'  # Absorbing
]
STATE_INDEX = {s: i for i, s in enumerate(STATES)}

def apply_cognition_mapping(measures, mapping_cfg):
    """Apply cognitive measures to utility deltas using mapping config."""
    disutilities = {}
    if not mapping_cfg or 'mappings' not in mapping_cfg:
        # Fallback to flat disutilities
        flat = mapping_cfg.get('flat_disutilities', {}) if mapping_cfg else {}
        for arm in ['ECT', 'Ketamine']:
            for phase in ['acute', 'maintenance']:
                key = f"{arm}_{phase}"
                disutilities[key] = flat.get(key, 0.0)  # default to 0.0
        return disutilities
    
    # Apply mappings
    for mapping_name, cfg in mapping_cfg['mappings'].items():
        measure_name = cfg['measure']
        if measure_name in measures:
            measure_delta = measures[measure_name]
            if cfg['type'] == 'linear':
                delta_utility = cfg['intercept'] + cfg['slope'] * measure_delta
            else:
                # Stub for spline, assume linear for now
                delta_utility = cfg['intercept'] + cfg['slope'] * measure_delta
            disutilities[mapping_name] = delta_utility
        else:
            # Fallback
            disutilities[mapping_name] = mapping_cfg.get('flat_disutilities', {}).get(mapping_name, 0.0)
    
    return disutilities

def get_transition_matrix(arm, inputs, cycle, time_in_remission=None):
    """Build transition matrix for the arm at given cycle with semi-Markov tunnels."""
    n = len(STATES)
    P = np.zeros((n, n))

    # Get clinical parameters for this arm
    induction_remission = inputs.get('remission_rates', {}).get(arm, 0.3)
    induction_partial = inputs.get('partial_response_rates', {}).get(arm, 0.2)
    relapse_rate_monthly = inputs.get('relapse_rates', {}).get(arm, 0.02)  # monthly relapse rate
    ae_rate = inputs.get('ae_rates', {}).get(arm, 0.01)
    death_rate = inputs.get('death_rates', {}).get('baseline', 0.001)  # baseline death rate

    # Tunnel progression (months in remission determine transitions)
    if time_in_remission is None:
        time_in_remission = 0

    # From Depressed (Non-response)
    P[STATE_INDEX['Depressed'], STATE_INDEX['Remission_0_3m']] = induction_remission
    P[STATE_INDEX['Depressed'], STATE_INDEX['PartialResponse']] = induction_partial
    P[STATE_INDEX['Depressed'], STATE_INDEX['Depressed']] = 1 - induction_remission - induction_partial - death_rate
    P[STATE_INDEX['Depressed'], STATE_INDEX['Death']] = death_rate

    # From PartialResponse
    P[STATE_INDEX['PartialResponse'], STATE_INDEX['Remission_0_3m']] = induction_remission * 0.5  # lower rate from partial
    P[STATE_INDEX['PartialResponse'], STATE_INDEX['PartialResponse']] = 1 - induction_remission * 0.5 - death_rate
    P[STATE_INDEX['PartialResponse'], STATE_INDEX['Death']] = death_rate

    # Tunnel transitions (time-dependent relapse hazard)
    tunnel_states = ['Remission_0_3m', 'Remission_4_6m', 'Remission_7_12m', 'Remission_12m_plus']
    for i, state in enumerate(tunnel_states):
        idx = STATE_INDEX[state]

        # Progress to next tunnel or stay
        if i < len(tunnel_states) - 1:
            # Move to next tunnel after 3 months
            if (cycle % 3) == 0 and cycle > 0:  # Every 3 months
                P[idx, STATE_INDEX[tunnel_states[i + 1]]] = 1 - relapse_rate_monthly - death_rate
            else:
                P[idx, idx] = 1 - relapse_rate_monthly - death_rate
        else:
            # Final tunnel - can stay indefinitely or relapse
            P[idx, idx] = 1 - relapse_rate_monthly - death_rate

        # Relapse from any remission state
        P[idx, STATE_INDEX['Relapse']] = relapse_rate_monthly
        P[idx, STATE_INDEX['Death']] = death_rate

    # From Relapse - can try treatment again or stay relapsed
    P[STATE_INDEX['Relapse'], STATE_INDEX['Depressed']] = 0.8  # Return to depressed for retreatment
    P[STATE_INDEX['Relapse'], STATE_INDEX['Relapse']] = 0.2 - death_rate
    P[STATE_INDEX['Relapse'], STATE_INDEX['Death']] = death_rate

    # From Post_AE - recovery or death
    P[STATE_INDEX['Post_AE'], STATE_INDEX['Depressed']] = 0.7
    P[STATE_INDEX['Post_AE'], STATE_INDEX['Post_AE']] = 0.3 - death_rate
    P[STATE_INDEX['Post_AE'], STATE_INDEX['Death']] = death_rate

    # Death is absorbing
    P[STATE_INDEX['Death'], STATE_INDEX['Death']] = 1.0

    # Add adverse event transitions from remission states (simplified)
    for state in tunnel_states:
        idx = STATE_INDEX[state]
        # Reduce self-loop probability to account for AE
        P[idx, idx] -= ae_rate
        P[idx, STATE_INDEX['Post_AE']] = ae_rate

    return P

def get_costs(arm, jurisdiction, perspective, inputs, cycle):
    """Get state-dependent costs for the arm in this cycle."""
    # Base treatment costs by arm (monthly)
    base_costs = {
        'ECT': 2000,  # ECT sessions
        'IV_Ketamine': 1500,  # IV ketamine infusions
        'Esketamine': 1200,  # Esketamine nasal spray
        'Oral_Ketamine': 800,  # Oral ketamine
        'rTMS': 600,  # rTMS sessions
        'Control': 300  # Standard care
    }

    # State-dependent cost adjustments
    _state_multipliers = {
        'Depressed': 1.0,  # Full treatment costs
        'PartialResponse': 0.8,  # Reduced intensity
        'Remission_0_3m': 0.3,  # Maintenance only
        'Remission_4_6m': 0.2,  # Minimal maintenance
        'Remission_7_12m': 0.1,  # Very low maintenance
        'Remission_12m_plus': 0.05,  # Minimal follow-up
        'Relapse': 1.2,  # Increased costs for relapse management
        'Post_AE': 1.5,  # AE management costs
        'Death': 0.0
    }

    # Phase-dependent costs (acute vs maintenance)
    acute_cycles = 1  # First month is acute
    if cycle < acute_cycles:
        phase_multiplier = 1.0  # Full acute costs
    else:
        phase_multiplier = 0.3  # Maintenance costs

    # Get base cost for this arm
    arm_base = base_costs.get(arm, 500)

    # Calculate total cost
    total_cost = arm_base * phase_multiplier

    # Add societal costs if perspective includes them
    if perspective == 'societal':
        # Transportation and time costs
        transportation_cost = 50  # Round trip transportation per visit
        time_cost = 100  # Patient time cost (lost productivity)

        # Treatment-specific visit frequencies
        visit_frequencies = {
            'ECT': 12,  # ECT sessions over acute period
            'IV_Ketamine': 8,  # IV infusions
            'Esketamine': 4,  # Esketamine administrations
            'Oral_Ketamine': 2,  # Follow-up visits
            'rTMS': 30,  # rTMS sessions
            'Control': 4   # Standard care visits
        }

        visits_per_month = visit_frequencies.get(arm, 4)
        monthly_transport = transportation_cost * visits_per_month
        monthly_time = time_cost * visits_per_month

        # Productivity losses based on health state
        # Note: We use friction cost method to avoid double counting with utilities
        productivity_loss = 0
        if cycle < acute_cycles:
            # Higher productivity loss during acute treatment
            productivity_loss = 500  # Monthly productivity loss during intensive treatment

        societal_addition = monthly_transport + monthly_time + productivity_loss
        total_cost += societal_addition

    return total_cost

def get_utility(state, inputs, cycle=None, arm=None, perspective='health_system'):
    """Get utility for the state with TRD-specific values and cognitive disutilities."""
    # TRD-specific utilities based on clinical evidence (EQ-5D values)
    base_utils = {
        'Depressed': 0.25,  # Severe TRD baseline (much lower than general depression)
        'PartialResponse': 0.45,  # Partial response utility
        'Remission_0_3m': 0.72,  # Early remission (6 months sustained)
        'Remission_4_6m': 0.75,  # Sustained remission (6-12 months)
        'Remission_7_12m': 0.78,  # Longer remission (12-18 months)
        'Remission_12m_plus': 0.80,  # Durable remission (>18 months)
        'Relapse': 0.20,  # Relapse utility (worse than baseline TRD)
        'Post_AE': 0.15,  # Post adverse event disutility
        'Death': 0.0
    }

    utility = base_utils.get(state, 0.0)

    # ECT cognitive disutility extends beyond acute month
    if arm and 'ECT' in arm and cycle is not None:
        ect_disutility = get_ect_cognitive_disutility(cycle)
        utility += ect_disutility  # disutility is negative

    # Treatment-specific acute disutilities
    if cycle is not None and cycle < 1:  # First month (acute phase)
        acute_disutilities = {
            'ECT': -0.15,  # ECT acute disutility (cognitive impairment, anesthesia)
            'IV_KA': -0.10,  # IV ketamine (infusions, monitoring)
            'IN_EKA': -0.08,  # Esketamine nasal (administration, monitoring)
            'PO_KA': -0.05,  # Oral ketamine (side effects)
            'PO_PSI': -0.12,  # Psilocybin (psychological preparation, integration)
            'rTMS': -0.03,  # rTMS (minimal acute disutility)
            'PHARM': -0.02   # Pharmacological (minimal)
        }

        if arm:
            arm_key = arm.split('_')[0]  # Extract base treatment
            utility += acute_disutilities.get(arm_key, 0.0)

    # Societal perspective: avoid double counting productivity
    # If utilities already reflect HR-QoL impact, don't add separate productivity losses
    # This is handled in the cost function for societal perspective

    return max(0.0, min(1.0, utility))  # Bound utilities to [0,1]

def get_ect_cognitive_disutility(cycle):
    """ECT cognitive disutility extending beyond acute month."""
    # Based on evidence that ECT cognitive effects can last weeks to months
    if cycle < 1:  # Acute month
        return -0.20  # Severe cognitive disutility
    elif cycle < 3:  # Months 2-3
        return -0.10  # Moderate persistent disutility
    elif cycle < 6:  # Months 4-6
        return -0.05  # Mild persistent disutility
    else:
        return 0.0  # No long-term cognitive disutility

def simulate_arm(arm, jurisdiction, perspective, settings, inputs, out_dir='nextgen_v3/out/'):
    """Simulate Markov model for one arm."""
    n_cycles = int(settings['time_horizon_years'] * 12 / settings['cycle_length_months'])
    discount_cost = settings['discount_costs'][jurisdiction]
    discount_qaly = settings['discount_qalys'][jurisdiction]

    # Load utility mapping config
    mapping_cfg = None
    mapping_path = 'nextgen_v3/config/utility_mapping.yaml'
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            mapping_cfg = yaml.safe_load(f)

    # Get cognitive measures (stub)
    measures = {'HVLT-R_Delta': -0.1, 'AMI_Delta': -0.05}  # stub deltas

    # Apply cognition mapping
    disutilities = apply_cognition_mapping(measures, mapping_cfg)

    # Determine phases
    acute_cycles = 1  # 1 month acute
    _maintenance_cycles = n_cycles - acute_cycles

    # Start in Depressed (treatment-resistant depression baseline)
    state_probs = np.zeros(len(STATES))
    state_probs[STATE_INDEX['Depressed']] = 1.0

    # Track time in remission for tunnel transitions
    time_in_remission = 0

    total_cost = 0
    total_qaly = 0
    for cycle in range(n_cycles):
        # Costs
        cost = sum(state_probs[i] * get_costs(arm, jurisdiction, perspective, inputs, cycle) for i in range(len(STATES)))
        total_cost += cost * (1 - discount_cost) ** (cycle / 12)  # annual discount

        # QALYs with enhanced utility system
        base_qaly = sum(state_probs[i] * get_utility(STATES[i], inputs, cycle, arm, perspective)
                       for i in range(len(STATES)))

        # Apply any additional disutilities (legacy compatibility)
        # Note: Most disutilities now handled in get_utility function
        adjusted_qaly = base_qaly

        total_qaly += adjusted_qaly * (1 - discount_qaly) ** (cycle / 12)

        # Transition with time-in-remission tracking
        P = get_transition_matrix(arm, inputs, cycle, time_in_remission)
        state_probs = state_probs @ P

        # Update time in remission if in remission tunnel
        current_state = np.argmax(state_probs)
        if 'Remission' in STATES[current_state]:
            time_in_remission += 1
        else:
            time_in_remission = 0

    # Save utility mapping effects
    effects = []
    for key, disutility in disutilities.items():
        effects.append({
            'arm': arm,
            'jurisdiction': jurisdiction,
            'perspective': perspective,
            'mapping_key': key,
            'disutility': disutility,
            'measure_HVLT_R_Delta': measures.get('HVLT-R_Delta', None),
            'measure_AMI_Delta': measures.get('AMI_Delta', None)
        })
    effects_df = pd.DataFrame(effects)
    effects_df.to_csv(f'{settings.get("out_dir", "nextgen_v3/out/")}utility_mapping_effects_v3.csv', mode='a', header=not os.path.exists(f'{settings.get("out_dir", "nextgen_v3/out/")}utility_mapping_effects_v3.csv'), index=False)

    return SimpleNamespace(cost=total_cost, qaly=total_qaly)

def run_cea_all_arms(settings_path, inputs, out_dir='nextgen_v3/out/'):
    """Run CEA for all arms, output results."""
    import yaml
    with open(settings_path, 'r') as f:
        settings = yaml.safe_load(f)

    results = []
    for arm in settings['arms']:
        for jur in settings['jurisdictions']:
            for pers in settings['perspectives']:
                res = simulate_arm(arm, jur, pers, settings, inputs)
                results.append({
                    'arm': arm,
                    'jurisdiction': jur,
                    'perspective': pers,
                    'total_cost': res.cost,
                    'total_qaly': res.qaly
                })

    df = pd.DataFrame(results)
    df.to_csv(f'{out_dir}/cea_results_by_arm_v3.csv', index=False)

    # Incremental vs ECT_std
    ect_std = df[df['arm'] == 'ECT_std'].set_index(['jurisdiction', 'perspective'])
    incremental = []
    for _, row in df.iterrows():
        if row['arm'] != 'ECT_std':
            base = ect_std.loc[(row['jurisdiction'], row['perspective'])]
            inc_cost = row['total_cost'] - base['total_cost']
            inc_qaly = row['total_qaly'] - base['total_qaly']
            icer = inc_cost / inc_qaly if inc_qaly != 0 else np.inf
            incremental.append({
                'arm': row['arm'],
                'jurisdiction': row['jurisdiction'],
                'perspective': row['perspective'],
                'incremental_cost': inc_cost,
                'incremental_qaly': inc_qaly,
                'icer': icer
            })

    inc_df = pd.DataFrame(incremental)
    inc_df.to_csv(f'{out_dir}/incremental_vs_ECT_std_v3.csv', index=False)

def run_structural_sensitivity(settings, inputs):
    """Run structural sensitivity analysis across all scenario combinations."""
    # Define arms
    arms = ['ECT_std', 'IV_ketamine']  # TODO: Load from config or inputs
    
    # Get all combinations
    scenarios = list(itertools.product(
        settings['structural_scenarios']['include_response_nonremit'],
        settings['structural_scenarios']['cycle_length_months'],
        settings['structural_scenarios']['semi_markov_memory'],
        settings['structural_scenarios']['switching_logic']
    ))
    
    # Baseline settings (assume default: true, 1, false, standard)
    baseline_settings = settings.copy()
    baseline_results = {}
    for arm in arms:
        res = simulate_arm(arm, 'AU', 'healthcare', baseline_settings, inputs)
        baseline_results[arm] = {'total_cost': res.cost, 'total_qaly': res.qaly}
    
    # Run each scenario
    results = []
    for i, (include_rnr, cycle_len, semi_markov, switching) in enumerate(scenarios):
        scenario_id = f"scenario_{i}"
        scen_settings = baseline_settings.copy()
        scen_settings['cycle_length_months'] = cycle_len
        # TODO: Implement modifications for include_rnr, semi_markov, switching
        
        for arm in arms:
            res = simulate_arm(arm, 'AU', 'healthcare', scen_settings, inputs)
            costs = res.cost
            qalys = res.qaly
            
            # Compute deltas
            wtp = 50000  # TODO: Use from settings
            baseline_costs = baseline_results[arm]['total_cost']
            baseline_qalys = baseline_results[arm]['total_qaly']
            baseline_nmb = baseline_qalys * wtp - baseline_costs
            
            nmb = qalys * wtp - costs
            
            inc_cost = costs - baseline_costs
            inc_qaly = qalys - baseline_qalys
            delta_icer = inc_cost / inc_qaly if inc_qaly != 0 else 0
            delta_nmb = nmb - baseline_nmb
            
            results.append({
                'scenario_id': scenario_id,
                'include_response_nonremit': include_rnr,
                'cycle_len_m': cycle_len,
                'semi_markov': semi_markov,
                'switching': switching,
                'arm': arm,
                'delta_ICER': delta_icer,
                'delta_INMB': delta_nmb
            })
    
    df = pd.DataFrame(results)
    os.makedirs('nextgen_v3/out', exist_ok=True)
    df.to_csv('nextgen_v3/out/structural_sensitivity_v3.csv', index=False)

def run_opportunity_cost_scenarios(settings, inputs):
    """Run opportunity cost scenarios across jurisdictions and k values."""
    if not settings.get('opportunity_cost', {}).get('use_k', False):
        return
    
    k_values = settings['opportunity_cost']['k_values']
    apply_in = settings['opportunity_cost']['apply_in']
    if 'CEA' not in apply_in:
        return
    
    # Stub incremental results vs ECT_std
    # In practice, get from run_cea_all_arms
    incremental_stub = {
        'AU': {
            'IV_ketamine': {'inc_cost': 10000, 'inc_qaly': 0.5}
        },
        'NZ': {
            'IV_ketamine': {'inc_cost': 8000, 'inc_qaly': 0.4}
        }
    }
    
    wtp = 50000  # Stub, assume same for AU/NZ
    
    results = []
    for jur in ['AU', 'NZ']:
        for k in k_values[jur]:
            for arm, inc in incremental_stub[jur].items():
                inc_cost = inc['inc_cost']
                inc_qaly = inc['inc_qaly']
                inmb_standard = inc_qaly * wtp - inc_cost
                health_forgone = inc_cost / k
                inmb_adjusted = inmb_standard - health_forgone * wtp
                results.append({
                    'jurisdiction': jur,
                    'k': k,
                    'arm': arm,
                    'INMB_standard': inmb_standard,
                    'INMB_adjusted': inmb_adjusted
                })
    
    df = pd.DataFrame(results)
    os.makedirs('nextgen_v3/out', exist_ok=True)
    df.to_csv('nextgen_v3/out/opportunity_cost_scenarios_v3.csv', index=False)