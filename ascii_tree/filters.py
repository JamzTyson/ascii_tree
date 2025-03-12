"""Manages file and directory filtering."""

import fnmatch
import re


PatternInput = str | list[str] | None  # Alias for pattern input.


class Filters:
    """Manage file and directory filters."""
    unix_hidden = '.*'

    def __init__(
            self,
            show_hidden_files: bool = False,
            show_hidden_dirs: bool = False,
            include_files: PatternInput = None,
            exclude_files: PatternInput = None,
            include_dirs: PatternInput = None,
            exclude_dirs: PatternInput = None,
    ) -> None:
        """Initialise Unix-style filename patterns.

        Args:
            show_hidden_files: Whether to show hidden directories.
            show_hidden_dirs: Whether to show hidden files.
            include_dirs: Patterns to include directories.
            include_files: Patterns to include files.
            exclude_dirs: Patterns to exclude directories.
            exclude_files: Patterns to exclude files.
        """
        if not show_hidden_files:
            exclude_files = self.append_pattern(exclude_files, Filters.unix_hidden)
        if not show_hidden_dirs:
            exclude_dirs = self.append_pattern(exclude_dirs, Filters.unix_hidden)

        self._include_files = _sanitize_patterns(include_files)
        self._exclude_files = _sanitize_patterns(exclude_files)

        self._include_dirs = _sanitize_patterns(include_dirs)
        self._exclude_dirs = _sanitize_patterns(exclude_dirs)

    @staticmethod
    def append_pattern(pattern: PatternInput, item: str) -> PatternInput:
        """Safely append a string to PatternInput."""
        if pattern is None:
            return item
        if isinstance(pattern, str):
            return [pattern, item]
        return pattern.append(item)

    # File Filters.
    @property
    def include_files(self) -> re.Pattern | None:
        """Return a single regex for file inclusion patterns."""
        return _combine_patterns(self._include_files)

    @include_files.setter
    def include_files(self, patterns: PatternInput) -> None:
        """Set list of patterns that define included directories.

        Raises:
            ValueError: if `patterns` is invalid.
        """
        self._include_files = _sanitize_patterns(patterns)

    @property
    def exclude_files(self) -> re.Pattern | None:
        """Return a single regex for file exclusion patterns."""
        return _combine_patterns(self._exclude_files)

    @exclude_files.setter
    def exclude_files(self, patterns: PatternInput) -> None:
        """Set list of patterns that define excluded files.

        Raises:
            ValueError: if `patterns` is invalid.
        """
        self._exclude_files = _sanitize_patterns(patterns)

    # Directory filters:
    @property
    def include_dirs(self) -> re.Pattern | None:
        """Return a single regex for directory inclusion patterns."""
        return _combine_patterns(self._include_dirs)

    @include_dirs.setter
    def include_dirs(self, patterns: PatternInput) -> None:
        """Set list of patterns that define included directories.

        Raises:
            ValueError: if `patterns` is invalid.
        """
        self._include_dirs = _sanitize_patterns(patterns)

    @property
    def exclude_dirs(self) -> re.Pattern | None:
        """Return a single regex for directory exclusion patterns."""
        return _combine_patterns(self._exclude_dirs)

    @exclude_dirs.setter
    def exclude_dirs(self, patterns: PatternInput) -> None:
        """Set list of patterns that define excluded directories.

        Raises:
            ValueError: if `patterns` is invalid.
        """
        self._exclude_dirs = _sanitize_patterns(patterns)


def _sanitize_patterns(patterns: PatternInput) -> list[str]:
    """Ensure patterns are in a list of unique strings.

    Args:
        patterns: A single string, a list of strings, or None.

    Returns:
        A list of strings.

    Raises:
        ValueError: If the input is not a string, a list of strings, or None.
    """
    if patterns is None:
        return []

    if isinstance(patterns, str):
        return [patterns]

    if isinstance(patterns, list) and all(isinstance(p, str) for p in patterns):
        return list(set(patterns))  # Remove duplicates.

    raise ValueError(f"Invalid pattern in {patterns}.")


def _combine_patterns(patterns: list[str]) -> re.Pattern | None:
    """Combine multiple wildcard patterns into a single regex."""
    if not patterns:
        return None
    if len(patterns) == 1:
        return re.compile(fnmatch.translate(patterns[0]))
    combined = "|".join(fnmatch.translate(pattern) for pattern in patterns)
    return re.compile(combined)
