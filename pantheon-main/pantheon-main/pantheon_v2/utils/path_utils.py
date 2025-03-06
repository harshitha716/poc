import re
from pathlib import Path


def sanitize_filename(filename: str, extension: str) -> str:
    """
    Remove special characters and spaces from filename.

    Args:
        filename: The original filename including extension

    Returns:
        A sanitized version of the filename with special characters replaced by underscores
    """
    # Get the stem (filename without extension) and extension
    path = Path(filename)
    stem = path.stem

    # Replace special characters and spaces with underscore
    sanitized_stem = re.sub(r"[^a-zA-Z0-9]", "_", stem)

    # Remove consecutive underscores
    sanitized_stem = re.sub(r"_+", "_", sanitized_stem)

    # Remove leading/trailing underscores
    sanitized_stem = sanitized_stem.strip("_")

    return f"{sanitized_stem}_transformed{extension}"
