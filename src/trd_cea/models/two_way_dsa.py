"""
Two-way DSA for Ketamine vs ECT
- Analyzes interaction between ECT remission rate and Ketamine remission rate
- Creates contour plot showing cost-effectiveness regions
- Outputs two_way_dsa_{country}.csv with results grid
"""
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.abspath(__file__))

def main(country="AU"):
    # Load base parameters from parameters_psa.csv
    params = pd.read_csv(os.path.join(script_dir, "../data/parameters_psa.csv")).set_index("Parameter")
    costs = params["BaseValue"].to_dict()

    # Load cost inputs
    cost_file = os.path.join(script_dir, f"../data/cost_inputs_{country.lower()}.csv")
    if os.path.exists(cost_file):
        cost_df = pd.read_csv(cost_file)
        value_col = "AUD_Value_2024" if country == "AU" else "NZD_Value_2024"
        for _, row in cost_df.iterrows():
            costs[row["Item"]] = float(row[value_col])

    # Set WTP based on country
    wtp = 50000 if country == "AU" else 45000

    # Helper functions
    def set_param(name, value):
        costs[name] = float(value)

    def get(name, default=0.0):
        return float(costs.get(name, default))

    def evaluate(p_ect, p_ket):
        """Return incremental NMB for Ketamine vs ECT under current params."""
        util_dep = get("Utility depressed", 0.57)
        util_rem = get("Utility remission", 0.81)

        c_ect = 8 * get(f"Cost ECT session {country}", 1000)
        c_ket = 8 * get(f"Cost ketamine session {country}", 300)

        # very simplified 5y QALY calc
        q_ect = ((1-p_ect)*util_dep + p_ect*util_rem)*5.0
        q_ket = ((1-p_ket)*util_dep + p_ket*util_rem)*5.0
        inc_cost = c_ket - c_ect
        inc_q = q_ket - q_ect
        inc_nmb = inc_q*wtp - inc_cost
        return inc_nmb

    # Two-way DSA: ECT remission vs Ketamine remission
    ect_remission_range = np.linspace(0.4, 0.8, 21)  # 21 points from 0.4 to 0.8
    ket_remission_range = np.linspace(0.2, 0.7, 21)  # 21 points from 0.2 to 0.7

    results = []
    for p_ect in ect_remission_range:
        for p_ket in ket_remission_range:
            nmb = evaluate(p_ect, p_ket)
            results.append({
                "ECT_remission": p_ect,
                "Ketamine_remission": p_ket,
                "Incremental_NMB": nmb,
                "Cost_effective": "Yes" if nmb >= 0 else "No"
            })

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(f"two_way_dsa_{country}.csv", index=False)

    # Create contour plot
    X, Y = np.meshgrid(ect_remission_range, ket_remission_range)
    Z = np.zeros_like(X)

    for i, p_ect in enumerate(ect_remission_range):
        for j, p_ket in enumerate(ket_remission_range):
            Z[j, i] = evaluate(p_ect, p_ket)  # Note: meshgrid indexing

    plt.figure(figsize=(10, 8))
    contour = plt.contourf(X, Y, Z, levels=np.linspace(Z.min(), Z.max(), 20), cmap='RdYlGn')
    plt.colorbar(contour, label='Incremental NMB')
    plt.contour(X, Y, Z, levels=[0], colors='black', linewidths=2, linestyles='--')
    plt.xlabel('ECT Remission Rate')
    plt.ylabel('Ketamine Remission Rate')
    plt.title(f'Two-way Sensitivity Analysis: ECT vs Ketamine Remission\n{country} (WTP = ${wtp:,})')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'two_way_dsa_{country}.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved two_way_dsa_{country}.csv and two_way_dsa_{country}.png")

if __name__ == "__main__":
    for country in ["AU", "NZ"]:
        main(country)