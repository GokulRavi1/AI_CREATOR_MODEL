"""
Character Manager — Save, Load, and Switch AI Character Identities

Manages character metadata, LoRA associations, and active character state.
Characters are stored as JSON metadata files in models/characters/{name}/.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime

from backend.utils.file_manager import PROJECT_ROOT


CHARACTERS_DIR = PROJECT_ROOT / "models" / "characters"


@dataclass
class Character:
    """Represents a trained AI character identity."""
    name: str
    trigger_word: str
    lora_path: str = ""
    lora_weight: float = 0.8
    preview_image: str = ""
    description: str = ""
    training_params: dict = field(default_factory=dict)
    dataset_path: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


# Active character state
_active_character: Optional[str] = None


def _char_dir(name: str) -> Path:
    """Get the directory for a character."""
    return CHARACTERS_DIR / name


def _metadata_path(name: str) -> Path:
    """Get the metadata file path for a character."""
    return _char_dir(name) / "metadata.json"


def save_character(character: Character) -> dict:
    """
    Save a character's metadata to disk.

    Creates the character directory and writes metadata.json.
    """
    now = datetime.now().isoformat()
    if not character.created_at:
        character.created_at = now
    character.updated_at = now

    char_dir = _char_dir(character.name)
    char_dir.mkdir(parents=True, exist_ok=True)

    data = asdict(character)
    with open(_metadata_path(character.name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {
        "success": True,
        "message": f"Character '{character.name}' saved",
        "path": str(char_dir),
    }


def load_character(name: str) -> Optional[Character]:
    """Load a character from disk by name."""
    meta_path = _metadata_path(name)
    if not meta_path.exists():
        return None

    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Character(**data)


def list_characters() -> List[dict]:
    """List all saved characters with their metadata."""
    if not CHARACTERS_DIR.exists():
        return []

    characters = []
    for char_dir in sorted(CHARACTERS_DIR.iterdir()):
        if char_dir.is_dir():
            meta_path = char_dir / "metadata.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    characters.append(data)
                except Exception:
                    characters.append({
                        "name": char_dir.name,
                        "error": "Could not read metadata",
                    })

    return characters


def delete_character(name: str) -> dict:
    """Delete a character and all its data."""
    import shutil

    char_dir = _char_dir(name)
    if not char_dir.exists():
        return {"success": False, "error": f"Character '{name}' not found"}

    shutil.rmtree(char_dir)

    global _active_character
    if _active_character == name:
        _active_character = None

    return {"success": True, "message": f"Character '{name}' deleted"}


def get_active_character() -> Optional[dict]:
    """Get the currently active character."""
    global _active_character
    if _active_character is None:
        return None

    char = load_character(_active_character)
    if char:
        return asdict(char)
    return None


def set_active_character(name: str) -> dict:
    """Set a character as the active/current character."""
    global _active_character

    char = load_character(name)
    if char is None:
        return {"success": False, "error": f"Character '{name}' not found"}

    _active_character = name
    return {
        "success": True,
        "message": f"Active character set to '{name}'",
        "character": asdict(char),
    }


def update_character(name: str, updates: dict) -> dict:
    """
    Update specific fields of a character.

    Args:
        name:    Character name
        updates: Dict of fields to update

    Returns:
        Result dict with success status.
    """
    char = load_character(name)
    if char is None:
        return {"success": False, "error": f"Character '{name}' not found"}

    # Apply updates
    for key, value in updates.items():
        if hasattr(char, key) and key not in ("name", "created_at"):
            setattr(char, key, value)

    return save_character(char)


def register_trained_lora(name: str, lora_filename: str) -> dict:
    """
    Register a trained LoRA file with an existing character.

    Looks for the file in models/loras/ and updates the character metadata.
    """
    lora_path = PROJECT_ROOT / "models" / "loras" / lora_filename
    if not lora_path.exists():
        return {
            "success": False,
            "error": f"LoRA file not found: {lora_filename}. "
                     f"Expected in models/loras/",
        }

    char = load_character(name)
    if char is None:
        return {"success": False, "error": f"Character '{name}' not found"}

    char.lora_path = str(lora_path.relative_to(PROJECT_ROOT))
    return save_character(char)


def create_character(
    name: str,
    trigger_word: str,
    description: str = "",
    lora_path: str = "",
    lora_weight: float = 0.8,
    tags: Optional[List[str]] = None,
) -> dict:
    """
    Create a new character with the given parameters.

    Also creates the dataset directory for the character.
    """
    # Check if exists
    if _metadata_path(name).exists():
        return {"success": False, "error": f"Character '{name}' already exists"}

    character = Character(
        name=name,
        trigger_word=trigger_word,
        description=description,
        lora_path=lora_path,
        lora_weight=lora_weight,
        dataset_path=str(PROJECT_ROOT / "datasets" / name),
        tags=tags or [],
    )

    # Create dataset directory too
    dataset_dir = PROJECT_ROOT / "datasets" / name
    dataset_dir.mkdir(parents=True, exist_ok=True)

    return save_character(character)
