"""Logging configuration for the Slack Archive Migration tool."""

import os
import logging
import structlog
from typing import Any, Dict
from src.config import Config

def setup_logging(config: Config) -> None:
    """Set up structured logging with the given configuration."""
    
    # Create logs directory if it doesn't exist
    log_file = config.log_file
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

class MigrationLogger:
    """Custom logger for migration operations with context."""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with context."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        self.logger.debug(message, **kwargs)
    
    def log_file_operation(self, operation: str, file_id: str, 
                          file_name: str, channel: str = None, 
                          status: str = "started", **kwargs: Any) -> None:
        """Log file operation with structured context."""
        self.logger.info(
            f"File {operation} {status}",
            operation=operation,
            file_id=file_id,
            file_name=file_name,
            channel=channel,
            status=status,
            **kwargs
        )
    
    def log_api_call(self, service: str, method: str, 
                    status: str = "success", **kwargs: Any) -> None:
        """Log API call with structured context."""
        self.logger.info(
            f"API call {status}",
            service=service,
            method=method,
            status=status,
            **kwargs
        )
    
    def log_migration_progress(self, total: int, processed: int, 
                              current_file: str = None, **kwargs: Any) -> None:
        """Log migration progress with structured context."""
        progress_percent = (processed / total * 100) if total > 0 else 0
        self.logger.info(
            "Migration progress",
            total_files=total,
            processed_files=processed,
            progress_percent=round(progress_percent, 2),
            current_file=current_file,
            **kwargs
        )
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with additional context information."""
        self.logger.error(
            f"Error occurred: {str(error)}",
            error_type=type(error).__name__,
            error_message=str(error),
            **context
        )

# tweak 20 at 2025-09-26 19:30:08
