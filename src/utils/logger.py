"""
Logging Configuration Module
Sets up logging for the ETL pipeline
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Set up logging configuration

    Args:
        config: Logging configuration dictionary with keys:
            - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            - file_path: Path to log file
            - format: Log message format
            - max_bytes: Maximum log file size
            - backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_file = Path(config.get('file_path', 'logs/etl_pipeline.log'))
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Get log level
    log_level = getattr(logging, config.get('level', 'INFO').upper())

    # Create logger
    logger = logging.getLogger('pharmacy_etl')
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=config.get('max_bytes', 10485760),  # 10 MB default
        backupCount=config.get('backup_count', 5)
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Logging initialized")

    return logger
