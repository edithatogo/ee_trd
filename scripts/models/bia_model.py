#!/usr/bin/env python3
"""
Budget Impact Analysis (BIA) Model
Generates 5-year BIA results for AU and NZ comparing ECT vs ketamine vs psilocybin uptake.
"""
import pandas as pd
import os
import sys
from pathlib import Path

# Setup logging infrastructure
script_dir = Path(__file__)
if script_dir.name in ('main.py', 'run.py'):
    script_dir = script_dir.parent
sys.path.insert(0, str(script_dir.parent))

from analysis.core.logging_config import get_default_logging_config, setup_analysis_logging  # noqa: E402

logging_config = get_default_logging_config()
logging_config.level = "INFO"
logger = setup_analysis_logging(__name__, logging_config)

def bia_5y(country="AU", ect_patients=3000, uptake_ket=[0.05,0.10,0.15,0.20,0.25], uptake_psi=[0.01,0.03,0.06,0.08,0.10]):
    cost_file = os.path.join(script_dir, f"../data/cost_inputs_{country.lower()}.csv")
    cost_table = pd.read_csv(cost_file)
    def get(item):
        row = cost_table[cost_table["Item"]==item]
        return float(row.iloc[0,1]) if not row.empty else 0.0
    c_ect = get("ECT total session cost (public)")*8
    c_ket = get("Ketamine total session (IV)")*12
    c_psi = get("Psilocybin program (2-dose + therapy)")
    out=[]
    for y in range(5):
        ect_share = 1 - uptake_ket[y] - uptake_psi[y]
        ect_n = int(ect_patients*ect_share)
        ket_n = int(ect_patients*uptake_ket[y])
        psi_n = int(ect_patients*uptake_psi[y])
        baseline = ect_patients*c_ect
        scenario = ect_n*c_ect + ket_n*c_ket + psi_n*c_psi
        out.append({"year":y+1,"baseline_cost":baseline,"scenario_cost":scenario,"net_impact":scenario-baseline,
                    "ECT_patients":ect_n,"Ket_patients":ket_n,"Psi_patients":psi_n})
    df = pd.DataFrame(out)
    df.to_csv(f"bia_results_{country}.csv", index=False)
    print(f"Saved bia_results_{country}.csv")
    return df

if __name__=="__main__":
    for country in ["AU", "NZ"]:
        bia_5y(country)
