"""Configuration options."""
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


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
        use_ascii: Whether to use ASCII symbols.
    """
    use_ascii: bool = False
    root_dir: Path = Path('.').resolve()
    include_hidden_dirs: bool = False
    include_hidden_files: bool = False
    include_files: None | re.Pattern = None
    exclude_files: None | re.Pattern = None
    include_dirs: None | re.Pattern = None
    exclude_dirs: None | re.Pattern = None
    terminal_output: bool = True
    output_file: Path | None = None
    debug: bool = False
    verbose: bool = False
    log_level: str = ''

    @property
    def symbols(self):
        """
        Choose the appropriate symbol enum based on the `use_ascii` flag.
        """
        return AsciiSymbols if self.use_ascii else UnicodeSymbols
