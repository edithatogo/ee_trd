"""
V4 Input/Output Utilities

Consolidated and enhanced I/O utilities from V2 analysis_core.
Handles data loading, validation, and export for all V4 analyses.

Responsibilities:
- Load PSA CSVs and strategy configuration YAML
- Validate schema integrity across perspectives and strategies
- Load and validate input parameters with provenance tracking
- Compute price-adjusted costs where applicable
- Export results in multiple formats (CSV, JSON, publication-ready)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Any

import numpy as np
import pandas as pd
import yaml

# V4 therapy abbreviations from manuscript
V4_THERAPY_ABBREVIATIONS = {
    "ECT": "Standard Electroconvulsive Therapy",
    "KA-ECT": "Ketamine-Assisted ECT",
    "IV-KA": "Intravenous Ketamine",
    "IN-EKA": "Intranasal Esketamine",
    "PO-PSI": "Oral Psilocybin-Assisted Therapy",
    "PO-KA": "Oral Ketamine",
    "rTMS": "Repetitive Transcranial Magnetic Stimulation",
    "UC+Li": "Usual Care + Lithium Augmentation",
    "UC+AA": "Usual Care + Atypical Antipsychotic",
    "Usual Care": "Standard Care Comparator"
}

REQUIRED_PSA_COLUMNS = {"draw", "strategy", "cost", "effect", "perspective"}


@dataclass
class StrategyConfig:
    """Configuration for treatment strategies and analysis parameters."""
    
    base: str
    perspectives: List[str]
    strategies: List[str]
    prices: Dict[str, float]
    effects_unit: str
    currency: str
    labels: Dict[str, str] = field(default_factory=dict)
    jurisdictions: List[str] = field(default_factory=lambda: ["AU", "NZ"])
    
    @classmethod
    def from_yaml(cls, path: Path) -> "StrategyConfig":
        """Load strategy configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Strategy configuration missing at '{path}'")
        
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        
        required = {"base", "perspectives", "strategies", "prices", "effects_unit", "currency"}
        missing = required - set(data)
        if missing:
            raise KeyError(f"Strategy config missing keys: {', '.join(sorted(missing))}")
        
        # Validate therapy abbreviations
        strategies = list(data["strategies"])
        invalid_strategies = []
        for s in strategies:
            # Allow standard V4 abbreviations or step-care sequences
            if s not in V4_THERAPY_ABBREVIATIONS and not s.startswith("Step-care:"):
                invalid_strategies.append(s)
        
        if invalid_strategies:
            raise ValueError(
                f"Invalid therapy abbreviations: {invalid_strategies}. "
                f"Must use V4 manuscript abbreviations: {list(V4_THERAPY_ABBREVIATIONS.keys())} "
                f"or step-care sequences starting with 'Step-care:'"
            )
        
        return cls(
            base=data["base"],
            perspectives=list(data["perspectives"]),
            strategies=strategies,
            prices={k: float(v) for k, v in data["prices"].items()},
            effects_unit=str(data["effects_unit"]),
            currency=str(data["currency"]),
            labels={str(k): str(v) for k, v in (data.get("labels") or {}).items()},
            jurisdictions=list(data.get("jurisdictions", ["AU", "NZ"]))
        )
    
    def validate_therapy_names(self) -> None:
        """Ensure all strategies use correct V4 manuscript abbreviations."""
        for strategy in self.strategies:
            if strategy not in V4_THERAPY_ABBREVIATIONS and not strategy.startswith("Step-care:"):
                raise ValueError(
                    f"Strategy '{strategy}' not in V4 therapy abbreviations. "
                    f"Use: {list(V4_THERAPY_ABBREVIATIONS.keys())} or step-care sequences"
                )


@dataclass
class DataProvenance:
    """Provenance tracking for data sources."""
    source_file: str
    load_timestamp: str
    data_hash: str
    version: str = "1.0"
    description: Optional[str] = None
    author: Optional[str] = None
    processing_steps: List[str] = field(default_factory=list)
    validation_status: str = "pending"
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class PSAData:
    """Enhanced container for PSA data with metadata and provenance tracking."""

    table: pd.DataFrame
    config: StrategyConfig
    perspective: str
    jurisdiction: Optional[str] = None
    provenance: Optional[DataProvenance] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_cache: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def strategies(self) -> List[str]:
        """Get unique strategies in the PSA data."""
        return list(self.table["strategy"].unique())
    
    @property
    def draws(self) -> np.ndarray:
        """Get sorted array of draw identifiers."""
        return np.sort(self.table["draw"].unique())
    
    def validate(self) -> None:
        """Validate PSA data integrity."""
        # Check required columns
        missing = REQUIRED_PSA_COLUMNS - set(self.table.columns)
        if missing:
            raise KeyError(f"PSA data missing columns: {', '.join(sorted(missing))}")

        # Check for infinite or NaN values
        if self.table[["cost", "effect"]].isnull().any().any():
            raise ValueError("PSA data contains NaN values")

        if np.isinf(self.table[["cost", "effect"]].values).any():
            raise ValueError("PSA data contains infinite values")

        # Validate strategies match configuration
        data_strategies = set(self.strategies)
        config_strategies = set(self.config.strategies)

        # Allow PSA data to contain a subset of configured strategies (common in unit tests
        # or partial-sample PSA files). If strict matching is required, callers can pass
        # a 'strict_strategy_validation' flag in metadata to enforce equality.
        strict = bool(self.metadata.get('strict_strategy_validation', False)) if isinstance(self.metadata, dict) else False

        if strict:
            if data_strategies != config_strategies:
                raise ValueError(
                    f"Strategy mismatch. Data: {data_strategies}, Config: {config_strategies}"
                )
        else:
            # Data strategies must be a subset of the configured strategies
            if not data_strategies.issubset(config_strategies):
                raise ValueError(
                    f"PSA data contains unknown strategies: {data_strategies - config_strategies}. Config: {config_strategies}"
                )

    def add_provenance(self, source_file: str, data_hash: str, **kwargs) -> None:
        """Add provenance information to the PSA data."""
        from datetime import datetime

        if self.provenance is None:
            self.provenance = DataProvenance(
                source_file=source_file,
                load_timestamp=datetime.now().isoformat(),
                data_hash=data_hash,
                **kwargs
            )
        else:
            # Update existing provenance
            self.provenance.source_file = source_file
            self.provenance.load_timestamp = datetime.now().isoformat()
            self.provenance.data_hash = data_hash
            if kwargs:
                for key, value in kwargs.items():
                    if hasattr(self.provenance, key):
                        setattr(self.provenance, key, value)

    def update_metadata(self, key: str, value: Any) -> None:
        """Update metadata dictionary."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)

    def cache_validation_result(self, validation_type: str, result: Any) -> None:
        """Cache validation results for performance."""
        self.validation_cache[validation_type] = result

    def get_cached_validation(self, validation_type: str) -> Any:
        """Get cached validation result."""
        return self.validation_cache.get(validation_type)

    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the PSA data."""
        return {
            'total_draws': len(self.draws),
            'strategies': self.strategies,
            'perspective': self.perspective,
            'jurisdiction': self.jurisdiction,
            'columns': list(self.table.columns),
            'data_shape': self.table.shape,
            'memory_usage_mb': self.table.memory_usage(deep=True).sum() / 1024 / 1024,
            'has_provenance': self.provenance is not None,
            'metadata_keys': list(self.metadata.keys()),
            'validation_cache_size': len(self.validation_cache)
        }

    def filter_by_strategy(self, strategies: List[str]) -> 'PSAData':
        """Create a new PSAData object filtered to specific strategies."""
        filtered_table = self.table[self.table['strategy'].isin(strategies)].copy()

        if filtered_table.empty:
            raise ValueError(f"No data found for strategies: {strategies}")

        # Create new PSAData with filtered table
        filtered_psa = PSAData(
            table=filtered_table,
            config=self.config,
            perspective=self.perspective,
            jurisdiction=self.jurisdiction,
            provenance=self.provenance,
            metadata=self.metadata.copy(),
            validation_cache=self.validation_cache.copy()
        )

        # Update provenance if present
        if filtered_psa.provenance:
            filtered_psa.provenance.processing_steps.append(
                f"Filtered to strategies: {strategies}"
            )

        return filtered_psa

    def get_cost_effectiveness_data(self) -> pd.DataFrame:
        """Get cost-effectiveness data in standard format for analysis."""
        return self.table[['draw', 'strategy', 'cost', 'effect']].copy()

    def compute_data_hash(self) -> str:
        """Compute hash of the PSA data for provenance tracking."""
        import hashlib

        # Create a deterministic representation of the data
        data_str = str(self.table.shape) + str(sorted(self.table.columns.tolist()))

        # Add first and last few values for uniqueness
        sample_data = self.table.head(5).to_string() + self.table.tail(5).to_string()
        data_str += sample_data

        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def export_metadata(self, output_path: Path) -> None:
        """Export PSA data metadata and provenance to JSON."""
        metadata_dict = {
            'data_summary': self.get_data_summary(),
            'provenance': {
                'source_file': self.provenance.source_file if self.provenance else None,
                'load_timestamp': self.provenance.load_timestamp if self.provenance else None,
                'data_hash': self.provenance.data_hash if self.provenance else None,
                'version': self.provenance.version if self.provenance else None,
                'description': self.provenance.description if self.provenance else None,
                'author': self.provenance.author if self.provenance else None,
                'processing_steps': self.provenance.processing_steps if self.provenance else [],
                'validation_status': self.provenance.validation_status if self.provenance else None,
                'validation_errors': self.provenance.validation_errors if self.provenance else []
            } if self.provenance else None,
            'metadata': self.metadata,
            'validation_cache': self.validation_cache
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(metadata_dict, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Loading Functions
# ---------------------------------------------------------------------------


def normalise_perspective(perspective: str, available: Iterable[str]) -> str:
    """Normalize perspective name to match available options."""
    items = list(available)
    if perspective in items:
        return perspective
    
    # Try case-insensitive match with underscores removed
    lookup = {p.lower().replace("_", ""): p for p in items}
    key = perspective.lower().replace("_", "")
    if key in lookup:
        return lookup[key]
    
    raise ValueError(f"Perspective '{perspective}' not found. Available: {items}")


def load_psa(path: Path, strategies_yaml: Optional[Path] = None) -> pd.DataFrame:
    """Load PSA data from CSV file and normalize strategy names to canonical keys.

    Args:
        path: Path to PSA CSV file
        strategies_yaml: Optional path to `config/strategies.yml` for canonical strategy list

    Returns:
        DataFrame with normalized `strategy` column
    """
    if not path.exists():
        raise FileNotFoundError(f"PSA file not found at '{path}'")

    df = pd.read_csv(path)

    # Check required columns
    missing = REQUIRED_PSA_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"PSA file missing columns: {', '.join(sorted(missing))}")

    # Replace infinite values with NaN
    df = df.replace([np.inf, -np.inf], np.nan)

    # Build canonical strategy mapping from config
    if strategies_yaml is None:
        strategies_yaml = Path('config/strategies.yml')

    try:
        cfg = StrategyConfig.from_yaml(Path(strategies_yaml))
        individual_strategies = [s for s in cfg.strategies if not s.startswith('Step-care:')]
    except Exception:
        cfg = None
        individual_strategies = []

    # Create mapping: placeholders and lowercased variants -> canonical key
    canonical_map: Dict[str, str] = {}
    if cfg is not None:
        for s in individual_strategies:
            canonical_map[s] = s
            canonical_map[s.lower()] = s

        # Map common labels (labels field) and V4 abbreviations if provided
        for s in individual_strategies:
            label = cfg.labels.get(s)
            if label:
                canonical_map[label] = s
                canonical_map[label.lower()] = s
            # also map manuscript full name to abbreviation if present
            full = V4_THERAPY_ABBREVIATIONS.get(s)
            if full:
                canonical_map[full] = s
                canonical_map[full.lower()] = s

        # Support placeholder names like 'Therapy A', 'Therapy B', ... mapping to canonical strategies by order
        for i, s in enumerate(individual_strategies):
            ph = f"Therapy {chr(ord('A') + i)}"
            canonical_map[ph] = s
            canonical_map[ph.lower()] = s

    # Normalize strategy column values
    def _map_strategy_value(v: Any) -> Any:
        if pd.isna(v):
            return v
        key = str(v)
        return canonical_map.get(key, canonical_map.get(key.lower(), key))

    if 'strategy' in df.columns:
        df['strategy'] = df['strategy'].apply(_map_strategy_value)

    return df


def load_strategies_config_mapping() -> Dict[str, str]:
    """Load strategy configuration and return mapping of strategy names."""
    config = StrategyConfig.from_yaml(Path('config/strategies.yml'))
    # Return only individual strategies (exclude step-care sequences)
    individual_strategies = {s: s for s in config.strategies if not s.startswith('Step-care:')}
    return individual_strategies


def load_analysis_inputs(
    psa_path: Path,
    config_path: Path,
    perspective: str,
    jurisdiction: Optional[str] = None
) -> PSAData:
    """
    Load and validate all inputs for analysis.
    
    Args:
        psa_path: Path to PSA CSV file
        config_path: Path to strategy configuration YAML
        perspective: Economic perspective (health_system or societal)
        jurisdiction: Geographic jurisdiction (AU or NZ)
    
    Returns:
        PSAData object with validated data and configuration
    """
    # Load configuration
    config = StrategyConfig.from_yaml(config_path)
    config.validate_therapy_names()
    
    # Normalize perspective
    perspective = normalise_perspective(perspective, config.perspectives)
    
    # Load PSA data
    psa_df = load_psa(psa_path)
    
    # Filter by perspective
    psa_df = psa_df[psa_df["perspective"] == perspective].copy()
    
    if psa_df.empty:
        raise ValueError(f"No data found for perspective '{perspective}'")
    
    # Filter by jurisdiction if specified
    if jurisdiction is not None:
        if "jurisdiction" in psa_df.columns:
            psa_df = psa_df[psa_df["jurisdiction"] == jurisdiction].copy()
            if psa_df.empty:
                raise ValueError(f"No data found for jurisdiction '{jurisdiction}'")
    
    # Create PSAData object
    psa_data = PSAData(
        table=psa_df,
        config=config,
        perspective=perspective,
        jurisdiction=jurisdiction
    )
    
    # Validate
    psa_data.validate()
    
    return psa_data


def assert_strategy_presence(psa: PSAData, strategy: str) -> None:
    """Assert that a strategy is present in the PSA data."""
    if strategy not in psa.strategies:
        raise ValueError(
            f"Strategy '{strategy}' not found in PSA data. "
            f"Available: {psa.strategies}"
        )


def filter_perspective(psa_data: pd.DataFrame, perspective: str) -> pd.DataFrame:
    """
    Filter PSA data to a specific perspective.
    
    Args:
        psa_data: PSA dataframe with perspective column
        perspective: Perspective to filter for
        
    Returns:
        Filtered dataframe
        
    Raises:
        ValueError: If no draws found for perspective
    """
    filtered = psa_data[psa_data["perspective"] == perspective]
    if len(filtered) == 0:
        raise ValueError(f"No PSA draws for perspective '{perspective}'")
    return filtered


def align_draws(psa_data: pd.DataFrame, base_draws: np.ndarray, report: List[str]) -> pd.DataFrame:
    """
    Align PSA draws to match base draws, reindexing if necessary.
    
    Args:
        psa_data: PSA dataframe with draw column
        base_draws: Array of base draw numbers
        report: List to append alignment messages to
        
    Returns:
        Reindexed PSA dataframe
    """
    unique_psa_draws = sorted(psa_data["draw"].unique())
    unique_base_draws = sorted(np.unique(base_draws))
    
    if unique_psa_draws != unique_base_draws:
        report.append(f"Reindexing draws from {unique_psa_draws} to {unique_base_draws}")
        # Create mapping from old draws to new draws
        draw_mapping = dict(zip(unique_psa_draws, unique_base_draws))
        psa_data = psa_data.copy()
        psa_data["draw"] = psa_data["draw"].map(draw_mapping)
    
    return psa_data


# ---------------------------------------------------------------------------
# Export Functions
# ---------------------------------------------------------------------------


def save_results(
    data: pd.DataFrame,
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save analysis results to CSV with optional metadata.
    
    Args:
        data: Results dataframe
        output_path: Output file path
        metadata: Optional metadata dictionary
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    data.to_csv(output_path, index=False)
    
    # Save metadata if provided
    if metadata is not None:
        metadata_path = output_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)


def save_results_multiformat(
    data: pd.DataFrame,
    output_path: Path,
    formats: Optional[List[str]] = None
) -> None:
    """
    Save results in multiple formats.
    
    Args:
        data: Results dataframe
        output_path: Base output path (without extension)
        formats: List of formats ('csv', 'json', 'xlsx')
    """
    if formats is None:
        formats = ['csv']
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for fmt in formats:
        if fmt == 'csv':
            data.to_csv(output_path.with_suffix('.csv'), index=False)
        elif fmt == 'json':
            data.to_json(output_path.with_suffix('.json'), orient='records', indent=2)
        elif fmt == 'xlsx':
            data.to_excel(output_path.with_suffix('.xlsx'), index=False)
        else:
            raise ValueError(f"Unsupported format: {fmt}")


def save_cma_results(
    results: Any,
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save CMA analysis results to JSON with metadata.

    Args:
        results: CMA analysis results
        output_path: Output file path
        metadata: Optional additional metadata
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert results to dictionary
    # Build a display mapping from canonical config labels and manuscript abbreviations
    try:
        cfg = StrategyConfig.from_yaml(Path('config/strategies.yml'))
        individual_strategies = [s for s in cfg.strategies if not s.startswith('Step-care:')]
    except Exception:
        # Fallback if config can't be loaded
        cfg = None
        individual_strategies = []

    display_map: Dict[str, str] = {}
    if cfg is not None:
        for s in individual_strategies:
            display_map[s] = cfg.labels.get(s) or V4_THERAPY_ABBREVIATIONS.get(s) or s

        # Support placeholder names like 'Therapy A', 'Therapy B', ... mapping to canonical strategies by order
        for i, s in enumerate(individual_strategies):
            ph = f"Therapy {chr(ord('A') + i)}"
            display_map.setdefault(ph, display_map.get(s, s))
            display_map.setdefault(ph.lower(), display_map.get(s, s))

    def map_value(v: Any) -> Any:
        if v is None:
            return v
        try:
            key = str(v)
        except Exception:
            return v
        return display_map.get(key, display_map.get(key.lower(), key))

    # Helper to map dataframe columns if present
    def _map_df(df):
        if df is None:
            return None
        df = df.copy()
        for col in ('strategy', 'Strategy', 'focal'):
            if col in df.columns:
                df[col] = df[col].apply(map_value)
        return df

    # Helper to safely convert dataframe to dict
    def _safe_to_dict(df):
        if df is None:
            return []
        mapped_df = _map_df(df)
        return mapped_df.to_dict('records') if mapped_df is not None else []

    results_dict = {
        'equivalence_tests': [
            {
                'strategy_a': map_value(test.strategy_a),
                'strategy_b': map_value(test.strategy_b),
                'effect_diff': test.effect_diff,
                'effect_diff_ci_lower': test.effect_diff_ci_lower,
                'effect_diff_ci_upper': test.effect_diff_ci_upper,
                'equivalence_margin': test.equivalence_margin,
                'equivalent': test.equivalent,
                'tost_p_value': test.p_value
            }
            for test in results.equivalence_tests
        ],
        'cost_minimization_results': _safe_to_dict(results.cost_minimization_results),
        'bootstrap_results': _safe_to_dict(results.bootstrap_results),
        'sensitivity_analysis': _safe_to_dict(results.sensitivity_analysis),
        'summary_stats': {
            **(results.summary_stats or {}),
        }
    }

    # Map any top-level summary_stats strategy names
    if 'least_costly_strategy' in results_dict['summary_stats']:
        results_dict['summary_stats']['least_costly_strategy'] = map_value(results_dict['summary_stats']['least_costly_strategy'])

    # Add metadata if provided
    if metadata:
        results_dict['metadata'] = metadata

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2, default=str)


def load_strategies_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load strategies configuration from YAML file.
    
    Args:
        path: Path to strategies YAML file. If None, uses default config/strategies.yml
    
    Returns:
        Dictionary of strategy configurations with strategy names as keys
    """
    if path is None:
        path = Path(__file__).parent.parent.parent / "config" / "strategies.yml"
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Convert strategies list to dictionary with strategy names as keys
    strategies_dict = {}
    if 'strategies' in config and isinstance(config['strategies'], list):
        for strategy in config['strategies']:
            strategies_dict[strategy] = {
                'name': strategy,
                'price': config.get('prices', {}).get(strategy, 0),
                'label': config.get('labels', {}).get(strategy, strategy)
            }
    
    return strategies_dict
