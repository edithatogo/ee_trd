"""
Engine Registry System

This module provides the central registry for discovering, registering, and managing
analysis engines in the V4 health economic evaluation framework.

The registry system enables:
- Dynamic discovery of available engines
- Engine capability detection and filtering
- Centralized engine configuration management
- Plugin-style engine loading
- Version compatibility checking
"""

import importlib
import inspect
import logging
from typing import Dict, List, Optional, Type, Any, Set, Union
from pathlib import Path
import sys
from dataclasses import dataclass

from .base import BaseAnalysisEngine, EngineMetadata, AnalysisType, EngineCapabilities

# Configure logger for this module
logger = logging.getLogger(__name__)


@dataclass
class EngineInfo:
    """Container for engine registration information."""
    name: str
    class_type: Type[BaseAnalysisEngine]
    metadata: EngineMetadata
    module_path: str
    is_loaded: bool = False
    load_error: Optional[str] = None


class EngineRegistry:
    """
    Central registry for managing analysis engines.

    This class provides methods for discovering, registering, and retrieving
    analysis engines, along with capability filtering and version management.
    """

    def __init__(self):
        """Initialize the engine registry."""
        self._engines: Dict[str, EngineInfo] = {}
        self._capability_index: Dict[EngineCapabilities, Set[str]] = {}
        self._type_index: Dict[AnalysisType, Set[str]] = {}
        self._search_paths: List[Path] = []
        self._auto_discovery_enabled = True

        # Initialize capability and type indexes
        for capability in EngineCapabilities:
            self._capability_index[capability] = set()
        for analysis_type in AnalysisType:
            self._type_index[analysis_type] = set()

        logger.info("Initialized engine registry")

    def register_engine(self, engine_class: Type[BaseAnalysisEngine],
                       metadata: Optional[EngineMetadata] = None,
                       force: bool = False) -> bool:
        """
        Register an analysis engine.

        Args:
            engine_class: Engine class to register
            metadata: Optional metadata for the engine
            force: If True, overwrite existing registration

        Returns:
            True if registration was successful

        Raises:
            ValueError: If engine is invalid or already registered
        """
        # Validate engine class
        if not inspect.isclass(engine_class):
            raise ValueError("Engine must be a class")

        if not issubclass(engine_class, BaseAnalysisEngine):
            raise ValueError("Engine class must inherit from BaseAnalysisEngine")

        # Get engine name
        engine_name = getattr(engine_class, '_engine_name', engine_class.__name__)

        # Check for existing registration
        if engine_name in self._engines and not force:
            raise ValueError(f"Engine '{engine_name}' is already registered")

        # Get metadata
        if metadata is None:
            try:
                # Try to get metadata from class attribute
                metadata = getattr(engine_class, '_engine_metadata', None)
                if metadata is None:
                    # Create instance to get default metadata
                    temp_instance = engine_class({})
                    metadata = temp_instance.get_metadata()
                    temp_instance.cleanup()
            except Exception as e:
                logger.warning(f"Could not get metadata for {engine_name}: {e}")
                metadata = self._create_default_metadata(engine_name, engine_class)

        # Create engine info
        engine_info = EngineInfo(
            name=engine_name,
            class_type=engine_class,
            metadata=metadata,
            module_path=engine_class.__module__
        )

        # Register engine
        self._engines[engine_name] = engine_info

        # Update indexes
        self._update_indexes(engine_name, metadata)

        logger.info(f"Registered engine: {engine_name}")
        return True

    def unregister_engine(self, engine_name: str) -> bool:
        """
        Unregister an analysis engine.

        Args:
            engine_name: Name of the engine to unregister

        Returns:
            True if engine was unregistered
        """
        if engine_name not in self._engines:
            logger.warning(f"Engine '{engine_name}' is not registered")
            return False

        # Remove from indexes
        engine_info = self._engines[engine_name]
        self._remove_from_indexes(engine_name, engine_info.metadata)

        # Remove from registry
        del self._engines[engine_name]

        logger.info(f"Unregistered engine: {engine_name}")
        return True

    def get_engine(self, engine_name: str) -> Optional[EngineInfo]:
        """
        Get information about a registered engine.

        Args:
            engine_name: Name of the engine

        Returns:
            EngineInfo if found, None otherwise
        """
        return self._engines.get(engine_name)

    def get_engine_class(self, engine_name: str) -> Optional[Type[BaseAnalysisEngine]]:
        """
        Get the class for a registered engine.

        Args:
            engine_name: Name of the engine

        Returns:
            Engine class if found, None otherwise
        """
        engine_info = self._engines.get(engine_name)
        return engine_info.class_type if engine_info else None

    def list_engines(self) -> List[str]:
        """
        List all registered engine names.

        Returns:
            List of registered engine names
        """
        return list(self._engines.keys())

    def list_engines_by_type(self, analysis_type: AnalysisType) -> List[str]:
        """
        List engines that support a specific analysis type.

        Args:
            analysis_type: Type of analysis

        Returns:
            List of engine names supporting the analysis type
        """
        return list(self._type_index.get(analysis_type, set()))

    def list_engines_by_capability(self, capability: EngineCapabilities) -> List[str]:
        """
        List engines that support a specific capability.

        Args:
            capability: Engine capability

        Returns:
            List of engine names supporting the capability
        """
        return list(self._capability_index.get(capability, set()))

    def find_engines(self,
                    analysis_type: Optional[AnalysisType] = None,
                    capabilities: Optional[List[EngineCapabilities]] = None,
                    require_all_capabilities: bool = True) -> List[str]:
        """
        Find engines matching specified criteria.

        Args:
            analysis_type: Required analysis type (optional)
            capabilities: Required capabilities (optional)
            require_all_capabilities: If True, engines must have all capabilities

        Returns:
            List of matching engine names
        """
        candidates = set(self._engines.keys())

        # Filter by analysis type
        if analysis_type:
            type_engines = self._type_index.get(analysis_type, set())
            candidates = candidates.intersection(type_engines)

        # Filter by capabilities
        if capabilities:
            if require_all_capabilities:
                # Engine must have all specified capabilities
                for capability in capabilities:
                    capability_engines = self._capability_index.get(capability, set())
                    candidates = candidates.intersection(capability_engines)
            else:
                # Engine must have at least one of the specified capabilities
                capability_engines = set()
                for capability in capabilities:
                    capability_engines.update(self._capability_index.get(capability, set()))
                candidates = candidates.intersection(capability_engines)

        return list(candidates)

    def add_search_path(self, path: Union[str, Path]) -> None:
        """
        Add a path to search for engines.

        Args:
            path: Directory path to search
        """
        path = Path(path)
        if path not in self._search_paths:
            self._search_paths.append(path)
            logger.info(f"Added search path: {path}")

    def enable_auto_discovery(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic engine discovery.

        Args:
            enabled: Whether to enable auto-discovery
        """
        self._auto_discovery_enabled = enabled
        logger.info(f"Auto-discovery {'enabled' if enabled else 'disabled'}")

    def discover_engines(self, search_paths: Optional[List[Union[str, Path]]] = None) -> int:
        """
        Discover and register available engines.

        Args:
            search_paths: Optional list of paths to search (uses registered paths if None)

        Returns:
            Number of engines discovered
        """
        if not self._auto_discovery_enabled:
            logger.info("Auto-discovery is disabled")
            return 0

        paths_to_search = search_paths or self._search_paths
        discovered_count = 0

        for search_path in paths_to_search:
            discovered_count += self._discover_engines_in_path(Path(search_path))

        logger.info(f"Discovered {discovered_count} engines")
        return discovered_count

    def _discover_engines_in_path(self, search_path: Path) -> int:
        """
        Discover engines in a specific path.

        Args:
            search_path: Path to search for engines

        Returns:
            Number of engines discovered in this path
        """
        if not search_path.exists():
            logger.warning(f"Search path does not exist: {search_path}")
            return 0

        discovered_count = 0

        # Search for Python files in the path
        if search_path.is_file() and search_path.suffix == '.py':
            discovered_count += self._discover_engines_in_file(search_path)
        elif search_path.is_dir():
            # Search recursively in directory
            for py_file in search_path.rglob('*.py'):
                if py_file.name.startswith('__'):
                    continue  # Skip __init__.py and similar files
                discovered_count += self._discover_engines_in_file(py_file)

        return discovered_count

    def _discover_engines_in_file(self, file_path: Path) -> int:
        """
        Discover engines in a specific Python file.

        Args:
            file_path: Path to Python file to search

        Returns:
            Number of engines discovered in this file
        """
        discovered_count = 0

        try:
            # Add the directory to sys.path temporarily
            file_dir = str(file_path.parent)
            if file_dir not in sys.path:
                sys.path.insert(0, file_dir)

            # Import the module
            module_name = file_path.stem
            module = importlib.import_module(module_name)

            # Find engine classes in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, BaseAnalysisEngine) and
                    obj != BaseAnalysisEngine):

                    try:
                        self.register_engine(obj)
                        discovered_count += 1
                        logger.debug(f"Discovered engine: {obj.__name__} in {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to register discovered engine {obj.__name__}: {e}")

        except Exception as e:
            logger.warning(f"Failed to discover engines in {file_path}: {e}")
        finally:
            # Clean up sys.path
            if file_dir in sys.path:
                sys.path.remove(file_dir)

        return discovered_count

    def _update_indexes(self, engine_name: str, metadata: EngineMetadata) -> None:
        """Update internal indexes when registering an engine."""
        # Update type index
        self._type_index[metadata.analysis_type].add(engine_name)

        # Update capability index
        for capability in metadata.capabilities:
            self._capability_index[capability].add(engine_name)

    def _remove_from_indexes(self, engine_name: str, metadata: EngineMetadata) -> None:
        """Remove engine from internal indexes."""
        # Remove from type index
        self._type_index[metadata.analysis_type].discard(engine_name)

        # Remove from capability index
        for capability in metadata.capabilities:
            self._capability_index[capability].discard(engine_name)

    def _create_default_metadata(self, engine_name: str,
                                engine_class: Type[BaseAnalysisEngine]) -> EngineMetadata:
        """Create default metadata for an engine."""
        return EngineMetadata(
            name=engine_name,
            version="1.0.0",
            description=f"Auto-generated metadata for {engine_name}",
            author="Unknown",
            analysis_type=AnalysisType.CUA,  # Default to CUA
            capabilities=[]
        )

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the registry.

        Returns:
            Dictionary with registry statistics
        """
        return {
            'total_engines': len(self._engines),
            'engines_by_type': {
                analysis_type.value: len(engine_names)
                for analysis_type, engine_names in self._type_index.items()
            },
            'engines_by_capability': {
                capability.value: len(engine_names)
                for capability, engine_names in self._capability_index.items()
            },
            'search_paths': [str(path) for path in self._search_paths],
            'auto_discovery_enabled': self._auto_discovery_enabled
        }

    def clear_registry(self) -> None:
        """Clear all registered engines."""
        self._engines.clear()
        for capability in EngineCapabilities:
            self._capability_index[capability].clear()
        for analysis_type in AnalysisType:
            self._type_index[analysis_type].clear()

        logger.info("Cleared engine registry")


# Global registry instance
_global_registry = EngineRegistry()


def get_registry() -> EngineRegistry:
    """Get the global engine registry instance."""
    return _global_registry


def discover_engines(search_paths: Optional[List[Union[str, Path]]] = None) -> int:
    """
    Convenience function to discover engines using the global registry.

    Args:
        search_paths: Optional list of paths to search

    Returns:
        Number of engines discovered
    """
    return _global_registry.discover_engines(search_paths)


def register_engine(engine_class: Type[BaseAnalysisEngine],
                   metadata: Optional[EngineMetadata] = None) -> bool:
    """
    Convenience function to register an engine with the global registry.

    Args:
        engine_class: Engine class to register
        metadata: Optional metadata for the engine

    Returns:
        True if registration was successful
    """
    return _global_registry.register_engine(engine_class, metadata)
