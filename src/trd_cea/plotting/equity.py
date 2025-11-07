import matplotlib.pyplot as plt

def plot_equity_impact(dcea_df, output_path='nextgen_v3/out/equity_plane_v3.png'):
    """Equity impact plane ΔAtkinson vs ΔTotal QALY."""
    # Assume dcea_df has columns: arm, epsilon, delta_atkinson, delta_total_qaly
    # Filter to a specific epsilon, e.g., 0 for utilitarian
    df = dcea_df[dcea_df['epsilon'] == 0]
    for arm in df['arm'].unique():
        arm_data = df[df['arm'] == arm]
        plt.scatter(arm_data['delta_atkinson'], arm_data['delta_total_qaly'], label=arm)
    plt.xlabel('ΔAtkinson Index')
    plt.ylabel('ΔTotal QALY')
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def plot_distributional_ceac(dcea_df, epsilons=[0,1,3], output_path='nextgen_v3/out/dceac_v3.png'):
    """Distributional CEAC by ε."""
    # Assume dcea_df has columns: epsilon, wtp, arm, prob_ce_weighted
    for eps in epsilons:
        df_eps = dcea_df[dcea_df['epsilon'] == eps]
        for arm in df_eps['arm'].unique():
            arm_data = df_eps[df_eps['arm'] == arm]
            plt.plot(arm_data['wtp'], arm_data['prob_ce_weighted'], label=f'{arm} ε={eps}')
    plt.xlabel('WTP ($/QALY)')
    plt.ylabel('Probability Cost-Effective (Weighted)')
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def plot_ecea_catastrate(ecea_df, output_path='nextgen_v3/out/ecea_catastrate_v3.png'):
    """ECEA catastrophe rates by arm and quintile."""
    for arm in ecea_df['arm'].unique():
        arm_data = ecea_df[ecea_df['arm'] == arm]
        plt.plot(arm_data['quintile'], arm_data['catastrophe_rate'], label=arm)
    plt.xlabel('Income Quintile')
    plt.ylabel('Catastrophe Rate')
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def plot_evppi(evppi_df, output_path='nextgen_v3/out/evppi_bar_v3.png'):
    """EVPPI bar plot."""
    plt.bar(evppi_df['parameter_group'], evppi_df['evppi'])
    plt.xlabel('Parameter Group')
    plt.ylabel('EVPPI')
    plt.xticks(rotation=45)
    plt.savefig(output_path)
    plt.close()

def plot_evsi(evsi_df, output_path='nextgen_v3/out/evsi_curve_v3.png'):
    """EVSI curve."""
    plt.plot(evsi_df['sample_size'], evsi_df['evsi'])
    plt.xlabel('Sample Size')
    plt.ylabel('EVSI')
    plt.savefig(output_path)
    plt.close()

def plot_rac(dcea_df, epsilons=[0,1,3], output_path='nextgen_v3/out/rac_epsilon_v3.png'):
    """Rank Acceptability Curves by ε."""
    # Assume dcea_df has columns: epsilon, wtp, arm, prob_rank1
    for eps in epsilons:
        df_eps = dcea_df[dcea_df['epsilon'] == eps]
        for arm in df_eps['arm'].unique():
            arm_data = df_eps[df_eps['arm'] == arm]
            plt.plot(arm_data['wtp'], arm_data['prob_rank1'], label=f'{arm} ε={eps}')
    plt.xlabel('WTP ($/QALY)')
    plt.ylabel('Probability Rank 1')
    plt.legend()
    plt.savefig(output_path)
    plt.close()