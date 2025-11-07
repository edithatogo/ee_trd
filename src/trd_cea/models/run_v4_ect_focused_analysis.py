"""
Run ECT-Focused V4 analysis and generate all outputs.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trd_cea.core.io import PSAData, StrategyConfig  # noqa: E402
from trd_cea.core.log_utils import setup_script_logging, AnalysisContext  # noqa: E402
from analysis.engines import cea_engine, dcea_engine, voi_engine  # noqa: E402
from analysis.plotting import cea_plots, dcea_plots, voi_plots  # noqa: E402


def create_ect_focused_config():
    """Create ECT-focused strategy configuration."""
    return StrategyConfig(
        base='ECT',
        perspectives=['healthcare', 'societal'],
        strategies=[
            'ECT', 'KA-ECT', 'IV-KA', 'IN-EKA', 'PO-PSI', 'PO-KA', 'rTMS'
        ],
        prices={s: 0 for s in [
            'ECT', 'KA-ECT', 'IV-KA', 'IN-EKA', 'PO-PSI', 'PO-KA', 'rTMS'
        ]},
        effects_unit='QALYs',
        currency='A$',
        labels={
            'ECT': 'Standard ECT',
            'KA-ECT': 'Ketamine-Assisted ECT',
            'IV-KA': 'IV Ketamine',
            'IN-EKA': 'Intranasal Esketamine',
            'PO-PSI': 'Oral Psilocybin',
            'PO-KA': 'Oral Ketamine',
            'rTMS': 'rTMS',
        },
        jurisdictions=['AU', 'NZ']
    )


def load_psa_data(csv_path: Path, perspective: str, jurisdiction: str):
    """Load PSA data from CSV."""
    df = pd.read_csv(csv_path)
    config = create_ect_focused_config()

    return PSAData(
        table=df,
        config=config,
        perspective=perspective,
        jurisdiction=jurisdiction
    )


def run_cea_analysis(psa: PSAData, output_dir: Path, figures_dir: Path, logger: logging.Logger):
    """Run CEA analysis and generate outputs."""
    with AnalysisContext(logger, "cost_effectiveness_analysis"):
        logger.info("=" * 60)
        logger.info("Running Cost-Effectiveness Analysis (ECT-Focused)")
        logger.info("=" * 60)

        # Run deterministic CEA
        logger.info("1. Running deterministic CEA...")
        det_results = cea_engine.run_deterministic_cea(psa, lambda_threshold=50000)

        # Save results
        output_dir.mkdir(parents=True, exist_ok=True)
        det_results.deterministic.to_csv(output_dir / 'cea_deterministic.csv', index=False)
        det_results.incremental.to_csv(output_dir / 'cea_incremental.csv', index=False)
        det_results.frontier.to_csv(output_dir / 'cea_frontier.csv', index=False)
        logger.info("  ✓ Saved deterministic results")

        # Calculate CEAC
        logger.info("2. Calculating Cost-Effectiveness Acceptability Curve...")
        lambda_grid = cea_engine.build_lambda_grid(0, 150000, 5000)
        ceac_results = cea_engine.compute_ceac(psa, lambda_grid)
        ceac_results.ceac.to_csv(output_dir / 'ceac.csv', index=False)
        logger.info("  ✓ Saved CEAC results")

        # Calculate CEAF
        logger.info("3. Calculating Cost-Effectiveness Acceptability Frontier...")
        ceaf_results = cea_engine.compute_ceaf(psa, lambda_grid)
        ceaf_results.ceaf.to_csv(output_dir / 'ceaf.csv', index=False)
        logger.info("  ✓ Saved CEAF results")

        # Generate figures
        logger.info("4. Generating CEA figures...")
        figures_dir.mkdir(parents=True, exist_ok=True)

        # Prepare data for plotting
        costs_wide = psa.table.pivot(index='draw', columns='strategy', values='cost')
        effects_wide = psa.table.pivot(index='draw', columns='strategy', values='effect')

        # CE Plane
        try:
            cea_plots.plot_ce_plane(costs_wide, effects_wide, 'ECT', figures_dir / 'ce_plane.png', 50000)
            logger.info("  ✓ Generated CE plane")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate CE plane: {e}")

        # CEAC
        try:
            # Pivot CEAC data to wide format for plotting
            ceac_wide = ceac_results.ceac.pivot(index='lambda', columns='strategy', values='probability_optimal')
            cea_plots.plot_ceac(ceac_wide, figures_dir / 'ceac.png')
            logger.info("  ✓ Generated CEAC plot")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate CEAC plot: {e}")

        # CEAF
        try:
            # Rename column to match plot function expectations
            ceaf_plot_data = ceaf_results.ceaf.copy()
            ceaf_plot_data = ceaf_plot_data.rename(columns={'ceaf_strategy': 'optimal_strategy'})
            cea_plots.plot_ceaf(ceaf_plot_data, figures_dir / 'ceaf.png')
            logger.info("  ✓ Generated CEAF plot")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate CEAF plot: {e}")

        # INMB Distribution
        try:
            inmb_data = psa.table.copy()
            inmb_data['inmb'] = 50000 * inmb_data['effect'] - inmb_data['cost']
            inmb_pivot = inmb_data.pivot(index='draw', columns='strategy', values='inmb')

            cea_plots.plot_inmb_distribution(inmb_pivot, figures_dir / 'inmb_distribution.png')
            logger.info("  ✓ Generated INMB distribution plot")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate INMB distribution plot: {e}")

        return det_results, ceac_results, ceaf_results


def run_voi_analysis(psa: PSAData, output_dir: Path, figures_dir: Path, logger: logging.Logger):
    """Run VOI analysis and generate outputs."""
    with AnalysisContext(logger, "value_of_information_analysis"):
        logger.info("=" * 60)
        logger.info("Running Value of Information Analysis (ECT-Focused)")
        logger.info("=" * 60)

        # Calculate EVPI
        logger.info("1. Calculating Expected Value of Perfect Information...")
        lambda_grid = np.arange(0, 150000, 5000)

        # Estimate eligible TRD population by jurisdiction
        # TRD affects ~20-30% of MDD patients
        # Australia: ~3 million with MDD → ~750,000 TRD
        # New Zealand: ~500,000 with MDD → ~125,000 TRD
        # Using eligible population (severe TRD requiring intensive treatment): ~10% of TRD
        population_size = 75000 if psa.jurisdiction == 'AU' else 12500

        evpi_results = voi_engine.calculate_evpi(
            psa,
            lambda_grid,
            population_size=population_size,
            time_horizon=10,
            discount_rate=0.05,
            confidence_level=0.95
        )

        # Save results
        evpi_results.evpi.to_csv(output_dir / 'evpi.csv', index=False)
        evpi_results.population_evpi.to_csv(output_dir / 'population_evpi.csv', index=False)
        logger.info(f"  ✓ Saved EVPI results (population: {population_size:,})")

        # Calculate EVPPI
        logger.info("2. Calculating Expected Value of Partial Perfect Information...")
        # Generate parameter names for ECT-focused strategies
        strategy_params = {
            'IV-KA': 'iv_ketamine',
            'ECT': 'ect',
            'KA-ECT': 'ka_ect',
            'IN-EKA': 'esketamine',
            'PO-PSI': 'psilocybin',
            'PO-KA': 'oral_ketamine',
            'rTMS': 'rtms',
        }

        # Add cost and effect parameters for each strategy
        parameter_names = []
        for strategy, param_base in strategy_params.items():
            if strategy in psa.strategies:
                parameter_names.extend([f'cost_{param_base}', f'effect_{param_base}'])

        logger.info(f"  Analyzing {len(parameter_names)} parameters across {len(psa.strategies)} strategies")
        evppi_df = voi_engine.calculate_evppi(psa, parameter_names, lambda_grid)

        # Create parameter rankings (simplified)
        evppi_at_50k = evppi_df[evppi_df['lambda'] == 50000].groupby('parameter')['evppi'].mean().reset_index()
        evppi_at_50k = evppi_at_50k.sort_values('evppi', ascending=False).reset_index(drop=True)

        # Save EVPPI results
        evppi_df.to_csv(output_dir / 'evppi.csv', index=False)
        evppi_at_50k.to_csv(output_dir / 'parameter_rankings.csv', index=False)
        logger.info("  ✓ Saved EVPPI results")

        # Calculate VOI tornado data (parameter sensitivity analysis)
        logger.info("3. Running VOI Tornado Analysis...")
        voi_tornado_data = voi_engine.calculate_voi_tornado(
            psa, parameter_names, base_lambda=50000, population_size=1000000  # 1M population
        )

        voi_tornado_data.to_csv(output_dir / 'voi_tornado.csv', index=False)
        logger.info("  ✓ Saved VOI tornado data")

        # Generate figures
        logger.info("4. Generating VOI figures...")
        figures_dir.mkdir(parents=True, exist_ok=True)

        # EVPI curve
        try:
            # Rename columns to match plot function expectations
            evpi_plot_data = evpi_results.evpi.copy()
            evpi_plot_data = evpi_plot_data.rename(columns={'lambda': 'wtp', 'evpi_per_person': 'evpi'})
            voi_plots.plot_evpi_curve(evpi_plot_data, figures_dir / 'evpi_curve.png')
            logger.info("  ✓ Generated EVPI curve")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate EVPI curve: {e}")

        # EVPPI bars
        try:
            # Filter EVPPI data to WTP = 50000
            evppi_at_50k = evppi_df[evppi_df['lambda'] == 50000][['parameter', 'evppi']].reset_index(drop=True)
            voi_plots.plot_evppi_bars(evppi_at_50k, figures_dir / 'evppi_bars.png')
            logger.info("  ✓ Generated EVPPI bars")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate EVPPI bars: {e}")

        # VOI tornado
        try:
            # Data is already in correct format with 'population_evppi' column
            tornado_plot_data = voi_tornado_data.copy()
            voi_plots.plot_voi_tornado(tornado_plot_data, figures_dir / 'voi_tornado.png')
            logger.info("  ✓ Generated VOI tornado")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate VOI tornado: {e}")

        return evpi_results, evppi_df, voi_tornado_data


def run_dcea_analysis(psa: PSAData, output_dir: Path, figures_dir: Path, logger: logging.Logger):
    """Run DCEA analysis and generate outputs."""
    with AnalysisContext(logger, "distributional_cost_effectiveness_analysis"):
        logger.info("=" * 60)
        logger.info("Running Distributional Cost-Effectiveness Analysis (ECT-Focused)")
        logger.info("=" * 60)

        # For DCEA, we need subgroup data
        # Use proper distributional cost-effectiveness analysis
        logger.info("1. Calculating Atkinson Index...")

        # Run proper DCEA analysis
        dcea_result = dcea_engine.run_dcea(psa)

        logger.info(f"  ✓ Calculated Atkinson indices for {len(dcea_result.atkinson_index)} strategies")

        # Save results
        dcea_df = dcea_result.atkinson_index[['strategy', 'atkinson_index']].copy()
        dcea_df['ede_qalys'] = dcea_result.ede_qalys['ede_qalys']
        dcea_df.to_csv(output_dir / 'dcea_summary.csv', index=False)
        logger.info("  ✓ Saved DCEA results")

        logger.info("2. Generating DCEA figures...")
        figures_dir.mkdir(parents=True, exist_ok=True)

        # Atkinson index comparison
        try:
            # Rename column to match plot function expectations
            atkinson_plot_data = dcea_df.copy()
            atkinson_plot_data = atkinson_plot_data.rename(columns={'atkinson_index': 'atkinson'})
            dcea_plots.plot_atkinson_index(atkinson_plot_data, figures_dir / 'atkinson_index.png')
            logger.info("  ✓ Generated Atkinson index comparison")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate Atkinson index comparison: {e}")

        # Prepare data for DCEA plots
        total_qalys = psa.table.groupby('strategy')['effect'].mean().reset_index()
        total_qalys = total_qalys.set_index('strategy').T

        # Equity impact plane
        try:
            # Prepare inequality data (Atkinson index)
            inequality_data = dcea_df[['strategy', 'atkinson_index']].set_index('strategy').T

            dcea_plots.plot_equity_impact_plane(
                total_qalys,
                inequality_data,
                figures_dir / 'equity_impact_plane.png',
                'ECT'
            )
            logger.info("  ✓ Generated equity impact plane")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate equity impact plane: {e}")

        # EDE-QALYs comparison
        try:
            # Prepare EDE-QALYs data
            ede_data = dcea_df[['strategy', 'ede_qalys']].copy()

            # Prepare total QALYs data in the format expected by the plotting function
            total_qalys_formatted = pd.DataFrame({
                'strategy': total_qalys.columns,
                'total_qalys': total_qalys.iloc[0].values
            })

            dcea_plots.plot_ede_qalys(ede_data, total_qalys_formatted, figures_dir / 'ede_qalys.png')
            logger.info("  ✓ Generated EDE-QALYs comparison")
        except Exception as e:
            logger.error(f"  ✗ Failed to generate EDE-QALYs comparison: {e}")

        return dcea_df


def main():
    """Run complete ECT-Focused V4 analysis."""
    # Set up logging
    logger = setup_script_logging("run_v4_ect_focused_analysis")

    logger.info("=" * 60)
    logger.info("ECT-Focused V4 Analysis Pipeline")
    logger.info("=" * 60)

    # Setup paths
    data_path = Path('data/sample/psa_sample_AU_healthcare.csv')
    output_dir = Path('results/v4_ect_focused_test')
    figures_dir = Path('figures/v4_ect_focused_test')

    if not data_path.exists():
        logger.error(f"Sample data not found at {data_path}")
        logger.error("Run: python scripts/generate_sample_data.py")
        return 1

    # Load data
    logger.info(f"Loading PSA data from: {data_path}")
    psa = load_psa_data(data_path, perspective='healthcare', jurisdiction='AU')
    logger.info(f"  ✓ Loaded {len(psa.table)} rows")
    logger.info(f"  ✓ Strategies: {len(psa.strategies)}")
    logger.info(f"  ✓ Draws: {len(psa.draws)}")

    # Run analyses
    try:
        _cea_results = run_cea_analysis(psa, output_dir, figures_dir, logger)
        _voi_results = run_voi_analysis(psa, output_dir, figures_dir, logger)
        _dcea_results = run_dcea_analysis(psa, output_dir, figures_dir, logger)

        logger.info("=" * 60)
        logger.info("✓ ECT-Focused Analysis Complete!")
        logger.info("=" * 60)
        logger.info(f"Results saved to: {output_dir}")
        logger.info(f"Figures would be in: {figures_dir}")

        # List generated files
        logger.info("Generated files:")
        for file in sorted(output_dir.glob('*.csv')):
            logger.info(f"  ✓ {file.name}")

        return 0

    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())