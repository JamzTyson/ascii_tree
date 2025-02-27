"""ASCII Tree Generator

A command-line tool for generating a plain text representation
of a directory tree. Output may be to the terminal, to a text file,
or both.

Main Features:

    Iterative tree traversal:
        Can potentially handle extremely large/deep directory trees.

    Flexible Pattern Handling:
        Manages inclusion and exclusion patterns for files and directories.

    Visual Formatting with Unicode Symbols:
        Produces a clear and visually appealing text representation of the
        tree structure.

    Optional Logging:
        Configurable through logging_config.py

Dependencies:
    Python >= 3.10

"""

import logging
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ascii_tree.logging_config import configure_logging, LOGGER_NAME
from ascii_tree.filters import Filters


configure_logging()
logger = logging.getLogger(LOGGER_NAME)


SYMBOL_LEN = 4
"""int: The length of all "prefix" symbols is 4 characters."""


class Symbol(Enum):
    """Indentation symbols."""
    INDENT = '    '
    CONTINUE = '│   '
    BRANCH = '├── '
    FINAL = '└── '
    DIR = '/'


@dataclass
class Node:
    """Represent a directory listing with attributes."""
    dir_path: Path
    dirs: list[str]
    files: list[str]
    depth: int
    prefix: str = ''
    name: str = ''

    def __post_init__(self):
        self.name = self.dir_path.name

    def __str__(self) -> str:
        """Return printable representation of node."""
        return f"{self.prefix}{self.name}/"


class Tree:
    """Directory tree."""

    def __init__(self, top: Path, filters: Filters = None) -> None:
        self.top = top
        self.filters = filters
        self.nodes: dict[Path, Node] = {}
        self.populate()
        self.prefix_nodes()

    def __str__(self) -> str:
        """Return tree as formatted string."""
        output_strings: list[str] = []
        stack: list[Node] = []  # Tracks parent directories with pending files

        for node in self.nodes.values():
            # When moving up the tree (current depth <= previous)
            # flush files from deeper directories
            while stack and stack[-1].depth >= node.depth:
                parent = stack.pop()
                output_strings = append_file_lines(output_strings, parent)

            # Add directory line and push to stack if it has files
            output_strings.append(f"{node.prefix}{node.name}{Symbol.DIR.value}")
            if node.files:
                stack.append(node)

        # Flush any remaining files after processing all nodes
        while stack:
            parent = stack.pop()
            output_strings = append_file_lines(output_strings, parent)

        return '\n'.join(output_strings)

    def populate(self):
        """Add Nodes to Tree."""
        root_depth = len(self.top.parts)
        for root, dirs, files in os.walk(self.top):
            directory = Path(root)
            dirs[:] = self.filter_dirs(dirs)
            files[:] = self.filter_files(files)
            depth = len(directory.parts) - root_depth
            self.nodes[directory] = Node(directory, dirs, files, depth)

    @staticmethod
    def do_filter(items: list[str],
                  include_re: re.Pattern | None,
                  exclude_re: re.Pattern | None) -> list[str]:
        """Filter items based on inclusion and exclusion regex patterns.

            Args:
                items: The list of items (e.g., files or directories) to filter.
                include_re: A regex pattern for inclusion (None means include all).
                exclude_re: A regex pattern for exclusion (None means exclude none).

            Returns:
                A list of items that satisfy the inclusion/exclusion criteria.
            """
        return [i for i in items
                if (not include_re or include_re.match(i)) and
                (not exclude_re or not exclude_re.match(i))]

    def filter_files(self, files: list[str]) -> list[str]:
        """Filter and sort files as required.

        Returns:
            list[str]: The sorted and filtered file list.
        """
        if self.filters is None:
            return sorted(files)
        return sorted(self.do_filter(
            files, self.filters.include_files, self.filters.exclude_files))

    def filter_dirs(self, directories: list[str]) -> list[str]:
        """Filter and sort directories as required.

        Returns:
            list[str]: The sorted and filtered directory list.
        """
        if self.filters is None:
            return sorted(directories)
        return sorted(self.do_filter(
            directories, self.filters.include_dirs, self.filters.exclude_dirs))

    def prefix_nodes(self) -> None:
        """Assign visual prefix to each Node in the Tree."""
        for dir_path, node in self.nodes.items():
            try:
                parent_node = self.nodes[dir_path.parent]
            except KeyError:  # Top level does not have a parent.
                if dir_path == self.top:
                    continue
                logger.error('Parent of {} cannot be accessed.'.format(dir_path))
                raise ValueError(f'Parent of {dir_path} cannot be accessed.')

            try:
                parent_node.dirs.remove(node.name)
            except ValueError as e:
                logger.warning(
                    "Failed to remove '{}' from parent '{}' dirs. "
                    "Current dirs: {}. {}".format(
                        node.name, parent_node.name, parent_node.dirs, e))

            node.prefix = transform_prefix(parent_node)


def transform_trailing_prefix(prefix: str) -> str:
    """Replace final symbol for proper continuation to next level."""
    prefix = replace_trailing_symbol(prefix, Symbol.CONTINUE, Symbol.BRANCH)
    prefix = replace_trailing_symbol(prefix, Symbol.INDENT, Symbol.FINAL)
    return prefix


def transform_prefix(parent: Node) -> str:
    """Transform parent prefix to create prefix for directory node.

    Prefixes, representing indentation, branches and continuation, are
    constructed based on each Node's hierarchical position within the Tree.

    Starting with the parent's prefix:
    - An initial `Symbol.BRANCH` is replaced with `Symbol.CONTINUE` to maintain
      vertical continuation.
    - A final `Symbol.BRANCH` is replaced with `Symbol.CONTINUE` to retain
      indentation and vertical continuation.
    - A final `Symbol.FINAL` is replaced with `Symbol.INDENT` to retain
      indentation without vertical continuation.
    - If the parent has more siblings (subdirectories or files) after the current
      node, add a `Symbol.BRANCH` for the current Node, else add a `Symbol.FINAL`.

    Args:
        parent: The parent node.

    Returns:
        str: The constructed prefix for the node.
    """
    new_prefix = transform_trailing_prefix(parent.prefix)
    new_prefix = replace_leading_symbol(new_prefix, Symbol.CONTINUE, Symbol.BRANCH)

    parent_has_siblings = parent.dirs or parent.files
    if parent_has_siblings:
        new_prefix += Symbol.BRANCH.value
    else:
        new_prefix += Symbol.FINAL.value

    return new_prefix


def append_file_lines(file_lines: list[str], node: Node) -> list[str]:
    """Append file lines, ensuring termination with FINAL prefix.

    The file prefix is derived from its parent by replacing the final
    Symbol BRANCH to CONTINUE, or FINAL to INDENT, then adding a Symbol for
    the file itself.

    Raises:
        SystemExit: If `node.files` is empty (unexpected state).

    Returns:
        list[str]: The updated list.
    """
    file_prefix = transform_trailing_prefix(node.prefix)

    try:
        for file in node.files[:-1]:
            file_lines.append(f'{file_prefix}{Symbol.BRANCH.value}{file}')
        file_lines.append(f'{file_prefix}{Symbol.FINAL.value}{node.files[-1]}')
    except IndexError:
        logger.critical("Unexpected empty files list in node: %s (path: %s).",
                        node.name, node.dir_path)
        sys.exit(1)

    return file_lines


def replace_leading_symbol(
        prefix: str, new_symbol: Symbol, match_symbol: Symbol) -> str:
    """Replace initial symbol in prefix string when it matches specified symbol.

        Args:
            prefix: The prefix to modify.
            new_symbol: The new symbol to use.
            match_symbol: The symbol will only be replaced if it matches.

        Returns:
            str: The modified string.
        """
    if prefix.startswith(match_symbol.value):
        return prefix[:-SYMBOL_LEN] + new_symbol.value
    return prefix


def replace_trailing_symbol(
        prefix: str, new_symbol: Symbol, match_symbol: Symbol) -> str:
    """Replace final symbol in prefix string when it matches specified symbol.

        Args:
            prefix: The prefix to modify.
            new_symbol: The new symbol to use.
            match_symbol: The symbol will only be replaced if it matches.

        Returns:
            str: The modified string.
        """
    if prefix.endswith(match_symbol.value):
        return prefix[:-SYMBOL_LEN] + new_symbol.value
    return prefix


def validate_root_path(root_dir: str) -> Path:
    """Validate root directory and return as an absolute path.

    Raises:
        ValueError: root_dir argument is not a valid file path.

    Returns:
        Path: Absolute Path
    """
    root_as_path = Path(root_dir)

    if root_as_path.exists() and root_as_path.is_dir():
        root_as_path = root_as_path.resolve()
        logger.debug(f"Root path={root_as_path}")
        return root_as_path
    else:
        raise ValueError(f"Directory not valid: '{root_dir}'.")


def main(root_dir: Path, filters: Filters = None) -> None:
    """Construct and print directory tree."""
    nodes: Tree = Tree(root_dir, filters)
    print(nodes)
    with open("results.txt", 'wt', encoding='utf-8') as fp:
        fp.write(str(nodes))


if __name__ == '__main__':
    test_dir = "../testing_data/Test_3"

    try:
        root_path = validate_root_path(test_dir)
    except ValueError as exc:
        print(f"{exc}")
        sys.exit(1)

    excluded = Filters(exclude_hidden_dirs=False,
                       # exclude_dirs=['v*'],
                       exclude_hidden_files=False)
    main(root_path, excluded)
