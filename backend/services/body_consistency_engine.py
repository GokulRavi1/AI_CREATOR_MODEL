"""
Body Consistency Engine — Generate body-consistent images

After face identity selection, generates body images with:
- Standing poses (front, 3/4, relaxed, arms crossed)
- Sitting poses (chair, casual, cross-legged)
- Action poses (walking, leaning, gesturing)
- Full-body framing (head-to-toe, waist-up, mid-body)
- Outfit variations (casual, formal, athletic)

Maintains consistent body shape, proportions, and identity using the same
seed ranges and LoRA identity lock.
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from itertools import product
from urllib.parse import quote

from backend.services.comfyui_client import ComfyUIClient
from backend.utils.file_manager import PROJECT_ROOT
from backend.services.history_service import log_generation


# ── Pose Templates ──────────────────────────────────────────────

POSES = {
    "standing_front": "standing straight, facing camera, front view, full body",
    "standing_3q": "standing casually, 3/4 angle, relaxed posture, full body",
    "standing_relaxed": "standing relaxed, weight on one leg, natural pose, full body",
    "arms_crossed": "standing with arms crossed, confident pose, full body",
    "sitting_chair": "sitting on a chair, relaxed, mid-body view",
    "sitting_casual": "sitting casually, legs crossed, natural pose, mid-body",
    "walking": "walking naturally, mid-stride, slight motion blur, full body",
    "leaning": "leaning against a wall, relaxed, casual pose, full body",
}

FRAMINGS = {
    "full_body": "full body shot, head to toe visible",
    "mid_body": "mid-body shot, waist up, upper body focus",
    "three_quarter": "three-quarter body shot, knees up",
}

OUTFITS = {
    "default": "",  # Uses base description
    "casual": "wearing casual clothes, t-shirt and jeans",
    "formal": "wearing formal attire, button-down shirt, smart look",
    "athletic": "wearing athletic sportswear, active look",
    "nude": "nude, naked, completely naked, full body nude, highly detailed skin texture, explicit",
}

BODY_LIGHTING = {
    "studio": "professional studio lighting, clean white background",
    "outdoor": "soft natural outdoor lighting, park setting",
    "indoor": "warm indoor ambient lighting, home setting",
}

DEFAULT_BODY_NEGATIVE = (
    "(multiple people:1.8), (two people:1.7), (crowd:1.6), (group:1.6), "
    "(2girls:1.7), (2boys:1.7), (couple:1.6), (duplicated face:1.5), "
    "(split image:1.5), (collage:1.5), (side by side:1.5), "
    "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
    "bad hands, missing fingers, extra fingers, bad proportions, "
    "watermark, text, logo, cropped head"
)


def get_body_variations() -> dict:
    """Return all available body variation categories."""
    return {
        "poses": list(POSES.keys()),
        "framings": list(FRAMINGS.keys()),
        "outfits": list(OUTFITS.keys()),
        "lighting": list(BODY_LIGHTING.keys()),
    }


def build_body_prompts(
    base_description: str = "a person",
    poses: Optional[List[str]] = None,
    framings: Optional[List[str]] = None,
    outfits: Optional[List[str]] = None,
    lighting_styles: Optional[List[str]] = None,
    lora_trigger: str = "",
) -> List[dict]:
    """
    Build body consistency prompt variations.

    Args:
        base_description: Character description
        poses:            Which poses (None = defaults)
        framings:         Which framings (None = defaults)
        outfits:          Which outfits (None = defaults)
        lighting_styles:  Which lighting (None = defaults)
        lora_trigger:     LoRA trigger word

    Returns:
        List of prompt dicts with prompt, negative, tags, label
    """
    use_poses = poses or [
        "standing_front", "standing_3q", "standing_relaxed",
        "sitting_chair", "walking",
    ]
    use_framings = framings or ["full_body", "mid_body"]
    use_outfits = outfits or ["casual"]
    use_lighting = lighting_styles or ["studio", "outdoor"]

    prompts = []
    for pose, framing, outfit, light in product(
        use_poses, use_framings, use_outfits, use_lighting
    ):
        parts = []

        if lora_trigger:
            parts.append(lora_trigger)

        # Single-person reinforcement with weighting
        parts.append("(solo:1.5)")
        parts.append("(1person:1.3)")
        parts.append("looking at viewer")

        # Base description with framing emphasis
        parts.append(f"(full body shot of 1 {base_description}:1.2)")

        parts.append(POSES[pose])
        parts.append(FRAMINGS[framing])
        parts.append(OUTFITS[outfit])
        parts.append(BODY_LIGHTING[light])
        parts.append("masterpiece, best quality, photorealistic, consistent proportions")

        prompt_text = ", ".join(parts)
        label = f"{pose}_{framing}_{outfit}_{light}"

        prompts.append({
            "prompt": prompt_text,
            "negative_prompt": DEFAULT_BODY_NEGATIVE,
            "tags": {
                "pose": pose,
                "framing": framing,
                "outfit": outfit,
                "lighting": light,
            },
            "label": label,
            "prefix": f"body_{pose}_{framing}",
        })

    return prompts


def generate_body_set(
    character_name: str,
    base_description: str = "a person",
    checkpoint: str = "",
    lora_trigger: str = "",
    lora_name: str = "",
    lora_strength: float = 0.8,
    poses: Optional[List[str]] = None,
    framings: Optional[List[str]] = None,
    outfits: Optional[List[str]] = None,
    width: int = 512,
    height: int = 768,
    steps: int = 25,
    cfg_scale: float = 7.5,
    comfyui_host: str = "127.0.0.1",
    comfyui_port: int = 8188,
    limit: int = 40,
    control_image_name: Optional[str] = None,
) -> dict:
    """
    Generate a full set of body consistency images.

    Creates body images with varied poses, framings, outfits, and lighting,
    saves them to outputs/discovery/{character_name}/bodies/.
    """
    client = ComfyUIClient(host=comfyui_host, port=comfyui_port)

    conn = client.check_connection()
    if not conn["connected"]:
        return {
            "success": False,
            "error": f"ComfyUI not connected at {client.base_url}",
        }

    prompts = build_body_prompts(
        base_description=base_description,
        poses=poses,
        framings=framings,
        outfits=outfits,
        lora_trigger=lora_trigger,
    )

    # Apply safety limit
    if len(prompts) > limit:
        prompts = prompts[:limit]
        print(f"⚠️ Limit reached: Truncating to {limit} prompts")

    output_dir = PROJECT_ROOT / "outputs" / "discovery" / character_name / "bodies"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(prompts)

    for i, p in enumerate(prompts):
        # Check if ControlNet model is available
        controlnet_model = "control_v11p_sd15_openpose.pth"
        controlnet_dir = Path(f"c:/workspace/OFM CODE/comfyui/models/controlnet")
        use_controlnet = (
            control_image_name
            and controlnet_dir.exists()
            and (controlnet_dir / controlnet_model).exists()
        )

        if control_image_name and not use_controlnet:
            print(f"⚠️ ControlNet model '{controlnet_model}' not found, falling back to standard generation")

        if use_controlnet:
            # use ControlNet
            workflow = client.build_controlnet_workflow(
                prompt=p["prompt"],
                control_image_name=control_image_name,
                controlnet_name=controlnet_model,
                negative_prompt=p["negative_prompt"],
                checkpoint=checkpoint,
                width=width,
                height=height,
                steps=steps,
                cfg_scale=cfg_scale,
                lora_name=lora_name,
                lora_strength=lora_strength,
            )
            result = client.execute_workflow(
                workflow=workflow,
                output_dir=str(output_dir),
                prefix=p["prefix"],
            )
        else:
            # use standard generation
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
                        "seed": result.get("seed", -1),
                        "model": checkpoint,
                        "lora_name": lora_name,
                        "lora_strength": lora_strength,
                        "pose": p["tags"]["pose"],
                        "framing": p["tags"]["framing"],
                        "outfit": p["tags"]["outfit"]
                    },
                    category="body_consistency"
                )

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


def get_body_results(character_name: str) -> dict:
    """Load and return the body consistency manifest."""
    manifest_path = (
        PROJECT_ROOT / "outputs" / "discovery" / character_name / "bodies" / "manifest.json"
    )
    if not manifest_path.exists():
        return {"found": False, "error": "No body consistency results found"}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for result in manifest.get("results", []):
        if result.get("images"):
            result["image_urls"] = [
                f"/api/discovery/image?path={quote(p)}" for p in result["images"]
            ]

    return {"found": True, "manifest": manifest}


def copy_body_to_dataset(
    character_name: str,
    selected_indices: Optional[List[int]] = None,
) -> dict:
    """
    Copy body images to the character dataset folder.

    If selected_indices is None, copies ALL body images.
    """
    manifest_path = (
        PROJECT_ROOT / "outputs" / "discovery" / character_name / "bodies" / "manifest.json"
    )
    if not manifest_path.exists():
        return {"success": False, "error": "No body results found"}

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    dataset_dir = PROJECT_ROOT / "datasets" / character_name
    dataset_dir.mkdir(parents=True, exist_ok=True)

    copied = []
    results = manifest.get("results", [])

    indices = selected_indices if selected_indices is not None else range(len(results))

    for idx in indices:
        if idx < len(results):
            result = results[idx]
            for img_path in result.get("images", []):
                src = Path(img_path)
                if src.exists():
                    dest = dataset_dir / src.name
                    shutil.copy2(src, dest)
                    copied.append(str(dest))

    return {
        "success": True,
        "copied_files": len(copied),
        "dataset_dir": str(dataset_dir),
    }
