"""Command line interface for ascii_tree."""

import argparse
from pathlib import Path

from ascii_tree import tree_gen


def validate_path(dir_path: str) -> Path:
    """Return absolute path if dir_path resolves to a valid directory.

    Raises:
        FileNotFoundError: If the path does not exist.
        NotADirectoryError: If the path exists but is not a directory.

    Returns:
        Path: The absolute path.
    """
    resolved_path = Path(dir_path).resolve(strict=True)
    if not resolved_path.is_dir():
        raise NotADirectoryError(f'Path "{resolved_path}" is not a directory.')
    return resolved_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()

    tree_gen.main(Path(validate_path(args.root)))



if __name__ == '__main__':
    main()
