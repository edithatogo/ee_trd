"""
Base Analysis Engine Classes

This module defines the abstract base classes and interfaces for all analysis engines
in the V4 health economic evaluation framework.

The base engine system provides:
- Standardized interfaces for all analysis operations
- Consistent input/output contracts
- Built-in validation and error handling
- Performance monitoring capabilities
- Metadata tracking for provenance and reproducibility
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from enum import Enum
import time
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Enumeration of supported analysis types."""
    CUA = "cost_utility_analysis"
    DCEA = "distributional_cost_effectiveness_analysis"
    VOI = "value_of_information"
    BIA = "budget_impact_analysis"
    DSA = "deterministic_sensitivity_analysis"
    PSA = "probabilistic_sensitivity_analysis"
    NMA = "network_meta_analysis"
    MCDA = "multi_criteria_decision_analysis"
    SUBGROUP = "subgroup_analysis"
    SCENARIO = "scenario_analysis"


class EngineCapabilities(Enum):
    """Enumeration of engine capabilities."""
    ASYNC_EXECUTION = "async_execution"
    PARALLEL_PROCESSING = "parallel_processing"
    MEMORY_EFFICIENT = "memory_efficient"
    STREAMING_OUTPUT = "streaming_output"
    INCREMENTAL_RESULTS = "incremental_results"
    CACHING = "caching"
    PERSISTENCE = "persistence"
    VALIDATION = "validation"


@dataclass
class EngineMetadata:
    """Metadata container for engine information and capabilities."""
    name: str
    version: str
    description: str
    author: str
    analysis_type: AnalysisType
    capabilities: List[EngineCapabilities] = field(default_factory=list)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    created_date: Optional[str] = None
    last_modified: Optional[str] = None


@dataclass
class EngineInput:
    """Standardized input container for analysis engines."""
    data: Any
    config: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class EngineOutput:
    """Standardized output container for analysis engines."""
    results: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None


class BaseAnalysisEngine(ABC):
    """
    Abstract base class for all analysis engines in the V4 framework.

    This class defines the standard interface that all analysis engines must implement,
    providing consistent behavior for initialization, execution, validation, and
    metadata management.
    """

    def __init__(self, config: Dict[str, Any], metadata: Optional[EngineMetadata] = None):
        """
        Initialize the analysis engine.

        Args:
            config: Configuration dictionary for engine parameters
            metadata: Optional metadata describing the engine
        """
        self.config = config
        self.metadata = metadata or self._get_default_metadata()
        self._execution_history: List[Dict[str, Any]] = []
        self._is_initialized = False

        # Validate configuration
        self._validate_config()

        logger.info(f"Initialized {self.metadata.name} engine v{self.metadata.version}")

    @abstractmethod
    def _get_default_metadata(self) -> EngineMetadata:
        """
        Return the default metadata for this engine.

        Returns:
            EngineMetadata instance with engine information
        """
        pass

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the engine configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    def _validate_input(self, input_data: EngineInput) -> None:
        """
        Validate input data for the analysis.

        Args:
            input_data: Input data to validate

        Raises:
            ValueError: If input data is invalid
        """
        pass

    @abstractmethod
    def _run_analysis(self, input_data: EngineInput) -> Any:
        """
        Execute the core analysis logic.

        Args:
            input_data: Validated input data for analysis

        Returns:
            Raw analysis results
        """
        pass

    def initialize(self) -> None:
        """
        Initialize the engine and prepare for analysis.

        This method should be called before running any analyses.
        """
        if self._is_initialized:
            logger.warning("Engine already initialized")
            return

        try:
            self._initialize_engine()
            self._is_initialized = True
            logger.info(f"Successfully initialized {self.metadata.name} engine")
        except Exception as e:
            logger.error(f"Failed to initialize {self.metadata.name} engine: {e}")
            raise

    @abstractmethod
    def _initialize_engine(self) -> None:
        """
        Perform engine-specific initialization.

        This method should handle any setup required for the engine to function,
        such as loading models, initializing caches, or setting up external connections.
        """
        pass

    def run(self, input_data: EngineInput) -> EngineOutput:
        """
        Execute the analysis with standardized input/output handling.

        Args:
            input_data: Input data for the analysis

        Returns:
            EngineOutput containing results and metadata

        Raises:
            RuntimeError: If engine is not initialized
            ValueError: If input validation fails
        """
        # Auto-initialize for convenience in tests / interactive usage
        if not self._is_initialized:
            logger.info(f"{self.metadata.name} engine not initialized: auto-initializing before run()")
            try:
                self.initialize()
            except Exception as e:
                raise RuntimeError(f"Failed to auto-initialize engine: {e}")

        # Start timing
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            # If tests or callers pass a raw pandas.DataFrame (instead of PSAData-like
            # container), wrap it in a lightweight compatibility object that exposes
            # `.table`, `.strategies`, `.draws` and proxies DataFrame attributes.
            try:
                import pandas as _pd
            except Exception:
                _pd = None

            if _pd is not None and isinstance(input_data.data, _pd.DataFrame):
                df = input_data.data

                class _PSADataLike:
                    def __init__(self, df, perspective=None):
                        self.table = df
                        # Derive perspective from input config where possible
                        self.perspective = perspective or (getattr(df, 'perspective', None) if hasattr(df, 'perspective') else None) or 'health_system'

                    @property
                    def strategies(self):
                        return list(self.table['strategy'].unique())

                    @property
                    def draws(self):
                        return _pd.sort_values(self.table['draw'].unique()) if hasattr(_pd, 'sort_values') else list(sorted(self.table['draw'].unique()))

                    def __getattr__(self, item):
                        # Delegate to underlying DataFrame where reasonable
                        return getattr(self.table, item)

                    def __bool__(self):
                        # Treat as truthy in boolean contexts to avoid ambiguous DataFrame truth
                        return True

                input_data = EngineInput(
                    data=_PSADataLike(df, perspective=input_data.config.get('perspective') if isinstance(input_data.config, dict) else None),
                    config=input_data.config,
                    metadata=input_data.metadata,
                    parameters=input_data.parameters
                )

            # Validate input
            self._validate_input(input_data)

            # Run analysis
            results = self._run_analysis(input_data)

            # Calculate execution metrics
            execution_time = time.time() - start_time
            memory_usage = self._get_memory_usage() - start_memory

            # Create output
            output = EngineOutput(
                results=results,
                metadata={
                    'engine_name': self.metadata.name,
                    'engine_version': self.metadata.version,
                    'execution_timestamp': time.time(),
                    'input_hash': self._hash_input(input_data),
                    **(input_data.metadata or {})
                },
                execution_time=execution_time,
                memory_usage=memory_usage
            )

            # Record execution
            self._record_execution(input_data, output)

            logger.info(f"Successfully completed {self.metadata.name} analysis in {execution_time:.2f}s")
            return output

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Analysis failed after {execution_time:.2f}s: {e}")

            # Return error output
            return EngineOutput(
                results=None,
                metadata={
                    'engine_name': self.metadata.name,
                    'engine_version': self.metadata.version,
                    'execution_timestamp': time.time(),
                    'error': str(e)
                },
                errors=[str(e)],
                execution_time=execution_time
            )

    def _get_memory_usage(self) -> float:
        """
        Get current memory usage in MB.

        Returns:
            Memory usage in MB, or 0 if unable to determine
        """
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0

    def _hash_input(self, input_data: EngineInput) -> str:
        """
        Generate a hash of the input data for reproducibility tracking.

        Args:
            input_data: Input data to hash

        Returns:
            String hash of the input data
        """
        import hashlib
        import json

        # Create a normalized representation of the input
        input_dict = {
            'data_type': str(type(input_data.data)),
            'config': input_data.config,
            'parameters': input_data.parameters or {}
        }

        # Convert to JSON string for consistent hashing
        input_str = json.dumps(input_dict, sort_keys=True)

        return hashlib.sha256(input_str.encode()).hexdigest()[:16]

    def _record_execution(self, input_data: EngineInput, output: EngineOutput) -> None:
        """
        Record execution details for history tracking.

        Args:
            input_data: Input data used in the execution
            output: Output generated by the execution
        """
        execution_record = {
            'timestamp': time.time(),
            'input_hash': self._hash_input(input_data),
            'execution_time': output.execution_time,
            'memory_usage': output.memory_usage,
            'success': len(output.errors) == 0,
            'warnings_count': len(output.warnings),
            'errors_count': len(output.errors)
        }

        self._execution_history.append(execution_record)

        # Keep only last 100 executions to prevent memory bloat
        if len(self._execution_history) > 100:
            self._execution_history = self._execution_history[-100:]

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get the execution history for this engine.

        Returns:
            List of execution records
        """
        return self._execution_history.copy()

    def get_capabilities(self) -> List[EngineCapabilities]:
        """
        Get the capabilities supported by this engine.

        Returns:
            List of engine capabilities
        """
        return self.metadata.capabilities

    def supports_capability(self, capability: EngineCapabilities) -> bool:
        """
        Check if the engine supports a specific capability.

        Args:
            capability: Capability to check

        Returns:
            True if capability is supported
        """
        return capability in self.metadata.capabilities

    def get_metadata(self) -> EngineMetadata:
        """
        Get the engine metadata.

        Returns:
            Engine metadata
        """
        return self.metadata

    def cleanup(self) -> None:
        """
        Clean up engine resources.

        This method should be called when the engine is no longer needed
        to free up any resources it may be holding.
        """
        try:
            self._cleanup_engine()
            self._is_initialized = False
            logger.info(f"Cleaned up {self.metadata.name} engine")
        except Exception as e:
            logger.warning(f"Error during {self.metadata.name} engine cleanup: {e}")

    @abstractmethod
    def _cleanup_engine(self) -> None:
        """
        Perform engine-specific cleanup.

        This method should handle any cleanup required when the engine
        is no longer needed, such as closing files, connections, or
        freeing large data structures.
        """
        pass


def create_engine_instance(engine_class: Type[BaseAnalysisEngine],
                          config: Dict[str, Any],
                          metadata: Optional[EngineMetadata] = None) -> BaseAnalysisEngine:
    """
    Factory function for creating engine instances.

    Args:
        engine_class: Class of the engine to create
        config: Configuration for the engine
        metadata: Optional metadata for the engine

    Returns:
        Configured engine instance

    Raises:
        ValueError: If engine_class is not a valid engine class
    """
    if not issubclass(engine_class, BaseAnalysisEngine):
        raise ValueError("Engine class must inherit from BaseAnalysisEngine")

    return engine_class(config=config, metadata=metadata)


def validate_engine_outputs(engine: BaseAnalysisEngine, outputs: EngineOutput) -> bool:
    """
    Validate engine outputs against expected schema.

    Args:
        engine: Engine that produced the outputs
        outputs: Outputs to validate

    Returns:
        True if outputs are valid

    Raises:
        ValueError: If outputs are invalid
    """
    if outputs.results is None and len(outputs.errors) == 0:
        raise ValueError("Engine produced no results and no errors")

    if engine.metadata.output_schema:
        # Additional schema validation could be implemented here
        # using libraries like pydantic or marshmallow
        pass

    return True
