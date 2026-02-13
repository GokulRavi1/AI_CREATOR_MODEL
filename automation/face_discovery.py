"""
Face Discovery — Interactive guide & prompt generator for character identity.

Since the user provides their own images, this module helps them:
- Understand what face images are needed
- Generate a checklist of required shots
- Create organized prompt suggestions for reference photography
- Validate face image coverage
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from backend.utils.file_manager import PROJECT_ROOT


# ── Shot Checklist ──────────────────────────────────────────────

FACE_SHOT_CHECKLIST = [
    # Angles
    {"category": "angle", "shot": "Front face (looking straight at camera)", "priority": "required"},
    {"category": "angle", "shot": "3/4 view (slightly turned left)", "priority": "required"},
    {"category": "angle", "shot": "3/4 view (slightly turned right)", "priority": "required"},
    {"category": "angle", "shot": "Profile (side view left)", "priority": "recommended"},
    {"category": "angle", "shot": "Profile (side view right)", "priority": "recommended"},
    {"category": "angle", "shot": "Slightly looking up", "priority": "optional"},
    {"category": "angle", "shot": "Slightly looking down", "priority": "optional"},

    # Expressions
    {"category": "expression", "shot": "Neutral expression", "priority": "required"},
    {"category": "expression", "shot": "Natural smile", "priority": "required"},
    {"category": "expression", "shot": "Serious / thoughtful", "priority": "recommended"},
    {"category": "expression", "shot": "Laughing / joyful", "priority": "optional"},
    {"category": "expression", "shot": "Subtle smirk", "priority": "optional"},

    # Lighting
    {"category": "lighting", "shot": "Even studio-style lighting", "priority": "required"},
    {"category": "lighting", "shot": "Natural daylight", "priority": "required"},
    {"category": "lighting", "shot": "Golden hour / warm light", "priority": "recommended"},
    {"category": "lighting", "shot": "Indoor ambient light", "priority": "recommended"},
]


def get_face_checklist() -> dict:
    """Return the face photography checklist with priority levels."""
    required = [s for s in FACE_SHOT_CHECKLIST if s["priority"] == "required"]
    recommended = [s for s in FACE_SHOT_CHECKLIST if s["priority"] == "recommended"]
    optional = [s for s in FACE_SHOT_CHECKLIST if s["priority"] == "optional"]

    return {
        "total_shots": len(FACE_SHOT_CHECKLIST),
        "required": {"count": len(required), "shots": required},
        "recommended": {"count": len(recommended), "shots": recommended},
        "optional": {"count": len(optional), "shots": optional},
        "tips": [
            "Aim for 10–15 face close-up images total",
            "Cover at least all 'required' shots",
            "Clean background makes training easier",
            "Consistent hairstyle across shots is important",
            "Good, even lighting without harsh shadows",
            "No sunglasses, masks, or heavy face covering",
        ],
    }


# ── Body Shot Checklist ─────────────────────────────────────────

BODY_SHOT_CHECKLIST = [
    # Poses
    {"category": "pose", "shot": "Standing straight (front)", "priority": "required"},
    {"category": "pose", "shot": "Standing straight (3/4 angle)", "priority": "required"},
    {"category": "pose", "shot": "Casual standing (relaxed)", "priority": "required"},
    {"category": "pose", "shot": "Sitting on chair", "priority": "recommended"},
    {"category": "pose", "shot": "Sitting casually", "priority": "recommended"},
    {"category": "pose", "shot": "Walking naturally", "priority": "recommended"},
    {"category": "pose", "shot": "Leaning against wall", "priority": "optional"},
    {"category": "pose", "shot": "Arms crossed", "priority": "optional"},

    # Framing
    {"category": "framing", "shot": "Full body (head to toe)", "priority": "required"},
    {"category": "framing", "shot": "Mid-body (waist up)", "priority": "required"},
    {"category": "framing", "shot": "Full body from slight distance", "priority": "recommended"},
    {"category": "framing", "shot": "Mid-body with arm gestures", "priority": "optional"},
]


def get_body_checklist() -> dict:
    """Return the body photography checklist with priority levels."""
    required = [s for s in BODY_SHOT_CHECKLIST if s["priority"] == "required"]
    recommended = [s for s in BODY_SHOT_CHECKLIST if s["priority"] == "recommended"]
    optional = [s for s in BODY_SHOT_CHECKLIST if s["priority"] == "optional"]

    return {
        "total_shots": len(BODY_SHOT_CHECKLIST),
        "required": {"count": len(required), "shots": required},
        "recommended": {"count": len(recommended), "shots": recommended},
        "optional": {"count": len(optional), "shots": optional},
        "tips": [
            "Aim for 10–20 mid-body and full-body images total",
            "Show consistent body proportions across shots",
            "Variety of outfits helps the model generalize",
            "Natural, relaxed poses work best",
            "Outdoor and indoor settings add diversity",
            "Avoid heavily cropped or awkward compositions",
        ],
    }


def get_full_shooting_guide() -> dict:
    """
    Complete photography guide for the user to shoot their own reference images.
    Returns a structured guide with face + body checklists and preparation steps.
    """
    return {
        "title": "Character Reference Photography Guide",
        "overview": (
            "This guide helps you take or collect the optimal set of reference "
            "photos for training your AI character model. The goal is 30–50 images "
            "covering faces, mid-body, and full-body from various angles."
        ),
        "face": get_face_checklist(),
        "body": get_body_checklist(),
        "after_shooting": [
            "1. Copy all images to the datasets/{character_name}/ folder",
            "2. Run the dataset validator to check coverage",
            "3. Use the resize tool to standardize to 512×512",
            "4. Run auto-captioning with your trigger word",
            "5. Review and adjust captions as needed",
        ],
        "common_mistakes": [
            "Too few images (under 20) — model won't learn identity well",
            "All same angle — model can't generalize to new poses",
            "Heavy filters/editing — model learns the filter, not the person",
            "Multiple people in frame — model gets confused about identity",
            "Very dark or blown-out lighting — model can't see features",
            "Inconsistent identity (mixing different time periods with different looks)",
        ],
    }


def save_guide_json(character_name: str) -> str:
    """
    Save the full shooting guide as a JSON file in the character's dataset folder.
    Returns the file path.
    """
    guide = get_full_shooting_guide()
    guide["character_name"] = character_name
    guide["generated_at"] = datetime.now().isoformat()

    output_dir = PROJECT_ROOT / "datasets" / character_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "shooting_guide.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(guide, f, indent=2, ensure_ascii=False)

    return str(output_path)
