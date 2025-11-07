import pandas as pd
import numpy as np

def gini_index(values):
    """Compute Gini index for inequality."""
    values = np.array(values)
    values = np.sort(values)
    n = len(values)
    cumsum = np.cumsum(values)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0

def atkinson_index(qalys, epsilon):
    """Compute Atkinson index for QALYs."""
    qalys = np.array(qalys)
    if epsilon == 0:
        return np.mean(qalys)
    elif epsilon == 1:
        return np.exp(np.mean(np.log(qalys)))
    else:
        return (np.mean(qalys**(1-epsilon)))**(1/(1-epsilon))

def run_dcea(cea_results_df, dcea_groups_df, dcea_weights_df, settings, inputs, wtp=50000, out_dir='nextgen_v3/out/'):
    """Run DCEA analysis with optional opportunity cost adjustment."""
    # Group-level cost/QALY/INB
    group_results = []
    for _, group in dcea_groups_df.iterrows():
        for _, arm_row in cea_results_df.iterrows():
            # TODO: Distribute CEA results to groups based on PopShare, etc.
            cost = arm_row['total_cost'] * group['pop_share']
            qaly = arm_row['total_qaly'] * group['pop_share']
            inb = qaly * wtp - cost
            
            # Adjust for opportunity cost if applicable
            if 'DCEA' in settings.get('opportunity_cost', {}).get('apply_in', []):
                # Stub: assume displaced_health proportional or from shares
                total_displaced = 0.1  # Stub, from CEA
                if hasattr(inputs, 'opportunity_cost_shares'):
                    share = inputs.opportunity_cost_shares.set_index('group').loc[group['group'], 'share']
                else:
                    share = 1 / len(dcea_groups_df)  # Proportional
                displaced_health = total_displaced * share
                inb_adjusted = inb - displaced_health * wtp
                # But for now, just note
            else:
                inb_adjusted = inb
            
            group_results.append({
                'group': group['group'],
                'arm': arm_row['arm'],
                'jurisdiction': arm_row['jurisdiction'],
                'perspective': arm_row['perspective'],
                'cost': cost,
                'qaly': qaly,
                'inb': inb,
                'inb_adjusted': inb_adjusted
            })

    group_df = pd.DataFrame(group_results)
    group_df.to_csv(f'{out_dir}/dcea_by_group_v3.csv', index=False)

    # EDE-QALYs from SWF
    ede_results = []
    swf_df = dcea_weights_df[dcea_weights_df['type'] == 'SWF']
    epsilons = swf_df['epsilon'].tolist() if not swf_df.empty else [0, 1, 3, 7]
    for eps in epsilons:
        for arm in cea_results_df['arm'].unique():
            arm_data = group_df[group_df['arm'] == arm]
            qalys = arm_data['qaly']
            ede_qaly = atkinson_index(qalys, eps)
            total_qaly = qalys.sum()
            ede_results.append({'arm': arm, 'epsilon': eps, 'ede_qaly': ede_qaly, 'total_qaly': total_qaly})

    ede_df = pd.DataFrame(ede_results)
    ede_df.to_csv(f'{out_dir}/dcea_edeqaly_v3.csv', index=False)

    # Weighted INB
    weighted_results = []
    weights_df = dcea_weights_df[dcea_weights_df['type'] == 'Weights']
    if not weights_df.empty:
        for arm in cea_results_df['arm'].unique():
            arm_data = group_df[group_df['arm'] == arm]
            weighted_inb = 0
            for _, w_row in weights_df.iterrows():
                group_inb = arm_data[arm_data['group'] == w_row['group']]['inb'].iloc[0]
                weighted_inb += group_inb * w_row['weight']
            weighted_results.append({'arm': arm, 'weighted_inb': weighted_inb})
    
    weighted_df = pd.DataFrame(weighted_results)
    weighted_df.to_csv(f'{out_dir}/dcea_weighted_inb_v3.csv', index=False)

    # Distributional CEAC
    dceac_results = []
    for eps in epsilons:
        ede_by_arm = ede_df[ede_df['epsilon'] == eps].set_index('arm')['ede_qaly']
        max_ede = ede_by_arm.max()
        for arm in ede_by_arm.index:
            prob = 1.0 if ede_by_arm[arm] == max_ede else 0.0  # Stub, no PSA
            dceac_results.append({'epsilon': eps, 'arm': arm, 'prob_ce': prob})
    
    dceac_df = pd.DataFrame(dceac_results)
    dceac_df.to_csv(f'{out_dir}/dceac_v3.csv', index=False)

    # Inequality deltas with opportunity cost allocation
    inequality_results = []
    displaced_total = 0.1  # Stub, from CEA opportunity cost
    shares_df = inputs.opportunity_cost_shares if hasattr(inputs, 'opportunity_cost_shares') else None
    
    for eps in epsilons:
        for arm in cea_results_df['arm'].unique():
            jur = cea_results_df[cea_results_df['arm'] == arm]['jurisdiction'].iloc[0]  # Assume same
            arm_data = group_df[group_df['arm'] == arm]
            groups = arm_data['group'].unique()
            n_groups = len(groups)
            
            for concentrated in [False, True]:
                qalys_no_adj = arm_data['qaly'].values
                ede_no_adj = atkinson_index(qalys_no_adj, eps)
                gini_no_adj = gini_index(qalys_no_adj)
                
                qalys_adj = []
                for _, row in arm_data.iterrows():
                    qaly = row['qaly']
                    group = row['group']
                    if concentrated and shares_df is not None:
                        share_row = shares_df[(shares_df['jurisdiction'] == jur) & (shares_df['group'] == group)]
                        share = share_row['share'].iloc[0] if not share_row.empty else 1 / n_groups
                    else:
                        share = 1 / n_groups
                    displaced = displaced_total * share
                    qaly_adj = qaly - displaced
                    qalys_adj.append(qaly_adj)
                
                ede_adj = atkinson_index(qalys_adj, eps)
                gini_adj = gini_index(qalys_adj)
                
                delta_atkinson = ede_adj - ede_no_adj
                delta_gini = gini_adj - gini_no_adj
                
                inequality_results.append({
                    'jur': jur,
                    'epsilon': eps,
                    'arm': arm,
                    'delta_atkinson': delta_atkinson,
                    'delta_gini': delta_gini,
                    'concentrated_flag': concentrated
                })
    
    inequality_df = pd.DataFrame(inequality_results)
    inequality_df.to_csv(f'{out_dir}/dcea_inequality_delta_v3.csv', index=False)

    # Weighted INB
    weighted_results = []
    for _, weight_row in dcea_weights_df.iterrows():
        group = weight_row['group']
        weight = weight_row['weight']
        group_data = group_df[group_df['group'] == group]
        weighted_inb = (group_data['inb'] * weight).sum()
        weighted_results.append({'group': group, 'weighted_inb': weighted_inb})

    weighted_df = pd.DataFrame(weighted_results)
    weighted_df.to_csv(f'{out_dir}/dcea_weighted_inb_v3.csv', index=False)

    return ede_df