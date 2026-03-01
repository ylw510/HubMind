"""
Logging Configuration Module
"""
import logging
import sys
from pathlib import Path
from config import Config


def setup_logger(name: str = "HubMind", level: str = None) -> logging.Logger:
    """
    Setup and return a configured logger

    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, uses Config.LOG_LEVEL

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Don't add handlers if they already exist (avoid duplicate logs)
    if logger.handlers:
        return logger

    # Set log level
    log_level = level or Config.LOG_LEVEL.upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler for backend logs
    try:
        # Try to create log file in backend directory
        # Path(__file__) is src/utils/logger.py, so parent.parent is project root
        project_root = Path(__file__).parent.parent.parent
        backend_dir = project_root / "backend"
        log_file = backend_dir / "backend.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.DEBUG)  # File handler always logs DEBUG and above
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If file logging fails, just use console
        print(f"Warning: Failed to setup file logging: {str(e)}", file=sys.stderr)

    # Prevent propagation to root logger (avoid duplicate logs)
    logger.propagate = False

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance for the given name

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if name is None:
        name = "HubMind"
    return setup_logger(name)


# Create root logger
root_logger = setup_logger("HubMind")
