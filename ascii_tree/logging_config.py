"""Logger configuration.

Configures logging to console and/or file. When logging to a file,
the directory must exist and be writeable. Logging levels may be
configured separately for console and file. Logging may be disabled
with the single 'LOGGING_ENABLED' flag.

The default location of the log file is 'ascii_tree.log' in the
system's Temp directory.

Raises:
    OSError: If LOG_FILE is invalid.
"""

import logging
import sys
import tempfile
from pathlib import Path

from ascii_tree.validate import validate_file_path

#TODO: Consider switching to Loguru.

_logger_configured = False  # Guard flag.

LOGGING_ENABLED: bool = True
LOGGER_NAME: str = 'ascii_tree'

LOG_TO_CONSOLE: bool = True
CONSOLE_LOG_LEVEL: int = logging.DEBUG
CONSOLE_LOG_FORMAT: str = "%(levelname)s:%(message)s"

LOG_TO_FILE: bool = False
FILE_LOG_FORMAT: str = "%(asctime)s:%(levelname)s:%(message)s"
FILE_LOG_LEVEL: int = logging.WARNING

_LOG_DIR: Path = Path(tempfile.gettempdir())
LOG_FILE: Path = _LOG_DIR / (LOGGER_NAME + '.log')


def configure_logging() -> None:
    """Configures logging for the application."""
    global _logger_configured
    if _logger_configured:  # Prevent multiple configurations
        return
    _logger_configured = True

    logger = logging.getLogger(LOGGER_NAME)

    if not LOGGING_ENABLED:
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
        return

    # Safely remove any existing handlers.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    logger.propagate = False

    if LOG_TO_FILE:
        try:
            validate_file_path(LOG_FILE)
        except OSError as exc:
            logger.critical(f"Error: {exc}")
            sys.exit(f"Error: {exc}")
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(FILE_LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
        logger.addHandler(file_handler)

    if LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(CONSOLE_LOG_LEVEL)
        console_handler.setFormatter(logging.Formatter(CONSOLE_LOG_FORMAT))
        logger.addHandler(console_handler)

    # Set the base logger level to the lowest handler level.
    # Sends CRITICAL messages to stderr through
    # logging.lastResort fallback when no handlers are configured.
    logger.setLevel(min(h.level for h in logger.handlers)
                    if logger.handlers else logging.CRITICAL)
