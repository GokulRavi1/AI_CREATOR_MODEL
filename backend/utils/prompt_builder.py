"""
Prompt Builder — Template-based prompt construction for Stable Diffusion.

Builds formatted prompts with LoRA injection, scene descriptions,
camera styles, and negative prompt handling.
"""

from typing import Optional, List
import random


# ── Preset Libraries ──────────────────────────────────────────────

CAMERA_STYLES = [
    "cinematic shot", "close-up portrait", "wide angle", "medium shot",
    "bird's eye view", "low angle", "dutch angle", "macro shot",
    "over the shoulder", "bokeh background",
]

LIGHTING_STYLES = [
    "natural lighting", "golden hour", "studio lighting", "dramatic lighting",
    "soft diffused light", "neon lighting", "backlit", "rim lighting",
    "overcast ambient", "candlelight",
]

QUALITY_TAGS = "masterpiece, best quality, highly detailed, sharp focus, 8k uhd"

DEFAULT_NEGATIVE = (
    "blurry, low quality, distorted, deformed, disfigured, bad anatomy, "
    "bad hands, missing fingers, extra fingers, watermark, text, logo, "
    "cropped, out of frame, worst quality, low resolution, jpeg artifacts"
)


def build_prompt(
    character: Optional[str] = None,
    lora_name: Optional[str] = None,
    lora_weight: float = 0.8,
    location: str = "",
    activity: str = "",
    camera_style: Optional[str] = None,
    lighting: Optional[str] = None,
    style_modifiers: Optional[List[str]] = None,
    include_quality_tags: bool = True,
) -> str:
    """
    Build a full Stable Diffusion prompt string.

    Args:
        character:    Character description / trigger word
        lora_name:    LoRA filename (without extension) to inject
        lora_weight:  LoRA weight (0.0–1.0)
        location:     Scene/environment description
        activity:     What the character is doing
        camera_style: Camera framing (or random if None)
        lighting:     Lighting style (or random if None)
        style_modifiers: Extra style tags

    Returns:
        Formatted prompt string ready for SD generation.
    """
    parts = []

    # LoRA trigger
    if lora_name:
        parts.append(f"<lora:{lora_name}:{lora_weight}>")

    # Character
    if character:
        parts.append(character)

    # Scene
    if activity:
        parts.append(activity)
    if location:
        parts.append(location)

    # Camera
    cam = camera_style or random.choice(CAMERA_STYLES)
    parts.append(cam)

    # Lighting
    light = lighting or random.choice(LIGHTING_STYLES)
    parts.append(light)

    # Style modifiers
    if style_modifiers:
        parts.extend(style_modifiers)

    # Quality
    if include_quality_tags:
        parts.append(QUALITY_TAGS)

    return ", ".join(parts)


def build_negative_prompt(extras: Optional[List[str]] = None) -> str:
    """Build a negative prompt, optionally appending extra tags."""
    if extras:
        return DEFAULT_NEGATIVE + ", " + ", ".join(extras)
    return DEFAULT_NEGATIVE


def build_random_prompt(
    character: str,
    lora_name: Optional[str] = None,
    locations: Optional[List[str]] = None,
    activities: Optional[List[str]] = None,
) -> str:
    """
    Build a randomized prompt for batch diversity.

    Picks random location, activity, camera, and lighting from presets
    or from provided lists.
    """
    location = random.choice(locations) if locations else ""
    activity = random.choice(activities) if activities else ""

    return build_prompt(
        character=character,
        lora_name=lora_name,
        location=location,
        activity=activity,
        camera_style=None,  # random
        lighting=None,       # random
    )
