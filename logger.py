"""
Edward Colored Logger Module
Custom logging with Full Metal Alchemist Edward color scheme
"""

import logging
import sys
from typing import Optional


class _Utf8StreamHandler(logging.StreamHandler):
    """
    StreamHandler that writes UTF-8 bytes directly to stdout.buffer,
    bypassing Python's text-encoding layer.  Works on Windows terminals
    locked to CP1252 where sys.stdout.reconfigure() has no effect.
    Falls back gracefully when no raw buffer is available (e.g. IDE consoles).
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record) + self.terminator
            buf = getattr(self.stream, 'buffer', None)
            if buf is not None:
                buf.write(msg.encode('utf-8', errors='replace'))
                buf.flush()
            else:
                # No raw buffer (IDE / redirected output): replace unencodable chars
                self.stream.write(msg.encode('ascii', errors='replace').decode('ascii'))
                self.flush()
        except Exception:
            self.handleError(record)


class EdwardColoredFormatter(logging.Formatter):
    """
    Custom formatter with Edward's color scheme from Full Metal Alchemist:
    - Gold (#DAA520) for INFO
    - Red (#B22222) for ERROR/CRITICAL
    - Silver (#A8A9AD) for DEBUG
    - White for WARNING
    """

    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GOLD   = "\033[38;2;218;165;32m"
    RED    = "\033[38;2;178;34;34m"
    SILVER = "\033[38;2;168;169;173m"
    WHITE  = "\033[97m"

    COLORS = {
        logging.DEBUG:    SILVER,
        logging.INFO:     GOLD,
        logging.WARNING:  WHITE,
        logging.ERROR:    RED,
        logging.CRITICAL: f"\033[1m\033[38;2;178;34;34m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color   = self.COLORS.get(record.levelno, self.WHITE)
        log_fmt = (
            f"{color}%(asctime)s - {self.BOLD}%(name)s{self.RESET}"
            f"{color} - %(levelname)s - %(message)s{self.RESET}"
        )
        return logging.Formatter(log_fmt, datefmt='%H:%M:%S').format(record)


def setup_logger(
    name:     str,
    level:    int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    logger.handlers.clear()

    # Console — writes UTF-8 bytes to stdout.buffer directly
    console_handler = _Utf8StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(EdwardColoredFormatter())
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        ))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    return setup_logger(name)


if __name__ == "__main__":
    log = get_logger(__name__)
    log.debug("Debug (silver)")
    log.info("Info (gold) ⚡ ✓ — unicode test")
    log.warning("Warning (white)")
    log.error("Error (red)")
    log.critical("Critical (bold red)")
