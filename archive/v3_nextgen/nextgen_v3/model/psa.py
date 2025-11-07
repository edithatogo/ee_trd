import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import beta, gamma, lognorm, norm
from .cea_engine import simulate_arm
from ..plots.pricing import plot_pricing

def sample_parameters(psa_df, n_iter=2000, correlated=False, correlations_path=None):
    """Sample parameters for PSA."""
    samples = {}
    if correlated and correlations_path:
        import yaml
        with open(correlations_path, 'r') as f:
            corr_config = yaml.safe_load(f)
        # Collect all params in blocks
        block_params = set()
        for block in corr_config['blocks']:
            block_params.update(block['params'])
        # Generate independent normals for all params
        all_params = list(psa_df['parameter'].unique())
        z_indep = norm.rvs(size=(n_iter, len(all_params)))
        param_to_idx = {p: i for i, p in enumerate(all_params)}
        # For each block, apply correlation
        for block in corr_config['blocks']:
            params = block['params']
            corr = np.array(block['corr'])
            if len(params) != corr.shape[0]:
                print(f"Skipping block {block['name']}: param count mismatch")
                continue
            try:
                L = np.linalg.cholesky(corr)
            except np.linalg.LinAlgError:
                print(f"Skipping block {block['name']}: correlation not PD")
                continue
            # Get indices
            indices = [param_to_idx[p] for p in params if p in param_to_idx]
            if len(indices) != len(params):
                print(f"Skipping block {block['name']}: some params not in psa_df")
                continue
            # Apply correlation
            z_block = z_indep[:, indices]
            z_corr = z_block @ L
            # Now, for each param in block, map to distribution
            for i, param in enumerate(params):
                if param not in psa_df['parameter'].values:
                    continue
                row = psa_df[psa_df['parameter'] == param].iloc[0]
                dist = row['distribution']
                mean = row['mean']
                std = row['std']
                z_vals = z_corr[:, i]
                if dist == 'Beta':
                    var = std**2
                    alpha = mean * (mean*(1-mean)/var - 1)
                    beta_param = (1-mean) * (mean*(1-mean)/var - 1)
                    samples[param] = beta.ppf(norm.cdf(z_vals), alpha, beta_param)
                elif dist == 'Gamma':
                    samples[param] = gamma.ppf(norm.cdf(z_vals), mean**2 / std**2, scale=std**2/mean)
                elif dist == 'Lognormal':
                    samples[param] = lognorm.ppf(norm.cdf(z_vals), s=std, scale=np.exp(mean))
                elif dist == 'Normal':
                    samples[param] = norm.ppf(norm.cdf(z_vals), mean, std)
                else:
                    # Independent fallback
                    samples[param] = norm.rvs(mean, std, size=n_iter)
        # For params not in blocks, independent
        for _, row in psa_df.iterrows():
            param = row['parameter']
            if param in samples:
                continue  # Already done
            dist = row['distribution']
            mean = row['mean']
            std = row['std']
            if dist == 'Beta':
                var = std**2
                alpha = mean * (mean*(1-mean)/var - 1)
                beta_param = (1-mean) * (mean*(1-mean)/var - 1)
                samples[param] = beta.rvs(alpha, beta_param, size=n_iter)
            elif dist == 'Gamma':
                samples[param] = gamma.rvs(mean**2 / std**2, scale=std**2/mean, size=n_iter)
            elif dist == 'Lognormal':
                samples[param] = lognorm.rvs(s=std, scale=np.exp(mean), size=n_iter)
            elif dist == 'Normal':
                samples[param] = norm.rvs(mean, std, size=n_iter)
    else:
        # Independent sampling
        for _, row in psa_df.iterrows():
            param = row['parameter']
            dist = row['distribution']
            mean = row['mean']
            std = row['std']
            if dist == 'Beta':
                var = std**2
                alpha = mean * (mean*(1-mean)/var - 1)
                beta_param = (1-mean) * (mean*(1-mean)/var - 1)
                samples[param] = beta.rvs(alpha, beta_param, size=n_iter)
            elif dist == 'Gamma':
                samples[param] = gamma.rvs(mean**2 / std**2, scale=std**2/mean, size=n_iter)
            elif dist == 'Lognormal':
                samples[param] = lognorm.rvs(s=std, scale=np.exp(mean), size=n_iter)
            elif dist == 'Normal':
                samples[param] = norm.rvs(mean, std, size=n_iter)
    return pd.DataFrame(samples)

def run_psa(settings_path, inputs, n_iter=2000, out_dir='nextgen_v3/out/'):
    """Run PSA and generate outputs."""
    import yaml
    with open(settings_path, 'r') as f:
        settings = yaml.safe_load(f)

    # Stub inputs if not provided
    if inputs is None:
        from types import SimpleNamespace
        inputs = SimpleNamespace()
        # Create stub parameters_psa
        import pandas as pd
        inputs.parameters_psa = pd.DataFrame({
            'parameter': ['param1', 'param2'],
            'distribution': ['Normal', 'Beta'],
            'mean': [0.5, 0.6],
            'std': [0.1, 0.05]
        })

    correlated = settings.get('correlated_psa', False)
    correlations_path = 'nextgen_v3/config/correlations.yaml' if correlated else None
    param_samples = sample_parameters(inputs.parameters_psa, n_iter, correlated=correlated, correlations_path=correlations_path)

    results = []
    for i in range(n_iter):
        sample = param_samples.iloc[i]
        # TODO: Pass sample to cea_engine.simulate_arm
        for arm in settings['arms']:
            for jur in settings['jurisdictions']:
                for pers in settings['perspectives']:
                    res = simulate_arm(arm, jur, pers, settings, inputs, out_dir)
                    results.append({
                        'iteration': i,
                        'arm': arm,
                        'jurisdiction': jur,
                        'perspective': pers,
                        'cost': res.cost,
                        'qaly': res.qaly
                    })

    df = pd.DataFrame(results)
    df.to_csv(f'{out_dir}/psa_results_v3.csv', index=False)

    # Compute mean stats for frontier
    mean_stats = df.groupby('arm').agg({'cost': 'mean', 'qaly': 'mean'}).reset_index()

    # Identify frontier arms (Pareto frontier in cost-QALY space)
    frontier_arms = []
    sorted_arms = mean_stats.sort_values('cost')
    max_qaly = -np.inf
    for _, row in sorted_arms.iterrows():
        if row['qaly'] > max_qaly:
            frontier_arms.append(row['arm'])
            max_qaly = row['qaly']

    # CEAC
    wtp_grid = settings['wtp_grid']
    ceac_results = []
    for wtp in wtp_grid:
        for arm in settings['arms']:
            arm_data = df[df['arm'] == arm]
            nmb = arm_data['qaly'] * wtp - arm_data['cost']
            max_nmb = df.groupby('iteration').apply(lambda x: x['qaly'] * wtp - x['cost']).max()
            prob_ce = (nmb >= max_nmb).mean()
            ceac_results.append({'wtp': wtp, 'arm': arm, 'prob_ce': prob_ce})

    ceac_df = pd.DataFrame(ceac_results)
    ceac_df.to_csv(f'{out_dir}/ceac_v3.csv', index=False)
    # Plot CEAC
    for arm in settings['arms']:
        arm_data = ceac_df[ceac_df['arm'] == arm]
        plt.plot(arm_data['wtp'], arm_data['prob_ce'], label=arm)
    plt.legend()
    plt.savefig(f'{out_dir}/ceac_v3.png')
    plt.close()

    # CEAF: prob of optimal arm
    ceaf_results = []
    for wtp in wtp_grid:
        optimal_arms = df.groupby('iteration').apply(lambda x: x.loc[(x['qaly'] * wtp - x['cost']).idxmax(), 'arm'])
        for arm in settings['arms']:
            prob = (optimal_arms == arm).mean()
            ceaf_results.append({'wtp': wtp, 'arm': arm, 'prob_optimal': prob})

    ceaf_df = pd.DataFrame(ceaf_results)
    ceaf_df.to_csv(f'{out_dir}/ceaf_v3.csv', index=False)
    # Plot CEAF with frontier annotation
    for arm in settings['arms']:
        label = arm
        if arm in frontier_arms:
            label += ' (frontier)'
        arm_data = ceaf_df[ceaf_df['arm'] == arm]
        plt.plot(arm_data['wtp'], arm_data['prob_optimal'], label=label)
    plt.legend()
    plt.savefig(f'{out_dir}/ceaf_v3.png')
    plt.close()

    # Regret analysis
    regret_results = []
    for wtp in wtp_grid:
        for iteration in df['iteration'].unique():
            iter_data = df[df['iteration'] == iteration]
            nmbs = iter_data['qaly'] * wtp - iter_data['cost']
            max_nmb = nmbs.max()
            for _, row in iter_data.iterrows():
                nmb = row['qaly'] * wtp - row['cost']
                regret = max_nmb - nmb
                regret_results.append({'iteration': iteration, 'wtp': wtp, 'arm': row['arm'], 'regret': regret})
    
    regret_df = pd.DataFrame(regret_results)
    expected_regret = regret_df.groupby(['arm', 'wtp'])['regret'].mean().reset_index(name='expected_regret')
    expected_regret.to_csv(f'{out_dir}/regret_table_v3.csv', index=False)
    
    # Minimax arm
    max_regret_per_arm = expected_regret.groupby('arm')['expected_regret'].max()
    minimax_arm = max_regret_per_arm.idxmin()
    print(f"Minimax arm: {minimax_arm}")
    
    # Plot regret curves
    from nextgen_v3.plots.frontier import plot_regret_curves
    plot_regret_curves(expected_regret, output_path=f'{out_dir}/regret_curves_v3.png')

    # Distributionally-robust NMB (optional)
    dr_results = []
    for arm in settings['arms']:
        arm_data = df[df['arm'] == arm]
        nmbs = arm_data['qaly'] * wtp_grid[0] - arm_data['cost']  # Use first wtp for simplicity
        # Bootstrap worst-case
        bootstrap_nmbs = []
        for _ in range(100):
            sample = nmbs.sample(n=len(nmbs), replace=True)
            bootstrap_nmbs.append(sample.min())  # Worst-case
        dr_nmb = np.mean(bootstrap_nmbs)
        dr_results.append({'arm': arm, 'dr_nmb': dr_nmb})
    
    dr_df = pd.DataFrame(dr_results)
    dr_df.to_csv(f'{out_dir}/dr_nmb_v3.csv', index=False)

    # Pricing thresholds
    plot_pricing(df, wtp_grid=wtp_grid, output_path=f'{out_dir}/pricing_thresholds_v3.png', csv_path=f'{out_dir}/pricing_thresholds_v3.csv')

    # ICER scatter vs ECT_std
    ect_data = df[df['arm'] == 'ECT_std'].set_index(['iteration', 'jurisdiction', 'perspective'])
    inc_results = []
    for _, row in df.iterrows():
        if row['arm'] != 'ECT_std':
            base = ect_data.loc[(row['iteration'], row['jurisdiction'], row['perspective'])]
            inc_cost = row['cost'] - base['cost']
            inc_qaly = row['qaly'] - base['qaly']
            inc_results.append({'arm': row['arm'], 'inc_cost': inc_cost, 'inc_qaly': inc_qaly})

    inc_df = pd.DataFrame(inc_results)
    plt.scatter(inc_df['inc_qaly'], inc_df['inc_cost'])
    plt.xlabel('Incremental QALYs')
    plt.ylabel('Incremental Cost')
    plt.savefig(f'{out_dir}/icer_scatter_v3.png')
    plt.close()