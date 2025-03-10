"""Command line interface for ascii_tree."""

import argparse
import logging
import sys
from pathlib import Path
import tomllib

from ascii_tree.config import TreeGenConfig
from ascii_tree import tree_gen
from ascii_tree.logging_config import configure_logging, LOGGER_NAME
from ascii_tree.filters import Filters

configure_logging()
logger = logging.getLogger(LOGGER_NAME)


def get_version() -> str:
    """Extract the version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        logger.warning("pyproject.toml not found, returning default version.")
        return "unknown"

    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)

    return pyproject_data.get("tool", {}).get("poetry", {}).get("version", "unknown")


def validate_path(dir_path: Path) -> Path:
    """Return absolute path if dir_path resolves to a valid directory.

    Raises:
        FileNotFoundError: If the path does not exist.
        NotADirectoryError: If the path exists but is not a directory.

    Returns:
        Path: The absolute path.
    """
    try:
        resolved_path = dir_path.resolve(strict=True)
    except OSError:
        raise FileNotFoundError(f'Path "{dir_path}" does not exist.')
    if not resolved_path.is_dir():
        raise NotADirectoryError(f'Path "{resolved_path}" is not a directory.')
    return resolved_path


def positive_int(value):
    """Validate positive integer."""
    int_value = int(value)
    if int_value < 1:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return int_value


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog='asciitree',
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

    # Tree display options.
    tree_group = parser.add_argument_group('Tree Options')

    tree_group.add_argument(
        '-a', '--all',
        help='''Show all files and directories, including hidden ones,
        up to specified depth (default: False).''',
        action='store_true'
    )
    tree_group.add_argument(
        '-L', '--max-depth',
        type=positive_int,
        default=None,
        help='Maximum depth for traversal (default: unlimited).'
    )
    tree_group.add_argument(
        '-d', '--dirs-only',
        help='Display only directories, suppress files (default: show both).',
        action='store_true'
    )
    tree_group.add_argument(
        '-hf', '--hidden-files',
        help='Include hidden files (default: False).',
        action='store_true'
    )
    tree_group.add_argument(
        '-hd', '--hidden-dirs',
        help='Include hidden directories (default: False).',
        action='store_true'
    )

    # Pattern filtering options.
    filter_group = parser.add_argument_group('Pattern Filtering Options')

    filter_group.add_argument(
        '-if', '--include-files',
        nargs='*',
        default=[],
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

    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> TreeGenConfig:
    """Convert the parsed arguments into a TreeGenConfig instance."""
    config = TreeGenConfig()

    # Configure root directory.
    try:
        config.root_dir = validate_path(args.root_dir)
    except (NotADirectoryError, FileNotFoundError) as exc:
        logger.critical(exc)
        print(f"Error: {exc}")
        sys.exit(1)

    # Configure tree display.
    if args.all:  # All directories and files up to specified depth.
        args.dirs_only = False
        args.hidden_files = True
        args.hidden_dirs = True
        args.include_files = []
        args.exclude_files = []
        args.include_dirs = []
        args.exclude_dirs = []

    else:
        if not args.hidden_files:
            args.exclude_files.append(Filters.unix_hidden)
        if not args.hidden_dirs:
            args.exclude_dirs.append(Filters.unix_hidden)

        config.dirs_only = args.dirs_only

    # Maximum depth applied even with -a / --all flag.
    if args.max_depth:
        config.depth = args.max_depth

    # Pattern filtering options.
    config.filters.include_files = args.include_files
    config.filters.exclude_files = args.exclude_files
    config.filters.include_dirs = args.include_dirs
    config.filters.exclude_dirs = args.exclude_dirs

    # Output options.
    config.terminal_output = not args.quiet
    config.output_file = args.output  # TODO: Validate before committing.
    config.use_ascii = args.ascii

    logger.debug(f"FILTERS: {config.filters.exclude_files}, "
                 f"{config.filters.exclude_dirs}")
    logger.debug(f"MAX_DEPTH: {config.depth}")
    logger.debug(f"Terminal output: {config.terminal_output}")
    logger.debug(f"Output File: {config.output_file}\n")
    return config


def main():
    """Parse CLI and call main program."""
    args = parse_args()
    config = config_from_args(args)

    for arg, value in vars(args).items():
        logger.debug(f'{arg}: {value}')

    tree_gen.main(config)


if __name__ == '__main__':
    main()
