"""
Face Discovery Engine — Generate diverse face images for identity selection

Generates a grid of face images with systematic variations across:
- Camera angles (front, 3/4 left, 3/4 right, profile)
- Lighting (studio, natural, golden hour, dramatic, rim light)
- Expressions (neutral, smile, serious, laughing, thoughtful)
- Hairstyles (default, pulled back, windswept)
- Focal lengths (50mm portrait, 85mm, 35mm)

The user reviews the generated grid and selects the best identity.
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from itertools import product
from urllib.parse import quote

from backend.services.comfyui_client import ComfyUIClient
from backend.utils.file_manager import PROJECT_ROOT
from backend.services.history_service import log_generation


# ── Prompt Variation Templates ──────────────────────────────────

ANGLES = {
    "front": "looking straight at camera, front view",
    "three_quarter_left": "3/4 view turned slightly left",
    "three_quarter_right": "3/4 view turned slightly right",
    "profile_left": "side profile view, facing left",
    "profile_right": "side profile view, facing right",
}

LIGHTING = {
    "studio": "professional studio lighting, even illumination",
    "natural": "soft natural daylight, outdoor",
    "golden_hour": "warm golden hour sunlight, sunset glow",
    "dramatic": "dramatic chiaroscuro lighting, high contrast",
    "rim_light": "rim lighting from behind, glowing edge light",
}

EXPRESSIONS = {
    "neutral": "neutral calm expression",
    "smile": "natural warm smile",
    "serious": "serious thoughtful expression",
    "laugh": "laughing joyfully, genuine happiness",
    "pensive": "contemplative pensive look",
}

HAIRSTYLES = {
    "default": "",  # No override — uses base description
    "pulled_back": "hair pulled back neatly",
    "windswept": "slightly windswept hair, natural movement",
}

FOCAL_LENGTHS = {
    "50mm": "shot with 50mm lens, classic portrait perspective",
    "85mm": "shot with 85mm lens, beautiful bokeh, shallow depth of field",
    "35mm": "shot with 35mm lens, slightly wider angle",
}

DEFAULT_NEGATIVE = (
    "(multiple people:1.8), (two people:1.7), (crowd:1.6), (group:1.6), "
    "(2girls:1.7), (2boys:1.7), (couple:1.6), (duplicated face:1.5), "
    "(split image:1.5), (collage:1.5), (side by side:1.5), "
    "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
    "bad hands, missing fingers, extra fingers, crossed eyes, "
    "watermark, text, logo, nsfw"
)


def get_face_variations() -> dict:
    """Return all available variation categories and options."""
    return {
        "angles": list(ANGLES.keys()),
        "lighting": list(LIGHTING.keys()),
        "expressions": list(EXPRESSIONS.keys()),
        "hairstyles": list(HAIRSTYLES.keys()),
        "focal_lengths": list(FOCAL_LENGTHS.keys()),
    }


def build_face_prompts(
    base_description: str = "a person",
    angles: Optional[List[str]] = None,
    lighting_styles: Optional[List[str]] = None,
    expressions: Optional[List[str]] = None,
    hairstyles: Optional[List[str]] = None,
    focal_lengths: Optional[List[str]] = None,
    lora_trigger: str = "",
) -> List[dict]:
    """
    Build a list of prompt variations for face discovery.

    Args:
        base_description: Character description (e.g. "a young man with brown hair")
        angles:           Which angles to use (None = defaults: front, 3/4 left/right)
        lighting_styles:  Which lighting (None = defaults: studio, natural, golden_hour)
        expressions:      Which expressions (None = defaults: neutral, smile, serious)
        hairstyles:       Which hairstyles (None = default only)
        focal_lengths:    Which focal lengths (None = default 85mm only)
        lora_trigger:     LoRA trigger word to prepend (e.g. "ohm_person")

    Returns:
        List of dicts with 'prompt', 'negative_prompt', 'tags', 'label'
    """
    # Defaults — balanced selection for fast discovery
    use_angles = angles or ["front", "three_quarter_left", "three_quarter_right"]
    use_lighting = lighting_styles or ["studio", "natural", "golden_hour"]
    use_expressions = expressions or ["neutral", "smile", "serious"]
    use_hairstyles = hairstyles or ["default"]
    use_focal = focal_lengths or ["85mm"]

    prompts = []
    for angle, light, expr, hair, focal in product(
        use_angles, use_lighting, use_expressions, use_hairstyles, use_focal
    ):
        parts = []

        # Single-person reinforcement with ComfyUI weight syntax
        if lora_trigger:
            parts.append(lora_trigger)
        parts.append("(solo:1.5)")
        parts.append("(1person:1.3)")

        # Base description — headshot framing reduces multi-face
        parts.append(f"(close-up headshot portrait of {base_description}:1.2)")
        parts.append("looking at viewer")

        # Angle
        parts.append(ANGLES[angle])

        # Expression
        parts.append(EXPRESSIONS[expr])

        # Hairstyle (if not default)
        if HAIRSTYLES.get(hair):
            parts.append(HAIRSTYLES[hair])

        # Lighting
        parts.append(LIGHTING[light])

        # Focal length
        parts.append(FOCAL_LENGTHS[focal])

        # Quality boosters
        parts.append("masterpiece, best quality, photorealistic, 8k, detailed skin texture")

        prompt_text = ", ".join(parts)
        label = f"{angle}_{light}_{expr}"

        prompts.append({
            "prompt": prompt_text,
            "negative_prompt": DEFAULT_NEGATIVE,
            "tags": {
                "angle": angle,
                "lighting": light,
                "expression": expr,
                "hairstyle": hair,
                "focal_length": focal,
            },
            "label": label,
            "prefix": f"face_{label}",
        })

    return prompts


def generate_face_discovery(
    character_name: str,
    base_description: str = "a person",
    checkpoint: str = "",
    lora_trigger: str = "",
    lora_name: str = "",
    lora_strength: float = 0.8,
    angles: Optional[List[str]] = None,
    lighting_styles: Optional[List[str]] = None,
    expressions: Optional[List[str]] = None,
    width: int = 512,
    height: int = 512,
    steps: int = 25,
    cfg_scale: float = 7.5,
    comfyui_host: str = "127.0.0.1",
    comfyui_port: int = 8188,
    limit: int = 40,
) -> dict:
    """
    Generate a full set of face discovery images.

    Creates multiple face images with varied angles, lighting, and expressions,
    saves them to outputs/discovery/{character_name}/faces/, and returns a
    manifest for the UI to display.
    """
    client = ComfyUIClient(host=comfyui_host, port=comfyui_port)

    # Check connection
    conn = client.check_connection()
    if not conn["connected"]:
        return {
            "success": False,
            "error": f"ComfyUI not connected at {client.base_url}",
        }

    # Build prompts
    prompts = build_face_prompts(
        base_description=base_description,
        angles=angles,
        lighting_styles=lighting_styles,
        expressions=expressions,
        lora_trigger=lora_trigger,
    )

    # Apply safety limit
    total = len(prompts)
    if total > limit:
        # Simple truncation (could be random sampling in future)
        prompts = prompts[:limit]
        print(f"⚠️ Limit reached: Truncating {total} prompts to {limit}")

    # Output directory
    output_dir = PROJECT_ROOT / "outputs" / "discovery" / character_name / "faces"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate each prompt
    results = []
    total = len(prompts)

    for i, p in enumerate(prompts):
        result = client.generate(
            prompt=p["prompt"],
            negative_prompt=p["negative_prompt"],
            checkpoint=checkpoint,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            lora_name=lora_name,
            lora_strength=lora_strength,
            output_dir=str(output_dir),
            prefix=p["prefix"],
        )

        results.append({
            "index": i,
            "label": p["label"],
            "tags": p["tags"],
            "prompt": p["prompt"],
            "success": result.get("success", False),
            "images": result.get("images", []),
            "error": result.get("error", ""),
        })

        # DB Logging
        if result.get("success", False):
            for img_path in result.get("images", []):
                log_generation(
                    image_path=img_path,
                    character_name=character_name,
                    prompt=p["prompt"],
                    negative_prompt=p["negative_prompt"],
                    settings={
                        "steps": steps,
                        "cfg_scale": cfg_scale,
                        "width": width,
                        "height": height,
                        "seed": result.get("seed", -1), # Client returns seed
                        "model": checkpoint,
                        "lora": lora_name,
                        "lora_strength": lora_strength
                    },
                    category="face_discovery"
                )

    # Save manifest
    manifest = {
        "character_name": character_name,
        "base_description": base_description,
        "generated_at": datetime.now().isoformat(),
        "total_prompts": total,
        "successful": sum(1 for r in results if r["success"]),
        "output_dir": str(output_dir),
        "results": results,
    }

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "success": True,
        "total": total,
        "generated": manifest["successful"],
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "results": results,
    }


def get_discovery_results(character_name: str) -> dict:
    """Load and return the face discovery manifest for a character."""
    manifest_path = (
        PROJECT_ROOT / "outputs" / "discovery" / character_name / "faces" / "manifest.json"
    )
    if not manifest_path.exists():
        return {"found": False, "error": "No face discovery results found"}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Add image URLs for frontend
    for result in manifest.get("results", []):
        if result.get("images"):
            result["image_urls"] = [
                f"/api/discovery/image?path={quote(p)}" for p in result["images"]
            ]

    return {"found": True, "manifest": manifest}


def select_identity(
    character_name: str,
    selected_indices: List[int],
) -> dict:
    """
    Mark selected face images as the chosen identity.

    Copies selected images to the character's dataset folder
    for use in LoRA training.
    """
    manifest_path = (
        PROJECT_ROOT / "outputs" / "discovery" / character_name / "faces" / "manifest.json"
    )
    if not manifest_path.exists():
        return {"success": False, "error": "No face discovery results found"}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Copy selected images to dataset
    dataset_dir = PROJECT_ROOT / "datasets" / character_name
    dataset_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    for idx in selected_indices:
        if idx < len(manifest["results"]):
            result = manifest["results"][idx]
            for img_path in result.get("images", []):
                src = Path(img_path)
                if src.exists():
                    dest = dataset_dir / src.name
                    shutil.copy2(src, dest)
                    copied.append(str(dest))

    # Update manifest with selections
    manifest["selected_indices"] = selected_indices
    manifest["selected_at"] = datetime.now().isoformat()
    manifest["copied_to_dataset"] = copied

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "success": True,
        "selected_count": len(selected_indices),
        "copied_files": len(copied),
        "dataset_dir": str(dataset_dir),
    }
