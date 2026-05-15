"""
Edward Colored Logger Module
Custom logging with Full Metal Alchemist Edward color scheme
"""

import logging
import sys
from typing import Optional


class EdwardColoredFormatter(logging.Formatter):
    """
    Custom formatter with Edward's color scheme from Full Metal Alchemist:
    - Gold (#DAA520) for INFO
    - Red (#B22222) for ERROR/CRITICAL
    - Silver (#A8A9AD) for DEBUG
    - White for WARNING
    """
    
    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Edward FMA colors
    GOLD = "\033[38;2;218;165;32m"      # #DAA520
    RED = "\033[38;2;178;34;34m"        # #B22222
    SILVER = "\033[38;2;168;169;173m"   # #A8A9AD
    WHITE = "\033[97m"
    
    # Level colors
    COLORS = {
        logging.DEBUG: SILVER,
        logging.INFO: GOLD,
        logging.WARNING: WHITE,
        logging.ERROR: RED,
        logging.CRITICAL: f"{BOLD}{RED}",
    }
    
    def format(self, record):
        """Format log record with colors"""
        # Get color for this level
        color = self.COLORS.get(record.levelno, self.WHITE)
        
        # Format the message
        log_fmt = f"{color}%(asctime)s - {self.BOLD}%(name)s{self.RESET}{color} - %(levelname)s - %(message)s{self.RESET}"
        
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup a logger with Edward's colored formatting.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file path for file logging
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(EdwardColoredFormatter())
    logger.addHandler(console_handler)
    
    # File handler without colors (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with Edward's formatting.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return setup_logger(name)


# Example usage
if __name__ == "__main__":
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message (silver)")
    logger.info("This is an info message (gold)")
    logger.warning("This is a warning message (white)")
    logger.error("This is an error message (red)")
    logger.critical("This is a critical message (bold red)")

# Made with Bob