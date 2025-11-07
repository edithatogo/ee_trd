import argparse
import os
from datetime import datetime
from nextgen_v3.io.loaders import load_all_inputs
from nextgen_v3.model.value_of_info import run_value_of_info
from nextgen_v3.config import load_settings
from nextgen_v3.utils import ensure_v3_output_dir

def main():
    parser = argparse.ArgumentParser(description="Run Value of Information analysis.")
    parser.add_argument('--config', default='nextgen_v3/config/settings.yaml')
    parser.add_argument('--outdir', help='Output directory (overrides default)')
    args = parser.parse_args()

    settings = load_settings()
    inputs = load_all_inputs(args.config)
    
    date_str = datetime.now().strftime('%Y%m%d')
    if args.outdir:
        out_dir = args.outdir
    else:
        out_dir = f'nextgen_v3/out/{date_str}/'
    ensure_v3_output_dir(out_dir)
    
    os.makedirs(out_dir, exist_ok=True)
    
    run_value_of_info(settings, inputs, out_dir=out_dir)

if __name__ == '__main__':
    main()