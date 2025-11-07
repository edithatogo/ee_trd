import argparse
import os
from datetime import datetime
import pandas as pd
from nextgen_v3.sourcing.harvest_costs import from_local_csv_au, from_local_csv_nz, write_costs_au, write_costs_nz
from nextgen_v3.sourcing.harvest_utilities import load_utilities_from_trials, write_utilities
from nextgen_v3.sourcing.harvest_equity import build_dcea_groups, build_dcea_weights, write_dcea_groups, write_dcea_weights
from nextgen_v3.sourcing.normalize_provenance import from_csl_json, from_bibtex, from_doi_list, write_provenance
from nextgen_v3.utils import ensure_v3_output_dir

def main():
    parser = argparse.ArgumentParser(description="Run sourcing pipeline to populate data schemas.")
    parser.add_argument('--costs-au', help='Path to local AU costs CSV')
    parser.add_argument('--costs-nz', help='Path to local NZ costs CSV')
    parser.add_argument('--utilities', help='Path to utilities CSV')
    parser.add_argument('--provenance-csl', help='Path to CSL-JSON')
    parser.add_argument('--provenance-bib', help='Path to BibTeX')
    parser.add_argument('--provenance-doi', help='Path to DOI list')
    parser.add_argument('--subgroups', action='store_true', help='Enable subgroup processing')
    parser.add_argument('--region', choices=['metro', 'rural'], help='Region filter')
    parser.add_argument('--ethnicity', choices=['Māori', 'Aboriginal & Torres Strait Islander', 'Pacific', 'Other'], help='Ethnicity filter')
    parser.add_argument('--payer', choices=['public', 'private'], help='Payer filter')
    parser.add_argument('--outdir', help='Output directory (overrides default)')
    args = parser.parse_args()

    date_str = datetime.now().strftime('%Y%m%d')
    if args.outdir:
        out_dir = args.outdir
    else:
        out_dir = f'nextgen_v3/out/{date_str}/'
    ensure_v3_output_dir(out_dir)

    os.makedirs(out_dir, exist_ok=True)

    if args.costs_au:
        df = from_local_csv_au(args.costs_au, region=args.region if args.subgroups else None, ethnicity=args.ethnicity if args.subgroups else None, payer=args.payer if args.subgroups else None)
        write_costs_au(df)
    if args.costs_nz:
        df = from_local_csv_nz(args.costs_nz, region=args.region if args.subgroups else None, ethnicity=args.ethnicity if args.subgroups else None, payer=args.payer if args.subgroups else None)
        write_costs_nz(df)
    if args.utilities:
        df = load_utilities_from_trials(args.utilities, region=args.region if args.subgroups else None, ethnicity=args.ethnicity if args.subgroups else None, payer=args.payer if args.subgroups else None)
        write_utilities(df)

    # Equity
    groups_df = build_dcea_groups(region=args.region if args.subgroups else None, ethnicity=args.ethnicity if args.subgroups else None, payer=args.payer if args.subgroups else None)
    write_dcea_groups(groups_df)
    weights_df = build_dcea_weights()
    write_dcea_weights(weights_df)

    # Provenance
    prov_df = pd.DataFrame()
    if args.provenance_csl:
        prov_df = pd.concat([prov_df, from_csl_json(args.provenance_csl)])
    if args.provenance_bib:
        prov_df = pd.concat([prov_df, from_bibtex(args.provenance_bib)])
    if args.provenance_doi:
        prov_df = pd.concat([prov_df, from_doi_list(args.provenance_doi)])
    if not prov_df.empty:
        write_provenance(prov_df)

if __name__ == '__main__':
    main()