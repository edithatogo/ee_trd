import argparse
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Run MCDA analysis (stub).")
    parser.add_argument('--config', default='nextgen_v3/config/settings.yaml')
    parser.add_argument('--outdir', help='Output directory (overrides default)')
    args = parser.parse_args()

    date_str = datetime.now().strftime('%Y%m%d')
    if args.outdir:
        out_dir = args.outdir
    else:
        out_dir = f'nextgen_v3/out/{date_str}/'
    if not (out_dir.startswith('nextgen_v3/out/') or out_dir.startswith('orchestration/out_versions/')):
        raise ValueError("Outputs must be under nextgen_v3/out/ or orchestration/out_versions/")

    os.makedirs(out_dir, exist_ok=True)

    # TODO: Implement MCDA
    print("MCDA stub - not implemented")

if __name__ == '__main__':
    main()