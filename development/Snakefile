rule all:
    input:
        "psa_results_AU.csv",
        "ceac_AU.png",
        "dsa_results_AU.csv",
        "bia_results_AU.csv",
        "psa_results_NZ.csv",
        "ceac_NZ.png",
        "dsa_results_NZ.csv",
        "bia_results_NZ.csv",
        "results/analysis_v2_pipeline.done"

rule run_cea:
    output:
        "cea_output.txt"
    shell:
        "python scripts/cea_model.py > cea_output.txt"

rule run_psa_au:
    output:
        "psa_results_AU.csv",
        "ceac_AU.png"
    shell:
        "python scripts/psa_cea_model.py"

rule run_psa_nz:
    output:
        "psa_results_NZ.csv",
        "ceac_NZ.png"
    shell:
        "python scripts/psa_cea_model.py"

rule run_dsa_au:
    output:
        "dsa_results_AU.csv"
    shell:
        "python scripts/dsa_run.py"

rule run_dsa_nz:
    output:
        "dsa_results_NZ.csv"
    shell:
        "python scripts/dsa_run.py"

rule run_bia_au:
    output:
        "bia_results_AU.csv"
    shell:
        "python scripts/bia_model.py"

rule run_bia_nz:
    output:
        "bia_results_NZ.csv"
    shell:
        "python scripts/bia_model.py"


rule analysis_v2_pipeline:
    output:
        "results/analysis_v2_pipeline.done"
    shell:
        "python analysis_v2/run_pipeline.py && touch {output}"