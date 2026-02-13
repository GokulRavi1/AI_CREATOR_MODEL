"""
File Manager — I/O helpers for outputs, models, and directory management.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional


# Project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def ensure_dirs():
    """Create all required project directories if they don't exist."""
    dirs = [
        "models", "models/loras", "models/sadtalker", "models/checkpoints",
        "datasets",
        "workflows",
        "outputs", "outputs/images", "outputs/videos", "outputs/avatars", "outputs/audio",
        "logs",
    ]
    for d in dirs:
        (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)


def get_timestamped_filename(prefix: str = "output", extension: str = "png") -> str:
    """Generate a timestamped filename like 'output_20260212_141958.png'."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{extension}"


def save_output(data: bytes, category: str, extension: str = "png", prefix: str = "gen") -> str:
    """
    Save binary output data to the appropriate outputs subdirectory.

    Args:
        data:      Binary content to write
        category:  Subdirectory name ('images', 'videos', 'avatars', 'audio')
        extension: File extension
        prefix:    Filename prefix

    Returns:
        Relative path to the saved file.
    """
    output_dir = PROJECT_ROOT / "outputs" / category
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = get_timestamped_filename(prefix, extension)
    filepath = output_dir / filename

    with open(filepath, "wb") as f:
        f.write(data)

    return str(filepath.relative_to(PROJECT_ROOT))


def list_models(model_type: str = "loras") -> List[dict]:
    """
    List model files in the given models subdirectory.

    Args:
        model_type: Subdirectory name ('loras', 'checkpoints', 'sadtalker')

    Returns:
        List of dicts with 'name', 'size_mb', and 'path' for each model file.
    """
    model_dir = PROJECT_ROOT / "models" / model_type
    if not model_dir.exists():
        return []

    valid_extensions = {".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".onnx"}
    models = []

    for f in model_dir.iterdir():
        if f.is_file() and f.suffix.lower() in valid_extensions:
            size_mb = f.stat().st_size / (1024 * 1024)
            models.append({
                "name": f.name,
                "size_mb": round(size_mb, 2),
                "path": str(f.relative_to(PROJECT_ROOT)),
            })

    return sorted(models, key=lambda m: m["name"])


def list_outputs(category: str = "images", limit: int = 20) -> List[dict]:
    """
    List recent output files in a category, newest first.

    Args:
        category: Subdirectory name ('images', 'videos', 'avatars', 'audio')
        limit:    Maximum number of results

    Returns:
        List of dicts with 'name', 'path', 'size_mb', and 'created' for each file.
    """
    output_dir = PROJECT_ROOT / "outputs" / category
    if not output_dir.exists():
        return []

    files = []
    for f in output_dir.iterdir():
        if f.is_file() and f.name != ".gitkeep":
            stat = f.stat()
            files.append({
                "name": f.name,
                "path": str(f.relative_to(PROJECT_ROOT)),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })

    files.sort(key=lambda x: x["created"], reverse=True)
    return files[:limit]


def cleanup_old_outputs(category: str, keep_count: int = 100):
    """
    Remove oldest output files, keeping only the most recent `keep_count`.
    Useful for auto-cleaning renders to save disk space.
    """
    output_dir = PROJECT_ROOT / "outputs" / category
    if not output_dir.exists():
        return

    files = [
        f for f in output_dir.iterdir()
        if f.is_file() and f.name != ".gitkeep"
    ]
    files.sort(key=lambda f: f.stat().st_ctime, reverse=True)

    for old_file in files[keep_count:]:
        old_file.unlink()
