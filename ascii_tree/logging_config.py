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
import tempfile
from pathlib import Path

LOGGING_ENABLED: bool = True
LOGGER_NAME: str = 'ascii_tree'

LOG_TO_CONSOLE: bool = True
CONSOLE_LOG_LEVEL = logging.DEBUG
CONSOLE_LOG_FORMAT: str = "%(levelname)s:%(message)s"

LOG_TO_FILE: bool = True
LOG_FILE: str = str(Path(tempfile.gettempdir()) / (LOGGER_NAME + '.log'))
FILE_LOG_FORMAT: str = "%(asctime)s:%(levelname)s:%(message)s"
FILE_LOG_LEVEL: int = logging.WARNING


if LOGGING_ENABLED and LOG_TO_FILE:
    try:
        Path(LOG_FILE).parent.mkdir(exist_ok=True)
        with open(LOG_FILE, 'a'):
            pass
    except (FileNotFoundError, PermissionError, OSError) as exc:
        raise OSError(f"Invalid LOG_FILE '{LOG_FILE}': {exc}") from exc


def configure_logging() -> None:
    """Configures logging for the application."""
    if not LOGGING_ENABLED:
        logging.disable(logging.CRITICAL + 1)  # Disable all logging if not enabled
        return

    # Set root logger level to NOTSET to delegate log level to handlers.
    logging.getLogger().setLevel(logging.NOTSET)
    logger = logging.getLogger(LOGGER_NAME)

    if logger.hasHandlers():
        logger.handlers.clear()

    handlers: list[logging.Handler] = []
    if LOG_TO_FILE:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(FILE_LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
        handlers.append(file_handler)

    if LOG_TO_CONSOLE:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(CONSOLE_LOG_LEVEL)
        stream_handler.setFormatter(logging.Formatter(CONSOLE_LOG_FORMAT))
        handlers.append(stream_handler)

    for handler in handlers:
        logger.addHandler(handler)

    # Logging level set per handler
    logger.setLevel(logging.NOTSET)
