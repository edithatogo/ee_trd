"""
Logging utilities for V4 health economic evaluation pipeline.

This module provides utility functions for logging setup, progress tracking,
and structured logging across all analysis scripts.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, Optional, Any
from contextlib import contextmanager

from .logging_config import LoggingConfig, setup_analysis_logging, get_default_logging_config


class ProgressTracker:
    """Tracks and logs progress for long-running analyses."""

    def __init__(self, logger: logging.Logger, total_steps: int, description: str = "Analysis"):
        """
        Initialize progress tracker.

        Args:
            logger: Logger instance to use for progress reporting
            total_steps: Total number of steps in the analysis
            description: Description of the analysis being tracked
        """
        self.logger = logger
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
        self.last_logged_progress = -1

    def update(self, step: int, message: str = "", force_log: bool = False) -> None:
        """
        Update progress and log if significant progress made.

        Args:
            step: Current step number (0-based)
            message: Optional message to include with progress
            force_log: Force logging even if progress hasn't changed significantly
        """
        self.current_step = min(step, self.total_steps)
        progress = self.current_step / self.total_steps

        # Only log if progress changed significantly (>1%) or forced
        progress_percent = int(progress * 100)
        if force_log or progress_percent > self.last_logged_progress:
            self.last_logged_progress = progress_percent

            elapsed = time.time() - self.start_time
            _eta = (elapsed / progress) - elapsed if progress > 0 else 0

            log_message = f"{self.description}: Step {self.current_step}/{self.total_steps}"
            if message:
                log_message += f" - {message}"

            # Use custom progress logging if available, otherwise use info
            if hasattr(self.logger, 'log_progress'):
                self.logger.log_progress(progress, log_message)  # type: ignore
            else:
                self.logger.info(f"{log_message} [{progress_percent:.1f}% complete]")

    def complete(self, message: str = "Analysis completed") -> None:
        """
        Mark progress as complete.

        Args:
            message: Completion message
        """
        elapsed = time.time() - self.start_time
        self.update(self.total_steps, f"{message} (took {elapsed:.1f}s)", force_log=True)


class AnalysisContext:
    """Context manager for analysis logging with automatic start/complete messages."""

    def __init__(self, logger: logging.Logger, analysis_type: str, **kwargs):
        """
        Initialize analysis context.

        Args:
            logger: Logger instance
            analysis_type: Type of analysis being performed
            **kwargs: Additional context data
        """
        self.logger = logger
        self.analysis_type = analysis_type
        self.context_data = kwargs
        self.start_time = None

    def __enter__(self) -> AnalysisContext:
        """Enter analysis context and log start."""
        self.start_time = time.time()

        # Log analysis start
        if hasattr(self.logger, 'log_analysis_start'):
            self.logger.log_analysis_start(self.analysis_type, extra=self.context_data)
        else:
            self.logger.info(f"Starting {self.analysis_type}", extra={'analysis_type': self.analysis_type})

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit analysis context and log completion or error."""
        elapsed = time.time() - self.start_time if self.start_time else 0

        if exc_type is not None:
            # Log error with context
            error_msg = f"Error in {self.analysis_type} after {elapsed:.1f}s: {str(exc_val)}"
            if hasattr(self.logger, 'log_analysis_error'):
                self.logger.log_analysis_error(self.analysis_type, exc_val, extra=self.context_data)
            else:
                self.logger.error(error_msg, exc_info=True, extra={'analysis_type': self.analysis_type})
        else:
            # Log successful completion
            complete_msg = f"Completed {self.analysis_type} in {elapsed:.1f}s"
            if hasattr(self.logger, 'log_analysis_complete'):
                self.logger.log_analysis_complete(self.analysis_type, extra=self.context_data)
            else:
                self.logger.info(complete_msg, extra={'analysis_type': self.analysis_type})


def create_analysis_logger(name: str, config: Optional[LoggingConfig] = None) -> logging.Logger:
    """
    Create a logger for analysis scripts with proper configuration.

    Args:
        name: Logger name (typically script name)
        config: Logging configuration (uses defaults if None)

    Returns:
        Configured logger instance
    """
    if config is None:
        config = get_default_logging_config()

    adapter = setup_analysis_logging(name, config)

    # Return the underlying logger for compatibility
    return adapter.logger


def log_analysis_results(logger: logging.Logger, results: Dict[str, Any],
                        analysis_type: str = "analysis") -> None:
    """
    Log analysis results in a structured format.

    Args:
        logger: Logger instance
        results: Results dictionary to log
        analysis_type: Type of analysis for context
    """
    # Log summary statistics
    if 'summary' in results:
        summary = results['summary']
        if hasattr(logger, 'log_progress'):
            logger.log_progress(1.0, f"{analysis_type} results summary", extra={'data': summary})
        else:
            logger.info(f"{analysis_type} results: {summary}", extra={'analysis_type': analysis_type, 'data': summary})

    # Log key metrics if available
    key_metrics = {}
    for key in ['nmb', 'icer', 'cost_savings', 'probability', 'rank']:
        if key in results:
            key_metrics[key] = results[key]

    if key_metrics:
        if hasattr(logger, 'log_progress'):
            logger.log_progress(1.0, f"{analysis_type} key metrics", extra={'data': key_metrics})
        else:
            logger.info(f"{analysis_type} metrics: {key_metrics}",
                       extra={'analysis_type': analysis_type, 'data': key_metrics})


def log_data_summary(logger: logging.Logger, data: Any, name: str = "data",
                    analysis_type: str = "analysis") -> None:
    """
    Log a summary of data being processed.

    Args:
        logger: Logger instance
        data: Data to summarize (DataFrame, dict, etc.)
        name: Name of the data for logging
        analysis_type: Type of analysis for context
    """
    summary = {}

    try:
        if hasattr(data, 'shape'):  # pandas DataFrame/Series
            summary.update({
                'type': type(data).__name__,
                'shape': str(data.shape),
                'columns': len(data.columns) if hasattr(data, 'columns') else 'N/A'
            })
        elif isinstance(data, dict):
            summary.update({
                'type': 'dict',
                'keys': len(data),
                'key_sample': list(data.keys())[:5]  # First 5 keys
            })
        elif isinstance(data, (list, tuple)):
            summary.update({
                'type': type(data).__name__,
                'length': len(data),
                'item_type': type(data[0]).__name__ if data else 'empty'
            })
        else:
            summary.update({
                'type': type(data).__name__,
                'str_repr': str(data)[:100]  # First 100 chars
            })

        if hasattr(logger, 'log_progress'):
            logger.log_progress(0.0, f"Loaded {name}: {summary}", extra={'data': summary})
        else:
            logger.info(f"Loaded {name}: {summary}",
                       extra={'analysis_type': analysis_type, 'data': summary})

    except Exception as e:
        # If summarization fails, just log the type and error
        logger.warning(f"Could not summarize {name}: {str(e)}",
                      extra={'analysis_type': analysis_type})


def log_error_with_context(logger: logging.Logger, error: Exception,
                          context: Dict[str, Any], analysis_type: str = "analysis") -> None:
    """
    Log an error with additional context information.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context data
        analysis_type: Type of analysis for context
    """
    error_context = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context
    }

    if hasattr(logger, 'log_analysis_error'):
        logger.log_analysis_error(analysis_type, error, extra=context)
    else:
        logger.error(f"Error in {analysis_type}: {str(error)} - Context: {context}",
                    exc_info=True, extra={'analysis_type': analysis_type, 'data': error_context})


@contextmanager
def analysis_step_context(logger: logging.Logger, step_name: str, analysis_type: str = "analysis"):
    """
    Context manager for logging individual analysis steps.

    Args:
        logger: Logger instance
        step_name: Name of the step being performed
        analysis_type: Type of analysis for context

    Yields:
        None
    """
    step_context = {'step': step_name}

    if hasattr(logger, 'log_analysis_start'):
        logger.log_analysis_start(f"{analysis_type}:{step_name}", extra=step_context)
    else:
        logger.info(f"Starting step: {step_name}", extra={'analysis_type': analysis_type, 'step': step_name})

    try:
        yield
        if hasattr(logger, 'log_analysis_complete'):
            logger.log_analysis_complete(f"{analysis_type}:{step_name}", extra=step_context)
        else:
            logger.info(f"Completed step: {step_name}", extra={'analysis_type': analysis_type, 'step': step_name})
    except Exception as e:
        if hasattr(logger, 'log_analysis_error'):
            logger.log_analysis_error(f"{analysis_type}:{step_name}", e, extra=step_context)
        else:
            logger.error(f"Error in step {step_name}: {str(e)}",
                        exc_info=True, extra={'analysis_type': analysis_type, 'step': step_name})
        raise


def setup_script_logging(script_name: str, config_path: Optional[Path] = None) -> logging.Logger:
    """
    Set up logging for a script with standard configuration.

    Args:
        script_name: Name of the script (without .py extension)
        config_path: Optional path to logging configuration file

    Returns:
        Configured logger instance
    """
    # Load configuration
    if config_path and config_path.exists():
        config = LoggingConfig.from_yaml(config_path)
    else:
        config = get_default_logging_config()

    # Create logger
    logger = create_analysis_logger(f"scripts.{script_name}", config)

    # Log setup completion
    logger.info(f"Logging initialized for {script_name}")

    return logger


def format_elapsed_time(seconds: float) -> str:
    """
    Format elapsed time in a human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"
