"""
One-way DSA for Ketamine vs ECT
- Reads dsa_inputs.csv
- For each parameter, evaluates Low and High while holding others at Base.
- Outputs dsa_results_{country}.csv with impact on incremental NMB (vs ECT) at WTP.
"""
import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

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

    # Helper to override a specific parameter
    def set_param(name, value):
        costs[name] = float(value)

    def get(name, default=0.0):
        return float(costs.get(name, default))

    def evaluate():
        """Return incremental NMB for Ketamine vs ECT under current params."""
        util_dep = get("Utility depressed", 0.57)
        util_rem = get("Utility remission", 0.81)
        p_ect = get("ECT remission", 0.60)
        p_ket = get("Ketamine remission (4w)", 0.45)

        c_ect = 8 * get(f"Cost ECT session {country}", 1000)
        c_ket = 8 * get(f"Cost ketamine session {country}", 300)

        # very simplified 5y QALY calc
        q_ect = ((1-p_ect)*util_dep + p_ect*util_rem)*5.0
        q_ket = ((1-p_ket)*util_dep + p_ket*util_rem)*5.0
        inc_cost = c_ket - c_ect
        inc_q = q_ket - q_ect
        inc_nmb = inc_q*wtp - inc_cost
        return inc_nmb

    # Run DSA
    dsa = pd.read_csv(os.path.join(script_dir, "../data/dsa_inputs.csv"))
    # Map AU parameters to NZ if needed
    if country == "NZ":
        dsa["Parameter"] = dsa["Parameter"].str.replace(" AU", " NZ")
    rows = []
    base_nmb = evaluate()
    for _,r in dsa.iterrows():
        name=r["Parameter"]
        base=r["Base"]
        low=r["Low"]
        high=r["High"]
        # backup
        original = costs.get(name, base)
        # low
        set_param(name, low)
        nmb_low = evaluate()
        # high
        set_param(name, high)
        nmb_high = evaluate()
        # restore
        set_param(name, original)
        rows.append({"Parameter":name,"Low":float(low),"High":float(high),"Base":float(base),
                     "NMB_low":nmb_low,"NMB_high":nmb_high,"NMB_base":base_nmb,
                     "Impact_low":abs(nmb_low-base_nmb),"Impact_high":abs(nmb_high-base_nmb)})
    out = pd.DataFrame(rows)
    out.to_csv(f"dsa_results_{country}.csv", index=False)
    print(f"Saved dsa_results_{country}.csv")

if __name__ == "__main__":
    for country in ["AU", "NZ"]:
        main(country)
