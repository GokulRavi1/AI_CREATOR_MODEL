"""
Dataset Preparation Tools — Resize, Caption, Validate & Analyze

Tools for preparing user-provided images into a LoRA training-ready dataset.
Users supply their own photos; these tools organize, resize, caption, and validate them.
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict

from PIL import Image

from backend.utils.file_manager import PROJECT_ROOT


# ── Dataset Guidelines ──────────────────────────────────────────

RECOMMENDED_COUNTS = {
    "face_closeup": {"min": 10, "max": 15, "description": "Face close-ups (head and shoulders)"},
    "mid_body": {"min": 10, "max": 15, "description": "Mid-body shots (waist up)"},
    "full_body": {"min": 10, "max": 20, "description": "Full-body images (head to toe)"},
}

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SUPPORTED_RESOLUTIONS = [512, 768, 1024]


@dataclass
class ImageInfo:
    filename: str
    path: str
    width: int
    height: int
    size_kb: float
    format: str
    category: str = "uncategorized"  # face_closeup, mid_body, full_body


@dataclass
class DatasetStats:
    total_images: int = 0
    face_closeups: int = 0
    mid_body: int = 0
    full_body: int = 0
    uncategorized: int = 0
    avg_width: float = 0
    avg_height: float = 0
    total_size_mb: float = 0
    resolutions: dict = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    ready: bool = False


@dataclass
class ValidationResult:
    valid: bool
    total_images: int
    issues: List[str]
    warnings: List[str]
    suggestions: List[str]
    stats: DatasetStats


# ── Core Functions ──────────────────────────────────────────────

def scan_images(input_dir: str) -> List[ImageInfo]:
    """Scan a directory and return info about all valid images."""
    input_path = Path(input_dir)
    if not input_path.exists():
        return []

    images = []
    for f in sorted(input_path.iterdir()):
        if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS:
            try:
                with Image.open(f) as img:
                    w, h = img.size
                    images.append(ImageInfo(
                        filename=f.name,
                        path=str(f),
                        width=w,
                        height=h,
                        size_kb=f.stat().st_size / 1024,
                        format=img.format or f.suffix.upper().strip('.'),
                    ))
            except Exception:
                continue

    return images


def resize_images(
    input_dir: str,
    output_dir: str,
    size: int = 512,
    maintain_aspect: bool = False,
) -> dict:
    """
    Batch resize images for LoRA training.

    Args:
        input_dir:       Source directory with original images
        output_dir:      Destination for resized images
        size:            Target resolution (512, 768, or 1024)
        maintain_aspect: If True, resize shortest side to `size` and center-crop

    Returns:
        Summary dict with counts and any errors.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {"processed": 0, "skipped": 0, "errors": [], "output_dir": str(output_path)}

    for f in sorted(input_path.iterdir()):
        if f.suffix.lower() not in VALID_EXTENSIONS:
            continue

        try:
            with Image.open(f) as img:
                img = img.convert("RGB")

                if maintain_aspect:
                    # Resize shortest side, then center crop
                    w, h = img.size
                    scale = size / min(w, h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    img = img.resize((new_w, new_h), Image.LANCZOS)

                    # Center crop to exact size
                    left = (new_w - size) // 2
                    top = (new_h - size) // 2
                    img = img.crop((left, top, left + size, top + size))
                else:
                    img = img.resize((size, size), Image.LANCZOS)

                # Save as PNG for best quality
                out_name = f.stem + ".png"
                img.save(output_path / out_name, "PNG", quality=95)
                results["processed"] += 1

        except Exception as e:
            results["errors"].append({"file": f.name, "error": str(e)})

    return results


def auto_caption(
    image_dir: str,
    trigger_word: str,
    default_description: str = "a photo of",
    overwrite: bool = False,
) -> dict:
    """
    Generate caption .txt files alongside each image for LoRA training.

    Each image gets a corresponding .txt file with format:
        {trigger_word}, {default_description} {trigger_word}

    Args:
        image_dir:           Directory containing training images
        trigger_word:        Character trigger word (e.g., "ohm_person")
        default_description: Base description prefix
        overwrite:           Whether to overwrite existing caption files

    Returns:
        Summary with created/skipped counts.
    """
    dir_path = Path(image_dir)
    results = {"created": 0, "skipped": 0, "files": []}

    for f in sorted(dir_path.iterdir()):
        if f.suffix.lower() not in VALID_EXTENSIONS:
            continue

        caption_file = f.with_suffix(".txt")

        if caption_file.exists() and not overwrite:
            results["skipped"] += 1
            continue

        # Build caption
        caption = f"{trigger_word}, {default_description} {trigger_word}"
        caption_file.write_text(caption, encoding="utf-8")

        results["created"] += 1
        results["files"].append({
            "image": f.name,
            "caption_file": caption_file.name,
            "caption": caption,
        })

    return results


def categorize_images(image_dir: str, categories: dict) -> dict:
    """
    Organize images into category subdirectories.

    Args:
        image_dir:  Directory containing all images
        categories: Dict mapping filename patterns/indices to categories
                    e.g. {"face_closeup": [0,1,2], "mid_body": [3,4,5], "full_body": [6,7,8]}
                    or   {"face_closeup": ["img001.jpg", "img002.jpg"], ...}

    Returns:
        Summary of categorization.
    """
    dir_path = Path(image_dir)
    images = sorted([
        f for f in dir_path.iterdir()
        if f.is_file() and f.suffix.lower() in VALID_EXTENSIONS
    ])

    results = {"moved": 0, "categories": {}}

    for category_name, items in categories.items():
        cat_dir = dir_path / category_name
        cat_dir.mkdir(exist_ok=True)
        count = 0

        for item in items:
            if isinstance(item, int) and 0 <= item < len(images):
                src = images[item]
            elif isinstance(item, str):
                src = dir_path / item
            else:
                continue

            if src.exists():
                dest = cat_dir / src.name
                src.rename(dest)
                count += 1

        results["categories"][category_name] = count
        results["moved"] += count

    return results


def validate_dataset(image_dir: str) -> ValidationResult:
    """
    Validate a dataset directory for LoRA training readiness.

    Checks:
    - Image count (recommended 30–50)
    - Resolution consistency
    - File format validity
    - Caption file presence
    - Image quality indicators
    """
    dir_path = Path(image_dir)
    issues = []
    warnings = []
    suggestions = []

    if not dir_path.exists():
        return ValidationResult(
            valid=False,
            total_images=0,
            issues=["Directory does not exist"],
            warnings=[],
            suggestions=["Create the dataset directory and add images"],
            stats=DatasetStats(),
        )

    images = scan_images(image_dir)
    total = len(images)

    if total == 0:
        return ValidationResult(
            valid=False,
            total_images=0,
            issues=["No valid images found"],
            warnings=[],
            suggestions=[
                "Add 30–50 images of your character",
                "Supported formats: JPG, PNG, WebP, BMP",
                f"Recommended: {RECOMMENDED_COUNTS['face_closeup']['min']}–{RECOMMENDED_COUNTS['face_closeup']['max']} face close-ups, "
                f"{RECOMMENDED_COUNTS['mid_body']['min']}–{RECOMMENDED_COUNTS['mid_body']['max']} mid-body, "
                f"{RECOMMENDED_COUNTS['full_body']['min']}–{RECOMMENDED_COUNTS['full_body']['max']} full-body",
            ],
            stats=DatasetStats(),
        )

    # Resolution check
    widths = [img.width for img in images]
    heights = [img.height for img in images]
    resolutions = {}
    for img in images:
        res_key = f"{img.width}x{img.height}"
        resolutions[res_key] = resolutions.get(res_key, 0) + 1

    if len(resolutions) > 1:
        warnings.append(
            f"Mixed resolutions found ({len(resolutions)} different). "
            "Consider resizing all images to a consistent resolution."
        )

    # Check for very small images
    small_images = [img for img in images if img.width < 512 or img.height < 512]
    if small_images:
        issues.append(
            f"{len(small_images)} images are smaller than 512×512. "
            "Use the resize tool to upscale them."
        )

    # Count check
    if total < 20:
        warnings.append(f"Only {total} images. Recommended: 30–50 for best results.")
    elif total > 80:
        warnings.append(f"{total} images is quite a lot. 30–50 is usually optimal.")

    # Caption check
    caption_count = sum(
        1 for img in images
        if Path(img.path).with_suffix(".txt").exists()
    )
    if caption_count == 0:
        suggestions.append(
            "No caption files found. Run auto_caption() to generate them."
        )
    elif caption_count < total:
        warnings.append(
            f"Only {caption_count}/{total} images have captions. "
            "Run auto_caption() to generate missing ones."
        )

    # Build stats
    total_size = sum(img.size_kb for img in images)
    stats = DatasetStats(
        total_images=total,
        avg_width=sum(widths) / total if total else 0,
        avg_height=sum(heights) / total if total else 0,
        total_size_mb=total_size / 1024,
        resolutions=resolutions,
        issues=issues,
        ready=len(issues) == 0,
    )

    valid = len(issues) == 0
    if not suggestions and valid:
        suggestions.append("Dataset looks good! Ready for LoRA training.")

    return ValidationResult(
        valid=valid,
        total_images=total,
        issues=issues,
        warnings=warnings,
        suggestions=suggestions,
        stats=stats,
    )


def analyze_dataset(image_dir: str) -> dict:
    """
    Return comprehensive analysis of a dataset directory.

    Returns dict with image list, stats, category breakdown,
    and readiness assessment.
    """
    images = scan_images(image_dir)
    validation = validate_dataset(image_dir)

    return {
        "directory": image_dir,
        "images": [
            {
                "filename": img.filename,
                "width": img.width,
                "height": img.height,
                "size_kb": round(img.size_kb, 1),
                "format": img.format,
            }
            for img in images
        ],
        "stats": asdict(validation.stats),
        "validation": {
            "valid": validation.valid,
            "issues": validation.issues,
            "warnings": validation.warnings,
            "suggestions": validation.suggestions,
        },
        "guidelines": RECOMMENDED_COUNTS,
    }


def get_dataset_guide() -> dict:
    """
    Return a guide for the user on what images to provide.

    Since the user provides their own images, this gives them
    clear instructions on what's needed for optimal LoRA training.
    """
    return {
        "overview": (
            "Provide 30–50 images of your character for LoRA training. "
            "The more diverse and high-quality the images, the better the model."
        ),
        "categories": {
            "face_closeup": {
                "count": "10–15 images",
                "description": "Head and shoulders, clear face visible",
                "tips": [
                    "Multiple angles: front, 3/4 view, profile",
                    "Different expressions: neutral, smiling, serious",
                    "Various lighting: natural, indoor, outdoor",
                    "Hair clearly visible",
                ],
            },
            "mid_body": {
                "count": "10–15 images",
                "description": "Waist-up framing",
                "tips": [
                    "Show upper body proportions",
                    "Different outfits if possible",
                    "Arms visible in natural positions",
                    "Both indoor and outdoor settings",
                ],
            },
            "full_body": {
                "count": "10–20 images",
                "description": "Head to toe, full figure visible",
                "tips": [
                    "Standing, sitting, walking poses",
                    "Show full proportions and height",
                    "Different angles and distances",
                    "Clean backgrounds preferred",
                ],
            },
        },
        "general_tips": [
            "Use high-resolution images (at least 512×512)",
            "Clean, uncluttered backgrounds work best",
            "Good, even lighting — avoid heavy shadows",
            "Only one person in each image (the character)",
            "No heavy filters or extreme editing",
            "Variety in poses and angles improves the model",
            "Consistent identity across all images",
        ],
        "preparation_steps": [
            "1. Collect your images into the datasets/ directory",
            "2. Run validate to check image quality",
            "3. Run resize to standardize resolution (512×512 or 768×768)",
            "4. Run auto_caption to generate training captions",
            "5. Review captions and adjust if needed",
            "6. Ready for LoRA training!",
        ],
    }
