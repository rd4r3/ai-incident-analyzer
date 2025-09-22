import logging
import logging.handlers
import os
from typing import Optional

def setup_logging(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 3,
    format_str: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
) -> logging.Logger:
    """Centralized logging configuration with green coding practices.

    Args:
        name: Logger name (defaults to module name)
        level: Logging level
        log_file: Log file path
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        format_str: Log message format

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if called multiple times
    if logger.hasHandlers():
        return logger

    # Set level
    logger.setLevel(level)

    # Create handlers
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    console_handler = logging.StreamHandler()

    # Set format
    formatter = logging.Formatter(format_str)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
