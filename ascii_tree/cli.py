"""Command line interface for ascii_tree."""

import argparse
import logging
from pathlib import Path
import tomllib

from ascii_tree import tree_gen
from ascii_tree.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def get_version() -> str:
    """Extract the version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        logger.warning("pyproject.toml not found, returning default version.")
        return "unknown"

    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)  # Use toml.load(f) if on Python < 3.11

    return pyproject_data.get("tool", {}).get("poetry", {}).get("version", "unknown")


def validate_path(dir_path: Path) -> Path:
    """Return absolute path if dir_path resolves to a valid directory.

    Raises:
        FileNotFoundError: If the path does not exist.
        NotADirectoryError: If the path exists but is not a directory.

    Returns:
        Path: The absolute path.
    """
    resolved_path = dir_path.resolve(strict=True)
    if not resolved_path.is_dir():
        raise NotADirectoryError(f'Path "{resolved_path}" is not a directory.')
    return resolved_path


def main():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description='Draw a text representation of a directory tree.'
    )

    # Positional argument: root directory.
    parser.add_argument(
        'root_dir',
        help='Path to root of directory tree.',
        nargs='?',
        default='.',
        type=Path
    )

    # General options.
    general_group = parser.add_argument_group('General Options')
    general_group.add_argument(
        '-a', '--all',
        help='Show all files and directories, including hidden ones (default: False).',
        action='store_true'
    )

    # Display options.
    display_group = parser.add_argument_group('Display Options')
    display_group.add_argument(
        '-d', '--dirs-only',
        help='Display only directories, suppress files (default: show both).',
        action='store_true'
    )
    display_group.add_argument(
        '-hf', '--hidden-files',
        help='Include hidden files (default: False).',
        action='store_true'
    )
    display_group.add_argument(
        '-hd', '--hidden-dirs',
        help='Include hidden directories (default: False).',
        action='store_true'
    )

    # Pattern filtering options.
    filter_group = parser.add_argument_group('Pattern Filtering Options')
    filter_group.add_argument(
        '-if', '--include-files',
        nargs='*',
        default=['*'],
        help='File patterns to include (default: all).'
    )
    filter_group.add_argument(
        '-xf', '--exclude-files',
        nargs='*',
        default=[],
        help='File patterns to exclude (default: none).'
    )
    filter_group.add_argument(
        '-id', '--include-dirs',
        nargs='*',
        default=[],
        help='Directory patterns to include (default: all).'
    )
    filter_group.add_argument(
        '-xd', '--exclude-dirs',
        nargs='*',
        default=[],
        help='Directory patterns to exclude (default: none).'
    )

    # Output options.
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '-q', '--quiet',
        help='Disable output to terminal (default: enabled).',
        action='store_true'
    )
    output_group.add_argument(
        '-L', '--max-depth',
        type=int,
        default=None,
        help='Maximum depth for traversal (default: unlimited).'
    )
    output_group.add_argument(
        '-o', '--output',
        help='Output file.',
        type=Path
    )
    output_group.add_argument(
        '-A', '--ascii',
        help='Use ASCII branch characters instead of Unicode (default: use Unicode).',
        action='store_true'
    )

    # Logging and debugging.
    logging_group = parser.add_argument_group('Logging and Debugging')
    logging_group.add_argument(
        '-D', '--debug',
        help='Show debug messages (default: False).',
        action='store_true'
    )
    logging_group.add_argument(
        '-v', '--verbose',
        help='Include OS info and full path to root (default: False).',
        action='store_true'
    )
    logging_group.add_argument(
        '-l', '--log',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='CRITICAL',
        help='Logging level (default: CRITICAL).'
    )
    logging_group.add_argument(
        '-V', '--version',
        action='version',
        version=f"%(prog)s {get_version()}"
    )

    args = parser.parse_args()
    for arg, value in vars(args).items():
        logger.debug(f'{arg}: {value}')

    # TODO:
    # tree_gen.main(validate_path(args.root_dir))


if __name__ == '__main__':
    main()
