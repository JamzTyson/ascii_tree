"""Command line interface for ascii_tree."""

import argparse
import sys
from pathlib import Path
import tomllib

from ascii_tree.config import TreeGenConfig
from ascii_tree import tree_gen
from ascii_tree.filters import Filters
from ascii_tree.validate import resolve_directory_path, validate_file_path


def get_version() -> str:
    """Extract the version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    if not pyproject_path.exists():
        return "unknown"

    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)

    return pyproject_data.get("tool", {}).get("poetry", {}).get("version", "unknown")


def positive_int(value):
    """Validate positive integer."""
    int_value = int(value)
    if int_value < 0:
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

    # Options.
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f"%(prog)s {get_version()}"
    )

    # Tree display options.
    tree_group = parser.add_argument_group('Tree Options')

    tree_group.add_argument(
        '-a', '--all',
        help='''Show all files and directories, including hidden ones,
        up to specified max_depth (default: False).''',
        action='store_true'
    )
    tree_group.add_argument(
        '-L', '--max-depth',
        type=positive_int,
        default=None,
        help='Maximum max_depth for traversal (default: unlimited).'
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
    output_group.add_argument(
        '-v', '--verbose',
        help='Include OS info and full path to root (default: False).',
        action='store_true'
    )
    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> TreeGenConfig:
    """Convert the parsed arguments into a TreeGenConfig instance."""
    config = TreeGenConfig()

    # Configure root directory.
    try:
        config.root_dir = resolve_directory_path(args.root_dir)
    except ValueError as exc:
        sys.exit(f"Error: {exc}")

    # Configure tree display.
    if args.all:  # All directories and files up to specified max_depth.
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
        config.max_depth = args.max_depth

    # Pattern filtering options.
    config.filters.include_files = args.include_files
    config.filters.exclude_files = args.exclude_files
    config.filters.include_dirs = args.include_dirs
    config.filters.exclude_dirs = args.exclude_dirs

    # Output options.
    if args.quiet and not args.output:
        # Nothing to do.
        sys.exit('Terminal output and file output disabled by options.')

    # Disable terminal output.
    config.terminal_output = not args.quiet

    if args.output:
        try:
            config.output_file = validate_file_path(args.output)
        except OSError as exc:
            sys.exit(f'Error: {exc}')

    # Use ASCII rather than Unicode symbols.
    config.use_ascii = args.ascii

    # Include OS info and full path to root.
    config.verbose = args.verbose

    return config


def main():
    """Parse CLI and call main program."""
    args = parse_args()
    config = config_from_args(args)
    tree_gen.main(config)


if __name__ == '__main__':
    main()
