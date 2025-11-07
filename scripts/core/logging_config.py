"""
Centralized logging configuration for V4 health economic evaluation pipeline.

This module provides standardized logging setup across all analysis scripts,
replacing print() statements with proper logging infrastructure.
"""
from __future__ import annotations

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml


@dataclass
class LoggingConfig:
    """Configuration for logging setup."""

    # Basic settings
    level: str = "INFO"
    format: str = "console"  # console, json, structured
    enable_console: bool = True
    enable_file: bool = True

    # File settings
    log_dir: Optional[Path] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    encoding: str = "utf-8"

    # Analysis-specific settings
    include_progress: bool = True
    include_timestamps: bool = True
    include_analysis_context: bool = True

    # Output formatting
    colorize_console: bool = True
    json_indent: Optional[int] = None

    def __post_init__(self):
        """Set default log directory if not provided."""
        if self.log_dir is None:
            self.log_dir = Path("logs")
        else:
            self.log_dir = Path(self.log_dir)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LoggingConfig:
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> LoggingConfig:
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class AnalysisFormatter(logging.Formatter):
    """Custom formatter for analysis logs with structured output."""

    def __init__(self, config: LoggingConfig):
        super().__init__()
        self.config = config

    def format(self, record: logging.LogRecord) -> str:
        """Format log record based on configuration."""
        if self.config.format == "json":
            return self._format_json(record)
        elif self.config.format == "structured":
            return self._format_structured(record)
        else:
            return self._format_console(record)

    def _format_json(self, record: logging.LogRecord) -> str:
        """Format as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add analysis context if available
        if hasattr(record, 'analysis_type'):
            analysis_type = getattr(record, 'analysis_type', None)
            if analysis_type is not None:
                log_data["analysis_type"] = str(analysis_type)
        if hasattr(record, 'progress'):
            progress = getattr(record, 'progress', None)
            if progress is not None:
                log_data["progress"] = float(progress)
        if hasattr(record, 'data'):
            data = getattr(record, 'data', None)
            if data is not None:
                log_data["data"] = data

        return json.dumps(log_data, indent=self.config.json_indent)

    def _format_structured(self, record: logging.LogRecord) -> str:
        """Format as structured text."""
        parts = []

        if self.config.include_timestamps:
            timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
            parts.append(f"[{timestamp}]")

        parts.append(f"{record.levelname}")
        parts.append(f"{record.name}")

        analysis_type = getattr(record, 'analysis_type', None)
        if analysis_type:
            parts.append(f"({analysis_type})")

        parts.append(record.getMessage())

        progress = getattr(record, 'progress', None)
        if progress and self.config.include_progress:
            parts.append(f"[{progress:.1%}]")

        return " ".join(parts)

    def _format_console(self, record: logging.LogRecord) -> str:
        """Format for console output."""
        if self.config.colorize_console:
            return self._format_colored(record)
        else:
            return self._format_plain(record)

    def _format_colored(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        reset = '\033[0m'

        color = colors.get(record.levelname, '')
        level_colored = f"{color}{record.levelname}{reset}"

        parts = [level_colored, record.name]

        analysis_type = getattr(record, 'analysis_type', None)
        if analysis_type:
            parts.append(f"({analysis_type})")

        message = record.getMessage()

        # Color progress indicators
        progress = getattr(record, 'progress', None)
        if progress and self.config.include_progress:
            progress_color = '\033[34m'  # Blue
            message += f" {progress_color}[{progress:.1%}]{reset}"

        parts.append(message)

        return " ".join(parts)

    def _format_plain(self, record: logging.LogRecord) -> str:
        """Format as plain text."""
        parts = [record.levelname, record.name]

        analysis_type = getattr(record, 'analysis_type', None)
        if analysis_type:
            parts.append(f"({analysis_type})")

        parts.append(record.getMessage())

        progress = getattr(record, 'progress', None)
        if progress and self.config.include_progress:
            parts.append(f"[{progress:.1%}]")

        return " ".join(parts)


class AnalysisLoggerAdapter(logging.LoggerAdapter):
    """Adapter to add analysis context to log records."""

    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Process log message with extra context."""
        # Add any extra fields from kwargs to the record
        extra = dict(self.extra) if self.extra else {}
        extra.update(kwargs.get('extra', {}))

        # Set analysis context on the record
        if 'analysis_type' in extra:
            kwargs['extra'] = extra

        return msg, kwargs

    def log_progress(self, progress: float, message: str, **kwargs):
        """Log progress with percentage."""
        extra = kwargs.get('extra', {})
        extra['progress'] = progress
        kwargs['extra'] = extra
        self.info(message, **kwargs)

    def log_analysis_start(self, analysis_type: str, **kwargs):
        """Log start of analysis."""
        extra = kwargs.get('extra', {})
        extra['analysis_type'] = analysis_type
        kwargs['extra'] = extra
        self.info(f"Starting {analysis_type}", **kwargs)

    def log_analysis_complete(self, analysis_type: str, **kwargs):
        """Log completion of analysis."""
        extra = kwargs.get('extra', {})
        extra['analysis_type'] = analysis_type
        kwargs['extra'] = extra
        self.info(f"Completed {analysis_type}", **kwargs)

    def log_analysis_error(self, analysis_type: str, error: Exception, **kwargs):
        """Log analysis error with context."""
        extra = kwargs.get('extra', {})
        extra['analysis_type'] = analysis_type
        extra['error_type'] = type(error).__name__
        kwargs['extra'] = extra
        self.error(f"Error in {analysis_type}: {str(error)}", exc_info=True, **kwargs)


def setup_analysis_logging(name: str, config: LoggingConfig) -> AnalysisLoggerAdapter:
    """
    Set up logging for analysis scripts.

    Args:
        name: Logger name (typically __name__)
        config: Logging configuration

    Returns:
        Configured logger adapter
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = AnalysisFormatter(config)

    # Console handler
    if config.enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if config.enable_file:
        # Ensure log_dir is not None (should be set by __post_init__)
        if config.log_dir is not None:
            config.log_dir.mkdir(parents=True, exist_ok=True)
            log_file = config.log_dir / f"{name.replace('.', '_')}.log"

            # Use rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=config.max_file_size,
                backupCount=config.backup_count,
                encoding=config.encoding
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    # Create adapter with empty extra context
    adapter = AnalysisLoggerAdapter(logger, {})

    return adapter


def load_logging_config(config_path: Optional[Path] = None) -> LoggingConfig:
    """
    Load logging configuration from file or use defaults.

    Args:
        config_path: Path to configuration file (YAML)

    Returns:
        Logging configuration
    """
    if config_path and config_path.exists():
        return LoggingConfig.from_yaml(config_path)
    else:
        # Return default configuration
        return LoggingConfig()


def get_default_logging_config() -> LoggingConfig:
    """Get default logging configuration for V4 analysis."""
    return LoggingConfig(
        level="INFO",
        format="console",
        enable_console=True,
        enable_file=True,
        log_dir=Path("logs"),
        max_file_size=10 * 1024 * 1024,  # 10MB
        backup_count=5,
        include_progress=True,
        include_timestamps=True,
        include_analysis_context=True,
        colorize_console=True
    )
