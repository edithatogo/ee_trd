"""
V4 Configuration Management

Unified configuration system for V4 analyses.
Handles loading and validation of all configuration files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

import yaml


@dataclass
class WTPConfig:
    """Willingness-to-pay configuration."""
    min: float
    max: float
    step: float
    default: float
    thresholds: List[float]


@dataclass
class PSAConfig:
    """PSA configuration."""
    iterations: int
    seed: int
    convergence_check: bool
    min_iterations: int


@dataclass
class DiscountConfig:
    """Discount rate configuration."""
    costs: float
    effects: float
    costs_nz: float
    effects_nz: float


@dataclass
class FigureStandards:
    """Publication figure standards."""
    resolution: int
    formats: List[str]
    dimensions: Dict[str, Any]
    fonts: Dict[str, Any]
    colors: Dict[str, str]


@dataclass
class PublicationConfig:
    """Publication standards configuration."""
    journal: str
    figure_standards: FigureStandards


class EngineExecutionMode(Enum):
    """Engine execution mode enumeration."""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


@dataclass
class EngineConfig:
    """Engine-specific configuration."""
    enabled: bool = True
    execution_mode: EngineExecutionMode = EngineExecutionMode.SYNCHRONOUS
    max_workers: int = 4
    timeout: Optional[float] = None
    memory_limit: Optional[int] = None  # MB
    auto_discovery: bool = True
    search_paths: List[str] = field(default_factory=list)
    cache_results: bool = True
    validate_outputs: bool = True
    progress_tracking: bool = True


@dataclass
class AsyncConfig:
    """Asynchronous execution configuration."""
    max_concurrent_engines: int = 4
    engine_timeout: Optional[float] = None
    progress_interval: float = 1.0
    enable_cancellation: bool = True
    resource_monitoring: bool = True
    retry_failed_engines: bool = True
    max_retries: int = 3


@dataclass
class PerformanceConfig:
    """Performance monitoring configuration."""
    enable_profiling: bool = True
    profile_memory: bool = True
    profile_cpu: bool = True
    benchmark_enabled: bool = False
    performance_thresholds: Dict[str, float] = field(default_factory=dict)
    memory_warning_threshold: float = 0.8  # 80% of available memory


@dataclass
class V4Config:
    """Complete V4 configuration."""

    version: str
    data_paths: Dict[str, str]
    strategies_yaml: str
    perspectives: List[str]
    jurisdictions: List[str]
    wtp: WTPConfig
    psa: PSAConfig
    discount: DiscountConfig
    time_horizon: Dict[str, Any]
    output: Dict[str, Any]
    seed: int
    performance: Dict[str, Any]
    validation: Dict[str, bool]
    modules: Dict[str, bool]
    sensitivity: Dict[str, bool]
    subgroups: Dict[str, bool]
    indigenous: Dict[str, Any]
    equity: Dict[str, Any]
    publication: PublicationConfig
    engines: EngineConfig = field(default_factory=EngineConfig)
    async_config: AsyncConfig = field(default_factory=AsyncConfig)
    performance_monitoring: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "V4Config":
        """Load V4 configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse WTP configuration
        wtp = WTPConfig(
            min=data['wtp']['min'],
            max=data['wtp']['max'],
            step=data['wtp']['step'],
            default=data['wtp']['default'],
            thresholds=data['wtp']['thresholds']
        )
        
        # Parse PSA configuration
        psa = PSAConfig(
            iterations=data['psa']['iterations'],
            seed=data['psa']['seed'],
            convergence_check=data['psa']['convergence_check'],
            min_iterations=data['psa']['min_iterations']
        )
        
        # Parse discount configuration
        discount = DiscountConfig(
            costs=data['discount']['costs'],
            effects=data['discount']['effects'],
            costs_nz=data['discount']['costs_nz'],
            effects_nz=data['discount']['effects_nz']
        )
        
        # Parse publication configuration
        pub_data = data['publication']
        fig_standards = FigureStandards(
            resolution=pub_data['figure_standards']['resolution'],
            formats=pub_data['figure_standards']['formats'],
            dimensions=pub_data['figure_standards']['dimensions'],
            fonts=pub_data['figure_standards']['fonts'],
            colors=pub_data['figure_standards']['colors']
        )
        
        publication = PublicationConfig(
            journal=pub_data['journal'],
            figure_standards=fig_standards
        )

        # Parse engine configuration
        engines_data = data.get('engines', {})
        engines = EngineConfig(
            enabled=engines_data.get('enabled', True),
            execution_mode=EngineExecutionMode(engines_data.get('execution_mode', 'synchronous')),
            max_workers=engines_data.get('max_workers', 4),
            timeout=engines_data.get('timeout'),
            memory_limit=engines_data.get('memory_limit'),
            auto_discovery=engines_data.get('auto_discovery', True),
            search_paths=engines_data.get('search_paths', []),
            cache_results=engines_data.get('cache_results', True),
            validate_outputs=engines_data.get('validate_outputs', True),
            progress_tracking=engines_data.get('progress_tracking', True)
        )

        # Parse async configuration
        async_data = data.get('async', {})
        async_config = AsyncConfig(
            max_concurrent_engines=async_data.get('max_concurrent_engines', 4),
            engine_timeout=async_data.get('engine_timeout'),
            progress_interval=async_data.get('progress_interval', 1.0),
            enable_cancellation=async_data.get('enable_cancellation', True),
            resource_monitoring=async_data.get('resource_monitoring', True),
            retry_failed_engines=async_data.get('retry_failed_engines', True),
            max_retries=async_data.get('max_retries', 3)
        )

        # Parse performance monitoring configuration
        perf_data = data.get('performance_monitoring', {})
        performance_monitoring = PerformanceConfig(
            enable_profiling=perf_data.get('enable_profiling', True),
            profile_memory=perf_data.get('profile_memory', True),
            profile_cpu=perf_data.get('profile_cpu', True),
            benchmark_enabled=perf_data.get('benchmark_enabled', False),
            performance_thresholds=perf_data.get('performance_thresholds', {}),
            memory_warning_threshold=perf_data.get('memory_warning_threshold', 0.8)
        )

        return cls(
            version=data['version'],
            data_paths=data['data'],
            strategies_yaml=data['strategies_yaml'],
            perspectives=data['perspectives'],
            jurisdictions=data['jurisdictions'],
            wtp=wtp,
            psa=psa,
            discount=discount,
            time_horizon=data['time_horizon'],
            output=data['output'],
            seed=data['seed'],
            performance=data['performance'],
            validation=data['validation'],
            modules=data['modules'],
            sensitivity=data['sensitivity'],
            subgroups=data['subgroups'],
            indigenous=data['indigenous'],
            equity=data['equity'],
            publication=publication,
            engines=engines,
            async_config=async_config,
            performance_monitoring=performance_monitoring
        )
    
    def get_discount_rate(self, jurisdiction: str, rate_type: str = 'costs') -> float:
        """Get discount rate for specific jurisdiction."""
        if jurisdiction == 'NZ':
            return self.discount.costs_nz if rate_type == 'costs' else self.discount.effects_nz
        else:
            return self.discount.costs if rate_type == 'costs' else self.discount.effects
    
    def get_wtp_grid(self) -> List[float]:
        """Generate WTP grid from configuration."""
        import numpy as np
        return [float(x) for x in np.arange(self.wtp.min, self.wtp.max + self.wtp.step, self.wtp.step)]
    
    def is_module_enabled(self, module: str) -> bool:
        """Check if analysis module is enabled."""
        return self.modules.get(module, False)

    def is_engine_enabled(self) -> bool:
        """Check if engine system is enabled."""
        return self.engines.enabled

    def get_engine_execution_mode(self) -> EngineExecutionMode:
        """Get the configured engine execution mode."""
        return self.engines.execution_mode

    def should_use_async_engines(self) -> bool:
        """Check if async engine execution is enabled."""
        return (self.engines.enabled and
                self.engines.execution_mode in [EngineExecutionMode.ASYNCHRONOUS, EngineExecutionMode.PARALLEL])

    def get_engine_search_paths(self) -> List[Path]:
        """Get engine search paths as Path objects."""
        return [Path(path) for path in self.engines.search_paths]

    def should_cache_engine_results(self) -> bool:
        """Check if engine result caching is enabled."""
        return self.engines.cache_results

    def should_validate_engine_outputs(self) -> bool:
        """Check if engine output validation is enabled."""
        return self.engines.validate_outputs

    def get_max_concurrent_engines(self) -> int:
        """Get maximum number of concurrent engines."""
        return self.async_config.max_concurrent_engines

    def get_engine_timeout(self) -> Optional[float]:
        """Get engine timeout setting."""
        return self.engines.timeout or self.async_config.engine_timeout

    def should_retry_failed_engines(self) -> bool:
        """Check if failed engines should be retried."""
        return self.async_config.retry_failed_engines

    def get_max_engine_retries(self) -> int:
        """Get maximum number of engine retries."""
        return self.async_config.max_retries

    def is_performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled."""
        return self.performance_monitoring.enable_profiling

    def should_profile_memory(self) -> bool:
        """Check if memory profiling is enabled."""
        return self.performance_monitoring.profile_memory

    def should_profile_cpu(self) -> bool:
        """Check if CPU profiling is enabled."""
        return self.performance_monitoring.profile_cpu

    def get_memory_warning_threshold(self) -> float:
        """Get memory warning threshold."""
        return self.performance_monitoring.memory_warning_threshold


def load_v4_config(config_path: Optional[Path] = None) -> V4Config:
    """
    Load V4 configuration.
    
    Args:
        config_path: Path to configuration file (defaults to config/v4_analysis_defaults.yml)
    
    Returns:
        V4Config object
    """
    if config_path is None:
        config_path = Path("config/v4_analysis_defaults.yml")
    
    return V4Config.from_yaml(config_path)


def load_journal_standards(journal_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load journal-specific publication standards.
    
    Args:
        journal_name: Journal name (defaults to Australian and New Zealand Journal of Psychiatry)
    
    Returns:
        Dictionary with journal standards
    """
    standards_path = Path("config/journal_standards.yml")
    
    if not standards_path.exists():
        raise FileNotFoundError(f"Journal standards file not found: {standards_path}")
    
    with open(standards_path, 'r') as f:
        all_standards = yaml.safe_load(f)
    
    if journal_name is None:
        journal_name = "australian_nz_psychiatry"
    
    # Normalize journal name
    journal_key = journal_name.lower().replace(" ", "_").replace("-", "_")
    
    if journal_key not in all_standards:
        # Fall back to generic standards
        return all_standards.get('generic', {})
    
    return all_standards[journal_key]


def validate_config(config: V4Config) -> List[str]:
    """
    Validate V4 configuration.
    
    Args:
        config: V4Config object
    
    Returns:
        List of validation warnings (empty if all valid)
    """
    warnings = []
    
    # Check WTP parameters
    if config.wtp.min >= config.wtp.max:
        warnings.append("WTP min must be less than max")
    
    if config.wtp.step <= 0:
        warnings.append("WTP step must be positive")
    
    # Check PSA parameters
    if config.psa.iterations < config.psa.min_iterations:
        warnings.append(f"PSA iterations ({config.psa.iterations}) less than minimum ({config.psa.min_iterations})")
    
    # Check discount rates
    for rate in [config.discount.costs, config.discount.effects, 
                 config.discount.costs_nz, config.discount.effects_nz]:
        if rate < 0 or rate > 1:
            warnings.append(f"Discount rate {rate} outside valid range [0, 1]")
    
    # Check data paths exist
    for name, path in config.data_paths.items():
        if not Path(path).exists():
            warnings.append(f"Data file not found: {path}")

    # Check engine configuration
    if config.engines.enabled:
        if config.engines.max_workers < 1:
            warnings.append("Engine max_workers must be at least 1")

        if config.engines.timeout and config.engines.timeout <= 0:
            warnings.append("Engine timeout must be positive")

        if config.engines.memory_limit and config.engines.memory_limit <= 0:
            warnings.append("Engine memory_limit must be positive")

        # Check search paths exist
        for path in config.engines.search_paths:
            if not Path(path).exists():
                warnings.append(f"Engine search path not found: {path}")

    # Check async configuration
    if config.should_use_async_engines():
        if config.async_config.max_concurrent_engines < 1:
            warnings.append("Max concurrent engines must be at least 1")

        if config.async_config.max_retries < 0:
            warnings.append("Max retries cannot be negative")

        if config.async_config.progress_interval <= 0:
            warnings.append("Progress interval must be positive")

    # Check performance monitoring configuration
    if config.performance_monitoring.enable_profiling:
        if config.performance_monitoring.memory_warning_threshold <= 0 or config.performance_monitoring.memory_warning_threshold > 1:
            warnings.append("Memory warning threshold must be between 0 and 1")

        # Check performance thresholds are positive
        for threshold_name, threshold_value in config.performance_monitoring.performance_thresholds.items():
            if threshold_value <= 0:
                warnings.append(f"Performance threshold '{threshold_name}' must be positive")

    return warnings
