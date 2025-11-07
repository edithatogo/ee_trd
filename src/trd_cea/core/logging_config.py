"""
Logging configuration for TRD CEA Toolkit.

This module provides standardized logging configuration for health economic evaluation tools.
"""

import logging
import sys
from pathlib import Path


def setup_logging(
    module_name: str,
    log_level: int = logging.INFO,
    log_file: str = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up standardized logging for a module.
    
    Args:
        module_name: Name of the module requesting logging
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        console_output: Whether to output logs to console
        
    Returns:
        Configured logger object
    """
    # Create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def setup_analysis_logging(
    analysis_name: str,
    results_dir: str = "results",
    log_level: int = logging.INFO
) -> logging.Logger:
    """
    Set up logging specifically for analysis runs.
    
    Args:
        analysis_name: Name of the analysis
        results_dir: Directory to store results and logs
        log_level: Logging level
        
    Returns:
        Configured logger for the analysis
    """
    # Create results directory if it doesn't exist
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    # Create log file path
    log_file = Path(results_dir) / f"{analysis_name.replace(' ', '_')}_log.txt"
    
    # Set up logger
    logger = setup_logging(
        f"analysis.{analysis_name}",
        log_level=log_level,
        log_file=str(log_file),
        console_output=True
    )
    
    # Log analysis start
    logger.info(f"Starting analysis: {analysis_name}")
    logger.info(f"Results directory: {results_dir}")
    logger.info(f"Log file: {log_file}")
    
    return logger


def log_analysis_parameters(logger: logging.Logger, parameters: dict):
    """
    Log analysis parameters for reproducibility.
    
    Args:
        logger: Logger to use for logging
        parameters: Dictionary of analysis parameters
    """
    logger.info("Analysis parameters:")
    for key, value in parameters.items():
        logger.info(f"  {key}: {value}")


def log_analysis_results(logger: logging.Logger, results: dict):
    """
    Log key analysis results for tracking.
    
    Args:
        logger: Logger to use for logging
        results: Dictionary of analysis results
    """
    logger.info("Analysis results summary:")
    
    if 'icers' in results:
        logger.info("  ICERs:")
        for strategy, icer in results['icers'].items():
            logger.info(f"    {strategy}: ${icer:,.2f}/QALY")
    
    if 'nmbs' in results:
        logger.info("  Net Monetary Benefits:")
        for strategy, nmb in results['nmbs'].items():
            logger.info(f"    {strategy}: ${nmb:,.2f}")
    
    if 'probabilities_ce' in results:
        logger.info("  Cost-effectiveness probabilities:")
        for strategy, prob in results['probabilities_ce'].items():
            logger.info(f"    {strategy}: {prob:.3f}")


def log_execution_info(logger: logging.Logger):
    """
    Log system and execution information for provenance.
    
    Args:
        logger: Logger to use for logging
    """
    import platform
    import sys
    import datetime
    
    logger.info("Execution environment information:")
    logger.info(f"  Python version: {sys.version}")
    logger.info(f"  Platform: {platform.platform()}")
    logger.info(f"  Processor: {platform.processor()}")
    logger.info(f"  Machine: {platform.machine()}")
    logger.info(f"  Timestamp: {datetime.datetime.now()}")
    
    # Log installed packages
    try:
        import pkg_resources
        logger.info("  Installed packages:")
        for dist in pkg_resources.working_set:
            logger.info(f"    {dist.project_name}: {dist.version}")
    except Exception as e:
        logger.warning(f"  Could not log package information: {e}")


class AnalysisLogger:
    """
    Higher-level logging class for health economic analyses.
    """
    
    def __init__(
        self,
        analysis_name: str,
        results_dir: str = "results",
        log_level: int = logging.INFO
    ):
        self.logger = setup_analysis_logging(
            analysis_name,
            results_dir,
            log_level
        )
        self.analysis_name = analysis_name
        self.results_dir = results_dir
    
    def start_analysis(self, parameters: dict):
        """Log analysis start."""
        self.logger.info("="*60)
        self.logger.info(f"STARTING ANALYSIS: {self.analysis_name}")
        self.logger.info("="*60)
        log_analysis_parameters(self.logger, parameters)
        log_execution_info(self.logger)
    
    def complete_analysis(self, results: dict):
        """Log analysis completion."""
        log_analysis_results(self.logger, results)
        self.logger.info("="*60)
        self.logger.info(f"COMPLETED ANALYSIS: {self.analysis_name}")
        self.logger.info("="*60)
    
    def info(self, msg: str):
        """Log an info message."""
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """Log a warning message."""
        self.logger.warning(msg)
    
    def error(self, msg: str):
        """Log an error message."""
        self.logger.error(msg)
    
    def debug(self, msg: str):
        """Log a debug message."""
        self.logger.debug(msg)