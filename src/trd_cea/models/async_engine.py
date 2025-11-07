"""
Asynchronous Engine Support

This module provides asynchronous execution capabilities for analysis engines,
enabling parallel processing and improved performance for computationally
intensive health economic analyses.

The async engine system provides:
- Non-blocking engine execution
- Concurrent analysis processing
- Resource pooling and management
- Timeout and cancellation support
- Progress tracking for long-running analyses
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import asynccontextmanager

from .base import BaseAnalysisEngine, EngineInput, EngineOutput, EngineCapabilities, EngineMetadata

# Configure logger for this module
logger = logging.getLogger(__name__)


@dataclass
class AsyncExecutionConfig:
    """Configuration for asynchronous engine execution."""
    max_workers: int = 4
    timeout: Optional[float] = None
    enable_progress_tracking: bool = True
    progress_interval: float = 1.0
    enable_cancellation: bool = True
    resource_limits: Optional[Dict[str, Any]] = None


@dataclass
class AsyncExecutionResult:
    """Result container for asynchronous execution."""
    success: bool
    output: Optional[EngineOutput]
    execution_time: float
    error: Optional[str] = None
    cancelled: bool = False
    progress: Optional[float] = None


class ProgressTracker:
    """Tracks progress for asynchronous operations."""

    def __init__(self, interval: float = 1.0):
        """Initialize progress tracker."""
        self.interval = interval
        self._progress: float = 0.0
        self._last_update = 0.0
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[float], None]] = []

    def update_progress(self, progress: float) -> None:
        """Update progress value."""
        with self._lock:
            self._progress = max(0.0, min(1.0, progress))
            current_time = time.time()

            if current_time - self._last_update >= self.interval:
                self._last_update = current_time
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(self._progress)
                    except Exception as e:
                        logger.warning(f"Progress callback error: {e}")

    def get_progress(self) -> float:
        """Get current progress value."""
        with self._lock:
            return self._progress

    def add_callback(self, callback: Callable[[float], None]) -> None:
        """Add progress callback."""
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[float], None]) -> None:
        """Remove progress callback."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)


class AsyncEngineWrapper:
    """
    Wrapper for executing analysis engines asynchronously.

    This class provides async capabilities for engines that don't natively
    support asynchronous execution, enabling parallel processing and
    improved resource utilization.
    """

    def __init__(self, engine: BaseAnalysisEngine, config: Optional[AsyncExecutionConfig] = None):
        """
        Initialize async engine wrapper.

        Args:
            engine: Engine to wrap
            config: Async execution configuration
        """
        self.engine = engine
        self.config = config or AsyncExecutionConfig()
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._progress_tracker = ProgressTracker(self.config.progress_interval)
        self._cancelled = False
        self._lock = threading.Lock()

        logger.info(f"Initialized async wrapper for {engine.metadata.name} engine")

    def cancel(self) -> None:
        """Cancel current execution."""
        if not self.config.enable_cancellation:
            logger.warning("Cancellation not enabled for this engine")
            return

        with self._lock:
            self._cancelled = True
            logger.info(f"Cancelled execution for {self.engine.metadata.name} engine")

    def is_cancelled(self) -> bool:
        """Check if execution is cancelled."""
        with self._lock:
            return self._cancelled

    def get_progress(self) -> float:
        """Get current progress."""
        return self._progress_tracker.get_progress()

    def add_progress_callback(self, callback: Callable[[float], None]) -> None:
        """Add progress callback."""
        self._progress_tracker.add_callback(callback)

    def remove_progress_callback(self, callback: Callable[[float], None]) -> None:
        """Remove progress callback."""
        self._progress_tracker.remove_callback(callback)

    async def run_async(self, input_data: EngineInput) -> AsyncExecutionResult:
        """
        Run engine asynchronously.

        Args:
            input_data: Input data for the analysis

        Returns:
            AsyncExecutionResult with results and metadata
        """
        start_time = time.time()
        self._cancelled = False

        try:
            # Submit to thread pool
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                self._executor,
                self._run_sync,
                input_data
            )

            # Wait for completion with timeout
            if self.config.timeout:
                result = await asyncio.wait_for(future, timeout=self.config.timeout)
            else:
                result = await future

            execution_time = time.time() - start_time
            logger.info(f"Async execution completed in {execution_time:.2f}s")

            return AsyncExecutionResult(
                success=result['success'],
                output=result['output'],
                execution_time=execution_time,
                error=result.get('error'),
                cancelled=result.get('cancelled', False),
                progress=result.get('progress')
            )

        except asyncio.TimeoutError:
            logger.error(f"Async execution timed out after {self.config.timeout}s")
            return AsyncExecutionResult(
                success=False,
                output=None,
                execution_time=time.time() - start_time,
                error=f"Execution timed out after {self.config.timeout}s",
                cancelled=False
            )
        except Exception as e:
            logger.error(f"Async execution failed: {e}")
            return AsyncExecutionResult(
                success=False,
                output=None,
                execution_time=time.time() - start_time,
                error=str(e),
                cancelled=False
            )

    async def sync_run(self, input_data: EngineInput) -> AsyncExecutionResult:
        """
        Coroutine-compatible synchronous-run alias.

        This method exists because some tests call `asyncio.run(async_wrapper.sync_run(...))`
        to execute the wrapped engine sequentially within an async context.
        It simply delegates to `run_async` to execute the work in the executor.
        """
        return await self.run_async(input_data)

    def _run_sync(self, input_data: EngineInput) -> Dict[str, Any]:
        """
        Run engine synchronously in thread pool.

        Args:
            input_data: Input data for analysis

        Returns:
            Dictionary with execution results
        """
        try:
            # Check for cancellation
            if self.is_cancelled():
                return {
                    'success': False,
                    'output': None,
                    'error': 'Execution cancelled',
                    'cancelled': True,
                    'progress': 0.0
                }

            # Update progress
            self._progress_tracker.update_progress(0.1)

            # Initialize engine if needed
            if not hasattr(self.engine, '_is_initialized') or not self.engine._is_initialized:
                self.engine.initialize()

            # Check for cancellation again
            if self.is_cancelled():
                return {
                    'success': False,
                    'output': None,
                    'error': 'Execution cancelled',
                    'cancelled': True,
                    'progress': 0.2
                }

            # Update progress
            self._progress_tracker.update_progress(0.3)

            # Run analysis
            output = self.engine.run(input_data)

            # Update progress
            self._progress_tracker.update_progress(1.0)

            return {
                'success': len(output.errors) == 0,
                'output': output,
                'error': None,
                'cancelled': False,
                'progress': 1.0
            }

        except Exception as e:
            logger.error(f"Synchronous execution failed: {e}")
            return {
                'success': False,
                'output': None,
                'error': str(e),
                'cancelled': False,
                'progress': 0.0
            }

    async def run_multiple_async(self,
                                inputs: List[EngineInput],
                                max_concurrent: Optional[int] = None) -> List[AsyncExecutionResult]:
        """
        Run multiple analyses concurrently.

        Args:
            inputs: List of input data for analyses
            max_concurrent: Maximum number of concurrent executions

        Returns:
            List of AsyncExecutionResult objects
        """
        if max_concurrent is None:
            max_concurrent = self.config.max_workers

        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(input_data: EngineInput) -> AsyncExecutionResult:
            async with semaphore:
                return await self.run_async(input_data)

        # Create tasks
        tasks = [run_with_semaphore(input_data) for input_data in inputs]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
                processed_results.append(AsyncExecutionResult(
                    success=False,
                    output=None,
                    execution_time=0.0,
                    error=str(result),
                    cancelled=False
                ))
            else:
                processed_results.append(result)

        return processed_results

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._executor.shutdown(wait=True)
            logger.info(f"Cleaned up async wrapper for {self.engine.metadata.name} engine")
        except Exception as e:
            logger.warning(f"Error during async wrapper cleanup: {e}")


class AsyncAnalysisEngine(BaseAnalysisEngine):
    """
    Base class for analysis engines that support native asynchronous execution.

    Engines that inherit from this class can override async methods to provide
    native async support, which is more efficient than using the wrapper.
    """

    def __init__(self, config: Dict[str, Any], metadata: Optional["EngineMetadata"] = None):
        """Initialize async engine."""
        super().__init__(config, metadata)

        # Add async capability if not present
        if EngineCapabilities.ASYNC_EXECUTION not in self.metadata.capabilities:
            self.metadata.capabilities.append(EngineCapabilities.ASYNC_EXECUTION)

    async def run_async(self, input_data: EngineInput) -> EngineOutput:
        """
        Run analysis asynchronously (native implementation).

        Args:
            input_data: Input data for analysis

        Returns:
            EngineOutput with results
        """
        # Default implementation uses sync method in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, input_data)

    async def initialize_async(self) -> None:
        """
        Initialize engine asynchronously.

        Default implementation calls sync initialize in thread pool.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.initialize)

    async def cleanup_async(self) -> None:
        """
        Clean up engine resources asynchronously.

        Default implementation calls sync cleanup in thread pool.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.cleanup)


@asynccontextmanager
async def async_engine_context(engine: BaseAnalysisEngine,
                              config: Optional[AsyncExecutionConfig] = None):
    """
    Async context manager for engine execution.

    Args:
        engine: Engine to execute
        config: Async execution configuration

    Yields:
        AsyncEngineWrapper instance
    """
    if isinstance(engine, AsyncAnalysisEngine):
        # Native async engine
        try:
            await engine.initialize_async()
            yield engine
        finally:
            await engine.cleanup_async()
    else:
        # Wrap with async wrapper
        wrapper = AsyncEngineWrapper(engine, config)
        try:
            yield wrapper
        finally:
            wrapper.cleanup()


def create_async_wrapper(engine: BaseAnalysisEngine,
                        config: Optional[AsyncExecutionConfig] = None) -> AsyncEngineWrapper:
    """
    Create an async wrapper for an engine.

    Args:
        engine: Engine to wrap
        config: Async execution configuration

    Returns:
        AsyncEngineWrapper instance
    """
    return AsyncEngineWrapper(engine, config)


async def run_engines_concurrently(engines: List[BaseAnalysisEngine],
                                  inputs: List[EngineInput],
                                  config: Optional[AsyncExecutionConfig] = None) -> List[AsyncExecutionResult]:
    """
    Run multiple engines concurrently.

    Args:
        engines: List of engines to run
        inputs: List of input data (must match engines length)
        config: Async execution configuration

    Returns:
        List of AsyncExecutionResult objects
    """
    if len(engines) != len(inputs):
        raise ValueError("Number of engines must match number of inputs")

    # Create wrappers for non-async engines
    wrappers = []
    for engine in engines:
        if isinstance(engine, AsyncAnalysisEngine):
            wrappers.append(engine)
        else:
            wrappers.append(AsyncEngineWrapper(engine, config))

    # Run concurrently
    tasks = []
    for wrapper, input_data in zip(wrappers, inputs):
        if isinstance(wrapper, AsyncAnalysisEngine):
            tasks.append(wrapper.run_async(input_data))
        else:
            tasks.append(wrapper.run_async(input_data))

    # Wait for all results
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert to AsyncExecutionResult format
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append(AsyncExecutionResult(
                success=False,
                output=None,
                execution_time=0.0,
                error=str(result),
                cancelled=False
            ))
        elif isinstance(result, EngineOutput):
            processed_results.append(AsyncExecutionResult(
                success=len(result.errors) == 0,
                output=result,
                execution_time=result.execution_time or 0.0,
                error=result.errors[0] if result.errors else None,
                cancelled=False
            ))
        else:
            # Already an AsyncExecutionResult
            processed_results.append(result)

    return processed_results
