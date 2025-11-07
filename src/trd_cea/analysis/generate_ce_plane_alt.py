#!/usr/bin/env python
"""Generate Alternative CE Plane with Legend Below"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.plotting import plot_ce_plane, JournalStandards  # noqa: E402
from trd_cea.run_v4_analysis import load_psa_data  # noqa: E402

base_dir = Path('outputs_v4/run_latest')
analyses = [('AU', 'healthcare'), ('AU', 'societal'), ('NZ', 'healthcare'), ('NZ', 'societal')]
standards = JournalStandards()

for jur, persp in analyses:
    print(f"{jur} - {persp}...")
    figures_dir = base_dir / 'figures' / jur / persp
    data_path = Path(f'data/sample/psa_sample_{jur}_{persp}.csv')
    
    if not data_path.exists():
        continue
    
    psa = load_psa_data(data_path, persp, jur)
    costs = psa.table.pivot(index='draw', columns='strategy', values='cost')
    effects = psa.table.pivot(index='draw', columns='strategy', values='effect')
    
    plot_ce_plane(
        costs=costs,
        effects=effects,
        reference_strategy='UC',
        output_path=figures_dir / 'ce_plane_alt',
        wtp=50000,
        currency='A$',
        title=f"Cost-Effectiveness Plane ({jur} {persp.title()})",
        standards=standards,
        legend_below=True,
        ylim=(-5000, 55000)
    )
    print("  ✓ Generated ce_plane_alt")

print("\n✓ Complete!")
