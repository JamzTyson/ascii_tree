"""Project idea based on: https://github.com/rahulbordoloi/Directory-Tree/"""
import logging
import os
from dataclasses import dataclass
from enum import Enum
from itertools import pairwise
from pathlib import Path

from ascii_tree.logging_config import configure_logging, LOGGER_NAME


configure_logging()
logger = logging.getLogger(LOGGER_NAME)


@dataclass
class Excluded:
    """Boolean flags to ignore some files / directories."""
    HIDDEN_DIRS: bool = True
    HIDDEN_FILES: bool = True
    # Not currently used.
    # Will contain patterns that can be filtered by fnmatch.fnmatch
    # EXCLUDED_DIRS: list[str] = []
    # EXCLUDED_FILES: list[str] = []


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

    def __init__(self, top: Path, ignore_types: Excluded) -> None:
        self.top = top
        self.ignore = ignore_types
        self.nodes: dict[Path, Node] = {}
        self.populate()
        self.prefix_nodes()

    def __str__(self) -> str:
        """Return tree as formatted string."""
        output_strings: list[str] = []
        files_to_add_nodes: list[Node] = []

        # We need to keep track of which Node's files have been added to
        # `output_strings`, so that we can remove the node from
        # `files_to_add_nodes` after iterating over it.
        files_added_nodes: list[Node] = []

        for node, next_node in pairwise(self.nodes.values()):
            output_strings.append(
                f'{node.prefix}{node.name}{Symbol.DIR.value}')

            if node.files:
                files_to_add_nodes.append(node)

            for file_node in reversed(files_to_add_nodes):
                # Check if we can add file output_strings yet.
                # Iterating in reverse to retain correct insertion order.
                if file_node.depth >= next_node.depth:
                    output_strings = append_file_lines(output_strings, file_node)
                    files_added_nodes.append(file_node)  # Marked for removal.

            # Remove nodes from `files_to_add_nodes` after they have been added
            # to `output_strings`.
            for n in files_added_nodes:
                files_to_add_nodes.remove(n)
            files_added_nodes.clear()

        # End of pairwise loop.

        last_node = next(reversed(self.nodes.values()))
        output_strings.append(f'{last_node.prefix}{
                              last_node.name}{Symbol.DIR.value}')

        if last_node.files:
            # We can add directly as there are no more directories.
            output_strings = append_file_lines(output_strings, last_node)

        # Add any remaining files.
        for file_node in reversed(files_to_add_nodes):
            output_strings = append_file_lines(output_strings, file_node)

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

    def filter_files(self, files: list[str]) -> list[str]:
        """Filter and sort files as required.

        Returns:
            list[str]: The sorted and filtered file list.
        """
        if self.ignore.HIDDEN_FILES:
            files = sorted(
                [f for f in files if not f.startswith('.')])
            return files
        return sorted(files)

    def filter_dirs(self, directories: list[str]) -> list[str]:
        """Filter and sort directories as required.

        Returns:
            list[str]: The sorted and filtered directory list.
        """
        if self.ignore.HIDDEN_DIRS:
            directories = sorted(
                [d for d in directories if not d.startswith('.')])
            return directories
        return sorted(directories)

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
            except ValueError as exc:
                logger.warning(
                    "Failed to remove '{}' from parent '{}' dirs. "
                    "Current dirs: {}. {}".format(
                        node.name, parent_node.name, parent_node.dirs, exc))

            node.prefix = transform_prefix(parent_node)


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
    new_prefix = parent.prefix

    transformations = [
        (Symbol.BRANCH, Symbol.CONTINUE, False),  # Leading BRANCH → CONTINUE
        (Symbol.BRANCH, Symbol.CONTINUE, True),  # Trailing BRANCH → CONTINUE
        (Symbol.FINAL, Symbol.INDENT, True),  # Trailing FINAL → INDENT
    ]
    for old_symbol, new_symbol, reverse in transformations:
        new_prefix = replace_symbol(
            new_prefix, new_symbol, old_symbol, reverse)

    parent_has_siblings = parent.dirs or parent.files
    if parent_has_siblings:
        new_prefix += Symbol.BRANCH.value
    else:
        new_prefix += Symbol.FINAL.value

    return new_prefix


def append_file_lines(
        file_lines: list[str], node: Node) -> list[str]:
    """Append file lines, ensuring termination with FINAL prefix.

    The file prefix is derived from its parent by replacing the final
    Symbol BRANCH to CONTINUE, or FINAL to INDENT, then adding a Symbol for
    the file itself.

    Returns:
        list[str]: The updated list.
    """
    file_prefix = node.prefix

    transformations = [
        (Symbol.BRANCH, Symbol.CONTINUE, True),  # Trailing BRANCH -> CONTINUE
        (Symbol.FINAL, Symbol.INDENT, True),  # Trailing FINAL -> INDENT
    ]
    for old_symbol, new_symbol, reverse in transformations:
        file_prefix = replace_symbol(
            file_prefix, new_symbol, old_symbol, reverse)

    for file in node.files[:-1]:
        file_lines.append(f'{file_prefix}{Symbol.BRANCH.value}{file}')
    file_lines.append(f'{file_prefix}{Symbol.FINAL.value}{node.files[-1]}')
    return file_lines


def replace_symbol(prefix: str,
                   new_symbol: Symbol,
                   old_symbol: Symbol,
                   reverse: bool = False) -> str:
    """Replace initial or final symbol in prefix string.

    Args:
        prefix: The prefix to modify.
        new_symbol: The new symbol to use.
        old_symbol: If present, the symbol will only be replaced if it matches.
            Default = None.
        reverse: If True, replace the final symbol, else replace the first.
            Default = False.

    Returns:
        str: The modified string.
    """
    if reverse:
        if old_symbol.value == prefix[-SYMBOL_LEN:]:
            return prefix[:-SYMBOL_LEN] + new_symbol.value

    if prefix.startswith(str(old_symbol.value)):
        return new_symbol.value + prefix[SYMBOL_LEN:]
    return prefix


def main(root_dir: Path, exclude: Excluded) -> None:
    """Construct and print directory tree."""
    nodes: Tree = Tree(root_dir, exclude)
    print(nodes)
    with open("results.txt", 'wt', encoding='utf-8') as fp:
        fp.write(str(nodes))


if __name__ == '__main__':
    root_path = Path("../testing_data/Test_1")

    if root_path.exists() and root_path.is_dir():
        root_path = root_path.resolve()
        logger.debug(f"Root path={root_path}")

        excluded = Excluded()
        main(root_path, excluded)
    else:
        print("Directory not valid.")
