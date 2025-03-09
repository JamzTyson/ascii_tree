"""Configuration options."""
import re
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
        use_ascii : bool
            Whether to use ASCII symbols (default=False).
        root_dir : Path
            Path to root of directory tree (default=current directory).
        filters: Filters
            File and directory filters (default=None).
        terminal_output : bool
            Print tree to console when True (default=True).
        output_file : Path
            Path to output file (default=None).
        debug : bool
            Show debug messages when True (default=False)
        verbose : bool
            Include additional header info when True (default=True).
        log_level : str
            Logging level (default: CRITICAL).
    """
    use_ascii: bool = False
    root_dir: Path = Path('.').resolve()
    filters: Filters | None = None
    terminal_output: bool = True
    output_file: Path | None = None
    debug: bool = False
    verbose: bool = False
    log_level: str = 'CRITICAL'

    @property
    def symbols(self):
        """
        Choose the appropriate symbol enum based on the `use_ascii` flag.
        """
        return AsciiSymbols if self.use_ascii else UnicodeSymbols
