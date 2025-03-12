"""Validators."""

from pathlib import Path


def resolve_directory_path(root_dir: str) -> Path:
    """Validate a directory exists and return as an absolute path.

    Raises:
        ValueError: root_dir argument is not a valid file path.

    Returns:
        Path: Absolute Path
    """
    root_as_path = Path(root_dir)

    if root_as_path.exists() and root_as_path.is_dir():
        root_as_path = root_as_path.resolve()
        return root_as_path
    else:
        raise ValueError(f"Directory not valid: '{root_dir}'.")


def validate_file_path(file_path: Path) -> Path:
    """Ensure file directory exists and is writable.

    Args:
        file_path: The path to validate.

    Raises:
        OSError: On any filesystem error that prevents writing.

    Return:
        Absolute path, resolved from file_path.
    """
    resolved_path = file_path.expanduser().resolve()
    file_exist = resolved_path.exists()

    try:
        resolved_path.touch(exist_ok=True)
    except OSError:
        raise OSError(f"Invalid file path '{file_path}' ({resolved_path})")
    finally:
        if not file_exist and resolved_path.exists():
            # Avoid masking original error if (unlikely) failure.
            try:
                resolved_path.unlink()
            except OSError:
                pass
    return resolved_path
