"""
PSA-enabled CEA for Psychedelics vs ECT (AU/NZ)
- Samples parameters from `parameters_psa.csv` using Distribution column (e.g., Beta(36,24), Gamma(sd=200))
- Uses a simplified cohort model (see cea_model.py); extend for decision-grade work.
Outputs:
- psa_results.csv (per-iteration costs & QALYs)
- ceac.png (cost-effectiveness acceptability curve)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import os
from concurrent.futures import ThreadPoolExecutor

script_dir = os.path.dirname(os.path.abspath(__file__))
PARAMS_CSV = os.path.join(script_dir, "../data/parameters_psa.csv")
COSTS_AU = os.path.join(script_dir, "../data/cost_inputs_au.csv")
COSTS_NZ = os.path.join(script_dir, "../data/cost_inputs_nz.csv")

def parse_dist(dist_str, mean):
    """Return sampler function given dist string and mean (from BaseValue)."""
    if pd.isna(dist_str) or dist_str=="" or str(dist_str).lower()=="fixed":
        return lambda n: np.full(n, mean)
    m = re.match(r"Beta\((\d+\.?\d*),\s*(\d+\.?\d*)\)", dist_str, re.I)
    if m:
        a=float(m.group(1)); b=float(m.group(2))
        return lambda n: np.random.beta(a,b,size=n)
    m = re.match(r"Gamma\(\s*sd\s*=\s*(\d+\.?\d*)\s*\)", dist_str, re.I)
    if m:
        sd=float(m.group(1)); mu=float(mean)
        k=(mu/sd)**2; theta=sd**2/mu
        return lambda n: np.random.gamma(shape=k, scale=theta, size=n)
    m = re.match(r"Normal\(\s*sd\s*=\s*(\d+\.?\d*)\s*\)", dist_str, re.I)
    if m:
        sd=float(m.group(1)); mu=float(mean)
        return lambda n: np.random.normal(mu, sd, size=n)
    m = re.match(r"Lognormal\(\s*gsd\s*=\s*(\d+\.?\d*)\s*\)", dist_str, re.I)
    if m:
        gsd=float(m.group(1)); mu=float(mean)
        # approximate: set sigma via gsd, derive mu_log from mean
        sigma=np.log(gsd); mu_log=np.log(mu) - 0.5*sigma**2
        return lambda n: np.random.lognormal(mean=mu_log, sigma=sigma, size=n)
    # default fixed
    return lambda n: np.full(n, mean)

def load_tables(country="AU"):
    params = pd.read_csv(PARAMS_CSV)
    costs = pd.read_csv(COSTS_AU if country=="AU" else COSTS_NZ)
    return params, costs

def get_cost(costs, item, country="AU"):
    col = "AUD_Value_2024" if country == "AU" else "NZD_Value_2024"
    row = costs[costs["Item"]==item]
    return float(row[col].iloc[0]) if not row.empty else 0.0

def simulate_once(draw, costs, country="AU", perspective="healthcare"):
    """Return dict of outcomes for each strategy (cost, qaly). Very simplified."""
    util_dep = draw("Utility depressed")
    util_rem = draw("Utility remission")

    # Adverse disutilities
    disutil_ect = draw("Adverse disutility ECT")
    disutil_ket = draw("Adverse disutility Ketamine")

    # remission probs
    p_remit = {
        "ECT": draw("ECT remission"),
        "Ketamine": draw("Ketamine remission (4w)"),
        "Esketamine": draw("Esketamine remission (4w)"),
        "Psilocybin": draw("Psilocybin remission")
    }

    # Healthcare costs (direct treatment costs) - NOW SAMPLED FROM DISTRIBUTIONS
    cost_ect_session = draw(f"Cost ECT session {country}")
    cost_ket_session = draw(f"Cost ketamine session {country}")
    cost_esk_session = draw(f"Cost esketamine session {country}")
    cost_psi_program = draw(f"Cost psilocybin program {country}")

    # Calculate total costs for treatment courses
    cost_ect = 8 * cost_ect_session  # 8 ECT sessions
    cost_ket = 8 * cost_ket_session  # 8 ketamine infusions
    cost_esk = 8 * cost_esk_session  # 8 esketamine treatments
    cost_psi = cost_psi_program  # Single psilocybin program

    # Societal costs (only included if perspective == "societal") - NOW SAMPLED FROM DISTRIBUTIONS
    societal_costs = {}
    if perspective == "societal":
        # Productivity loss (annual cost for depressed state)
        prod_loss = draw(f"Productivity loss per year {country}")

        # Informal care (annual cost for depressed state)
        informal_care = draw(f"Informal care per year {country}")

        # Out-of-pocket costs (per session)
        oop_ect_session = draw(f"OOP ECT per session {country}")
        oop_ket_session = draw(f"OOP Ketamine per session {country}")
        oop_esk_session = draw(f"OOP Ketamine per session {country}")  # Assume same as ketamine
        oop_psi = 0  # Assume covered by program

        # Calculate total societal costs over 5-year horizon
        societal_costs = {
            "ECT": (prod_loss + informal_care) * 5 + oop_ect_session * 8,  # 5 years + 8 sessions
            "Ketamine": (prod_loss + informal_care) * 5 + oop_ket_session * 8,
            "Esketamine": (prod_loss + informal_care) * 5 + oop_esk_session * 8,
            "Psilocybin": (prod_loss + informal_care) * 5 + oop_psi
        }

    # single-cycle-like simplification over 5y horizon for QALYs
    cohort = 1.0
    horizon_yrs = 5.0

    results = {}
    for s, cost_ind in [("ECT", cost_ect), ("Ketamine", cost_ket), ("Esketamine", cost_esk), ("Psilocybin", cost_psi)]:
        rem = cohort * p_remit[s]
        dep = cohort - rem

        # Adjust utilities for adverse events
        util_dep_adj = util_dep
        util_rem_adj = util_rem

        if s == "ECT":
            util_dep_adj += disutil_ect  # Adverse disutility applies to depressed state
        elif s in ["Ketamine", "Esketamine"]:
            util_dep_adj += disutil_ket

        qalys = (dep*util_dep_adj + rem*util_rem_adj) * horizon_yrs

        # Total cost depends on perspective
        total_cost = cost_ind
        if perspective == "societal":
            total_cost += societal_costs.get(s, 0)

        results[s] = {"cost": total_cost, "qalys": qalys}
    return results

def simulate_once_worker(i, samplers, costs, country="AU", perspective="healthcare"):
    """Worker function for parallel simulation."""
    def draw(name):
        return samplers[name](1)[0] if name in samplers else np.nan
    res = simulate_once(draw, costs, country, perspective)
    records = []
    wtp = 50000 if country == "AU" else 45000  # Country-specific WTP
    for s in ["Ketamine","Esketamine","Psilocybin"]:
        dcost = res[s]["cost"] - res["ECT"]["cost"]
        dq = res[s]["qalys"] - res["ECT"]["qalys"]
        nmb = dq*wtp - dcost
        records.append({"iter":i+1,"strategy":s,"cost":res[s]["cost"],"qalys":res[s]["qalys"],
                        "inc_cost":dcost,"inc_qalys":dq,"nmb":nmb})
    return records

def main(country="AU", N=2000, perspective="healthcare"):
    params, costs = load_tables(country)
    # build samplers
    samplers = {}
    for _,r in params.iterrows():
        name=r["Parameter"]; mean=float(r["BaseValue"]); dist=r["Distribution"]
        samplers[name]=parse_dist(dist, mean)

    # Parallel simulation with threads
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(simulate_once_worker, i, samplers, costs, country, perspective) for i in range(N)]
        records = []
        for future in futures:
            records.extend(future.result())

    df = pd.DataFrame(records)
    df.to_csv(f"psa_results_{country}_{perspective}.csv", index=False)

    # CEAC: probability of cost-effectiveness by WTP for each strategy vs ECT
    wtp_grid = np.linspace(0, 100000, 101)
    ceac = []
    for s in ["Ketamine","Esketamine","Psilocybin"]:
        df_s = df[df["strategy"]==s]
        for w in wtp_grid:
            prob = (df_s["nmb"] > 0).mean()  # simplified, assuming wtp fixed
            ceac.append({"strategy":s,"wtp":w,"prob_ce":prob})
    ceac_df = pd.DataFrame(ceac)

    fig, ax = plt.subplots(figsize=(8,6))
    for s in ["Ketamine","Esketamine","Psilocybin"]:
        sub = ceac_df[ceac_df["strategy"]==s]
        ax.plot(sub["wtp"], sub["prob_ce"], label=s)
    ax.set_xlabel("WTP (AUD per QALY)" if country=="AU" else "WTP (NZD per QALY)")
    ax.set_ylabel("Probability cost-effective vs ECT")
    ax.set_ylim(0,1)
    ax.legend()
    ax.set_title(f"Cost-Effectiveness Acceptability Curve\n{country} - {perspective.title()} Perspective")
    fig.tight_layout()
    fig.savefig(f"ceac_{country}_{perspective}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved psa_results_{country}_{perspective}.csv and ceac_{country}_{perspective}.png")

if __name__ == "__main__":
    # Run both perspectives for both countries
    for country in ["AU", "NZ"]:
        for perspective in ["healthcare", "societal"]:
            main(country, perspective=perspective)
