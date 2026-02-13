"""
Batch Content Generation Script — Automation Stub

Phase 5 will turn this into a full weekly content automation pipeline:
- Read scene list from YAML
- Generate 50–100 images per batch
- Generate video clips from best images
- Queue content for export

Usage (future):
    python -m automation.batch_generate --scenes scenes.yaml --count 50
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.utils.prompt_builder import build_random_prompt
from backend.services.image_service import ImageService, ImageRequest


# ── Example Scene Configurations ──────────────────────────────────

EXAMPLE_SCENES = {
    "character": "beautiful woman, 25 years old, brown hair, green eyes",
    "locations": [
        "in a modern cafe, warm interior",
        "walking on a city street, sunset",
        "sitting in a park, cherry blossoms",
        "at the beach, golden hour",
        "in a luxury office, modern decor",
        "on a rooftop, city skyline background",
        "in a cozy library, bookshelves",
        "at a street market, vibrant colors",
    ],
    "activities": [
        "smiling at camera",
        "reading a book",
        "holding a coffee cup",
        "looking at sunset",
        "walking confidently",
        "sitting elegantly",
        "laughing naturally",
        "posing for photo",
    ],
}


async def run_batch(count: int = 10):
    """
    Generate a batch of images with randomized prompts.

    TODO (Phase 5):
    - Load scene config from YAML file
    - Connect to running FastAPI server or ComfyUI directly
    - Save outputs with metadata
    - Generate video clips from top-rated images
    """
    print(f"{'='*60}")
    print(f"  AI Character Batch Generator")
    print(f"  Generating {count} randomized prompts...")
    print(f"{'='*60}\n")

    for i in range(count):
        prompt = build_random_prompt(
            character=EXAMPLE_SCENES["character"],
            lora_name="character_ai",
            locations=EXAMPLE_SCENES["locations"],
            activities=EXAMPLE_SCENES["activities"],
        )
        print(f"[{i+1:03d}/{count:03d}] {prompt[:100]}...")

    print(f"\n{'='*60}")
    print(f"  Batch complete! (stub — no actual generation yet)")
    print(f"  In Phase 5, this will call ComfyUI + save outputs")
    print(f"{'='*60}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    asyncio.run(run_batch(count))
