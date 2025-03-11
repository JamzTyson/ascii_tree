"""Configuration options."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ascii_tree.filters import Filters


class UnicodeSymbols(Enum):
    """Indentation symbols."""
    INDENT = '    '
    CONTINUE = '│   '
    BRANCH = '├── '
    FINAL = '└── '
    DIR = '/'


class AsciiSymbols(Enum):
    """Indentation symbols."""
    INDENT = '    '
    CONTINUE = '|   '
    BRANCH = '+-- '
    FINAL = '+-- '
    DIR = '/'


SymbolType = type[UnicodeSymbols] | type[AsciiSymbols]


@dataclass
class TreeGenConfig:
    """Configuration for the tree generator.

    Attributes:
        root_dir : Path
            Root of directory tree (default=current directory).
        filters: Filters
            File and directory filters (default=None).
        terminal_output : bool
            Print tree to console when True (default=True).
        output_file : Path
            Output file (default=None).
        debug : bool
            Show debug messages when True (default=False)
        verbose : bool
            Include additional header info when True (default=True).
        log_level : str
            Logging level (default: CRITICAL).
        use_ascii : bool
            Whether to use ASCII symbols (default=False).
    """
    root_dir: Path = Path('.').resolve()
    max_depth: int = -1  # Unrestricted.
    dirs_only: bool = False
    filters: Filters = Filters()
    terminal_output: bool = True
    output_file: Path | None = None
    use_ascii: bool = False
    # TODO:
    debug: bool = False
    verbose: bool = False
    log_level: str = 'CRITICAL'

    @property
    def symbols(self):
        """
        Choose the appropriate symbol enum based on the `use_ascii` flag.
        """
        return AsciiSymbols if self.use_ascii else UnicodeSymbols
