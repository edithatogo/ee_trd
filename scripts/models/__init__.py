"""
Analysis Engines Module

This module provides the core engine abstraction layer for the V4 health economic
evaluation framework. It includes base classes, interfaces, and utilities for
creating modular, extensible analysis engines.

The engine system enables:
- Pluggable analysis components
- Standardized input/output contracts
- Asynchronous execution support
- Performance monitoring and validation
- Automatic documentation generation

Classes:
    BaseAnalysisEngine: Abstract base class for all analysis engines
    EngineRegistry: Central registry for engine discovery and management
    AsyncEngineWrapper: Wrapper for asynchronous engine execution

Functions:
    discover_engines: Dynamic discovery of available engines
    create_engine_instance: Factory function for engine creation
    validate_engine_outputs: Standardized output validation
"""

from .base import BaseAnalysisEngine, EngineCapabilities, EngineMetadata
from .registry import EngineRegistry, discover_engines
from .async_engine import AsyncEngineWrapper

__all__ = [
    'BaseAnalysisEngine',
    'EngineCapabilities',
    'EngineMetadata',
    'EngineRegistry',
    'discover_engines',
    'AsyncEngineWrapper'
]

# Version information for the engines module
__version__ = '1.0.0'
__author__ = 'V4 Health Economic Framework'
