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
from ascii_tree.config import TreeGenConfig, SymbolType
from ascii_tree.validate import resolve_directory_path

configure_logging()
logger = logging.getLogger(LOGGER_NAME)


SYMBOL_LEN = 4
"""int: The length of all "prefix" symbols is 4 characters."""


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

    def __init__(self, config: TreeGenConfig) -> None:
        """Initialise Tree instance."""
        self.config = config
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
                output_strings = append_file_lines(
                    output_strings, parent, self.config.symbols)

            # Add directory line and push to stack if it has files
            output_strings.append(
                f"{node.prefix}{node.name}{self.config.symbols.DIR.value}")
            if node.files:
                stack.append(node)

        # Flush any remaining files after processing all nodes
        while stack:
            parent = stack.pop()
            output_strings = append_file_lines(
                output_strings, parent, self.config.symbols)

        return '\n'.join(output_strings)

    def populate(self):
        """Add Nodes to Tree."""
        print(self.config.root_dir)
        root_depth = len(self.config.root_dir.parts)
        for root, dirs, files in os.walk(self.config.root_dir):
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
        if self.config.filters is None:
            return sorted(files)
        include = self.config.filters.include_files
        exclude = self.config.filters.exclude_files
        return sorted(self.do_filter(files, include, exclude))

    def filter_dirs(self, directories: list[str]) -> list[str]:
        """Filter and sort directories as required.

        Returns:
            list[str]: The sorted and filtered directory list.
        """
        if self.config.filters is None:
            return sorted(directories)
        include = self.config.filters.include_dirs
        exclude = self.config.filters.exclude_dirs
        return sorted(self.do_filter(directories, include, exclude))

    def prefix_nodes(self) -> None:
        """Assign visual prefix to each Node in the Tree."""
        for dir_path, node in self.nodes.items():
            try:
                parent_node = self.nodes[dir_path.parent]
            except KeyError:  # Top level does not have a parent.
                if dir_path == self.config.root_dir:
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

            node.prefix = transform_prefix(parent_node, self.config.symbols)


def transform_trailing_prefix(prefix: str,
                              symbols: SymbolType) -> str:
    """Replace final symbol for proper continuation to next level."""
    prefix = replace_trailing_symbol(prefix, symbols.CONTINUE, symbols.BRANCH)
    prefix = replace_trailing_symbol(prefix, symbols.INDENT, symbols.FINAL)
    return prefix


def transform_prefix(parent: Node, symbols: SymbolType) -> str:
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
        symbols: ASCII or Unicode symbol Enum.

    Returns:
        str: The constructed prefix for the node.
        symbols: ASCII or Unicode symbol Enums.
    """
    new_prefix = transform_trailing_prefix(parent.prefix, symbols)
    new_prefix = replace_leading_symbol(new_prefix, symbols.CONTINUE, symbols.BRANCH)

    parent_has_siblings = parent.dirs or parent.files
    if parent_has_siblings:
        new_prefix += symbols.BRANCH.value
    else:
        new_prefix += symbols.FINAL.value

    return new_prefix


def append_file_lines(file_lines: list[str], node: Node, symbols) -> list[str]:
    """Append file lines, ensuring termination with FINAL prefix.

    The file prefix is derived from its parent by replacing the final
    Symbol BRANCH to CONTINUE, or FINAL to INDENT, then adding a Symbol for
    the file itself.

    Raises:
        SystemExit: If `node.files` is empty (unexpected state).

    Returns:
        list[str]: The updated list.
    """
    file_prefix = transform_trailing_prefix(node.prefix, symbols)

    try:
        for file in node.files[:-1]:
            file_lines.append(f'{file_prefix}{symbols.BRANCH.value}{file}')
        file_lines.append(f'{file_prefix}{symbols.FINAL.value}{node.files[-1]}')
    except IndexError:
        logger.critical("Unexpected empty files list in node: %s (path: %s).",
                        node.name, node.dir_path)
        sys.exit(1)

    return file_lines


def replace_leading_symbol(
        prefix: str, new_symbol: Enum, match_symbol: Enum) -> str:
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
        prefix: str, new_symbol: Enum, match_symbol: Enum) -> str:
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


def main(config: TreeGenConfig) -> None:
    """Construct and print directory tree.

    Args:
        config: A TreeGenConfig object holding configuration options.
    """
    nodes: Tree = Tree(config)
    print(nodes)
    with open("results.txt", 'wt', encoding='utf-8') as fp:
        fp.write(str(nodes))


if __name__ == '__main__':
    default_config = TreeGenConfig()
    main(default_config)
