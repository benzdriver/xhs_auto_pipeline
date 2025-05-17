"""
Logging utilities for the Web Scraping Toolkit.

This module provides a consistent logging interface for all components
of the Web Scraping Toolkit.
"""

import os
import logging
import datetime
from typing import Optional

def configure_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger with the specified name and log level.
    
    Args:
        name: The name of the logger.
        log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Map string log levels to their corresponding constants
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    # Get the numeric log level (default to INFO if not recognized)
    level = log_level_map.get(log_level.upper(), logging.INFO)
    
    # Create and configure logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicate logging
    if logger.handlers:
        logger.handlers = []
        
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set formatter on console handler
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Configure file handler if LOG_TO_FILE is enabled
    if os.getenv("LOG_TO_FILE", "").lower() == "true":
        _add_file_handler(logger, name, level, formatter)
    
    return logger

def _add_file_handler(
    logger: logging.Logger,
    name: str,
    level: int,
    formatter: logging.Formatter
) -> None:
    """
    Add a file handler to the logger.
    
    Args:
        logger: The logger to add the file handler to.
        name: The name of the logger (used for the log file name).
        level: The log level.
        formatter: The formatter to use for the file handler.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.getenv("LOG_DIRECTORY", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log file name with current date
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{name}_{date_str}.log")
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Add file handler to logger
    logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: The name of the logger.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Get log level from environment variable or use default
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    return configure_logger(name, log_level) 