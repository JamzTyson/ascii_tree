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
CONSOLE_LOG_LEVEL: int = logging.DEBUG
CONSOLE_LOG_FORMAT: str = "%(levelname)s:%(message)s"

LOG_TO_FILE: bool = False
FILE_LOG_FORMAT: str = "%(asctime)s:%(levelname)s:%(message)s"
FILE_LOG_LEVEL: int = logging.WARNING

_LOG_DIR: Path = Path(tempfile.gettempdir())
LOG_FILE: Path = _LOG_DIR / (LOGGER_NAME + '.log')


def _validate_log_file(file_path: Path) -> None:
    """Ensure log file directory exists and is writable.

    Args:
        file_path: The path to validate.

    Notes:
        The parent directory is expected to exist. If you are happy for
        ancestors to be created, change mkdir to `parents=True`.

    Raises:
        OSError: On any filesystem error that prevents logging.
    """
    try:
        file_path.parent.mkdir(exist_ok=True, parents=False)
        file_path.touch(exist_ok=True)
    except OSError as exc:
        raise OSError(f"Invalid LOG_FILE '{file_path}': {exc}") from exc


def configure_logging() -> None:
    """Configures logging for the application."""
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
        _validate_log_file(LOG_FILE)
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
