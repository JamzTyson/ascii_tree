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


def validate_file_path(file_path: Path) -> None:
    """Ensure file directory exists and is writable.

    Creates the immediate parent directory if missing, but to
    prevent accidental deep directory creation, it does
    not create other missing directories.

    Args:
        file_path: The path to validate.

    Raises:
        OSError: On any filesystem error that prevents writing.
    """
    file_exist = file_path.exists()

    try:
        file_path.parent.mkdir(exist_ok=True, parents=False)
        file_path.touch(exist_ok=False)
    except OSError as exc:
        raise OSError(f"Invalid file path '{file_path}': {exc}") from exc
    finally:
        if not file_exist and file_path.exists():
            # Avoid masking original error if (unlikely) failure.
            try:
                file_path.unlink()
            except OSError:
                pass
