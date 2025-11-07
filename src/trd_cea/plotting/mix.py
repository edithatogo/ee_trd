import matplotlib.pyplot as plt

def plot_stacked_mix(bia_df, output_path='nextgen_v3/out/bia_mix_plot_v3.png'):
    """Plot stacked bar chart of treatment mix over years."""
    # TODO: Implement stacked bar plot for adoption mix
    # For now, stub
    fig, ax = plt.subplots()
    ax.bar([1,2,3,4,5], [10,20,30,40,50])  # example
    plt.savefig(output_path)
    plt.close()