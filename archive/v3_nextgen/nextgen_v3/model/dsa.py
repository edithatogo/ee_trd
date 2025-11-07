import numpy as np
import matplotlib.pyplot as plt

def run_dsa(settings_path, inputs, wtp=50000, out_dir='nextgen_v3/out/'):
    """Run one-way DSA tornado on incremental NMB vs ECT_std."""
    import yaml
    with open(settings_path, 'r') as f:
        _settings = yaml.safe_load(f)

    # TODO: Vary each parameter in parameters_psa.csv ±20%, compute incremental NMB
    # For now, stub with example parameters
    params = ['param1', 'param2', 'param3']
    base_nmb = 10000  # stub
    low_nmb = [8000, 9000, 9500]
    high_nmb = [12000, 11000, 10500]

    # Plot tornado
    fig, ax = plt.subplots()
    y_pos = np.arange(len(params))
    ax.barh(y_pos, np.array(high_nmb) - base_nmb, left=base_nmb, color='red', label='High')
    ax.barh(y_pos, np.array(low_nmb) - base_nmb, left=base_nmb, color='blue', label='Low')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(params)
    ax.legend()
    plt.savefig(f'{out_dir}/tornado_v3.png')
    plt.close()