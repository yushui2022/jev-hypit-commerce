from pathlib import Path

ALLOWED = (
    "examples/assets/",
    "productions/hd-fast/assets/",
    "productions/advanced/assets/",
    "productions/matrix-ugc/videos/",
)
SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".wav"}


def media_path(root, path):
    root = Path(root).resolve()
    resolved = (root / path).resolve()
    if (
        not any(path.startswith(prefix) for prefix in ALLOWED)
        or not resolved.is_relative_to(root)
        or any(p == ".." for p in Path(path).parts)
        or resolved.suffix.lower() not in SUFFIXES
        or not resolved.is_file()
    ):
        raise KeyError("Media not found")
    # Resolve symlinks against the same allowlisted directories.
    if not any(resolved.is_relative_to((root / p).resolve()) for p in ALLOWED):
        raise KeyError("Media not found")
    return resolved
