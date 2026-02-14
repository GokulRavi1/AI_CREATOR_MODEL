"""
AI Fixed Character Generation System — FastAPI Server

Main application entry point with all API endpoints.
Serves both the REST API and the frontend dashboard.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
from datetime import datetime

import shutil
from backend.config import config
from backend.services.image_service import ImageService, ImageRequest
from backend.services.video_service import VideoService, VideoRequest
from backend.services.voice_service import VoiceService, VoiceRequest
from backend.services.avatar_service import AvatarService, AvatarRequest
from backend.services.character_manager import (
    create_character, load_character, list_characters, delete_character,
    set_active_character, get_active_character, update_character,
    register_trained_lora,
)
from backend.services.training_service import (
    TrainingConfig, generate_kohya_config, save_training_config,
    start_training, get_training_status, stop_training,
    get_recommended_config,
)
from backend.utils.prompt_builder import (
    build_prompt, build_negative_prompt, build_random_prompt,
    CAMERA_STYLES, LIGHTING_STYLES,
)
from backend.utils.file_manager import (
    ensure_dirs, list_models, list_outputs, cleanup_old_outputs, PROJECT_ROOT,
)
from backend.utils.dataset_tools import (
    resize_images, auto_caption, validate_dataset, analyze_dataset,
    get_dataset_guide,
)
from automation.face_discovery import get_full_shooting_guide, save_guide_json
from backend.services.comfyui_client import ComfyUIClient
from backend.services.face_discovery_engine import (
    generate_face_discovery, get_discovery_results, select_identity,
    get_face_variations,
)
from backend.services.body_consistency_engine import (
    generate_body_set, get_body_results, copy_body_to_dataset,
    get_body_variations,
)
from dataclasses import asdict
from backend.services.content_engine import ContentEngine
from fastapi import UploadFile, File

# ── Initialize ────────────────────────────────────────────────────

from backend.routers import history

app = FastAPI(
    title="AI Character Generation System",
    description="Fixed AI character image, video, and talking avatar pipeline",
    version="0.1.0",
)

app.include_router(history.router)

# CORS — allow local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure output directories exist on startup
ensure_dirs()

# Service instances
image_service = ImageService(
    comfyui_host=config.comfyui.host,
    comfyui_port=config.comfyui.port,
)
video_service = VideoService()
voice_service = VoiceService(engine=config.voice.engine, model=config.voice.model)
video_service = VideoService()
voice_service = VoiceService(engine=config.voice.engine, model=config.voice.model)
avatar_service = AvatarService(engine=config.avatar.engine)
content_engine = ContentEngine(host=config.comfyui.host, port=config.comfyui.port)

# ── Static Files (Frontend UI) ───────────────────────────────────

UI_DIR = Path(__file__).resolve().parent.parent / "ui"
app.mount("/static", StaticFiles(directory=str(UI_DIR)), name="static")


# ── Request/Response Models ───────────────────────────────────────

class GenerateImageBody(BaseModel):
    prompt: str = Field(..., description="Scene description prompt")
    character_lora: Optional[str] = Field(None, description="LoRA model name")
    lora_weight: float = Field(0.8, ge=0.0, le=1.5)
    width: int = Field(512, ge=256, le=1024)
    height: int = Field(512, ge=256, le=1024)
    steps: int = Field(25, ge=1, le=100)
    cfg_scale: float = Field(7.5, ge=1.0, le=20.0)
    seed: int = Field(-1)
    negative_prompt: Optional[str] = None
    camera_style: Optional[str] = None
    lighting: Optional[str] = None


class GenerateVideoBody(BaseModel):
    source_image: str = Field(..., description="Path to source image")
    prompt: str = Field("", description="Motion prompt")
    frames: int = Field(16, ge=4, le=64)
    fps: int = Field(8, ge=1, le=30)


class GenerateAvatarBody(BaseModel):
    face_image: str = Field(..., description="Path to face image")
    audio_path: str = Field(..., description="Path to audio file")
    engine: str = Field("sadtalker", description="'sadtalker' or 'wav2lip'")


class GenerateVoiceBody(BaseModel):
    text: str = Field(..., description="Text to convert to speech")
    voice_model: str = Field("en_US-lessac-medium")
    speed: float = Field(1.0, ge=0.5, le=2.0)


class CreateCharacterBody(BaseModel):
    name: str = Field(..., description="Character name (used as folder name)")
    trigger_word: str = Field(..., description="LoRA trigger word (e.g. 'ohm_person')")
    description: str = Field("", description="Character description")
    lora_weight: float = Field(0.8, ge=0.0, le=1.5)
    tags: Optional[List[str]] = None


class UpdateCharacterBody(BaseModel):
    trigger_word: Optional[str] = None
    description: Optional[str] = None
    lora_weight: Optional[float] = None
    tags: Optional[List[str]] = None


class TrainingConfigBody(BaseModel):
    character_name: str = Field(..., description="Name of the character to train")
    trigger_word: str = Field("ohm_person")
    pretrained_model: str = Field("runwayml/stable-diffusion-v1-5")
    network_rank: int = Field(32, ge=4, le=128)
    network_alpha: int = Field(32, ge=1, le=128)
    resolution: int = Field(512)
    batch_size: int = Field(1, ge=1, le=8)
    epochs: int = Field(12, ge=1, le=100)
    learning_rate: float = Field(1e-4)
    gpu_vram_gb: int = Field(8, ge=4, le=48)
    use_recommended: bool = Field(False, description="Auto-select settings based on GPU and dataset")


class DatasetPrepareBody(BaseModel):
    character_name: str = Field(..., description="Character name")
    resolution: int = Field(512)
    trigger_word: str = Field("ohm_person")
    maintain_aspect: bool = Field(False)


class FaceDiscoveryBody(BaseModel):
    character_name: str = Field(..., description="Character name")
    base_description: str = Field("a person", description="Physical description of the character")
    checkpoint: str = Field("", description="SD checkpoint name (leave empty for default)")
    lora_trigger: str = Field("", description="LoRA trigger word")
    lora_name: str = Field("", description="Existing LoRA file name")
    lora_strength: float = Field(0.8, ge=0.0, le=1.5)
    angles: Optional[List[str]] = Field(None, description="Angles to generate")
    lighting: Optional[List[str]] = Field(None, description="Lighting styles")
    expressions: Optional[List[str]] = Field(None, description="Expressions")
    width: int = Field(512, ge=256, le=1024)
    height: int = Field(512, ge=256, le=1024)
    steps: int = Field(25, ge=1, le=100)
    steps: int = Field(25, ge=1, le=100)
    cfg_scale: float = Field(7.5, ge=1.0, le=20.0)
    limit: int = Field(40, ge=1, le=100, description="Max images to generate (safety limit)")


class BodyConsistencyBody(BaseModel):
    character_name: str = Field(..., description="Character name")
    base_description: str = Field("a person", description="Physical description")
    checkpoint: str = Field("")
    lora_trigger: str = Field("")
    lora_name: str = Field("")
    lora_strength: float = Field(0.8, ge=0.0, le=1.5)
    poses: Optional[List[str]] = Field(None)
    framings: Optional[List[str]] = Field(None)
    outfits: Optional[List[str]] = Field(None)
    width: int = Field(512, ge=256, le=1024)
    height: int = Field(768, ge=256, le=1024)
    steps: int = Field(25, ge=1, le=100)
    steps: int = Field(25, ge=1, le=100)
    cfg_scale: float = Field(7.5, ge=1.0, le=20.0)
    limit: int = Field(40, ge=1, le=100, description="Max images to generate")
    control_image_name: Optional[str] = Field(None, description="Reference image for ControlNet")


class SelectIdentityBody(BaseModel):
    selected_indices: List[int] = Field(..., description="Indices of selected images")


class BuildPromptBody(BaseModel):
    character: Optional[str] = None
    lora_name: Optional[str] = None
    lora_weight: float = 0.8
    location: str = ""
    activity: str = ""
    camera_style: Optional[str] = None
    lighting: Optional[str] = None
    style_modifiers: Optional[List[str]] = None


class StudioGenerateBody(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 512
    height: int = 768
    steps: int = 25
    cfg_scale: float = 7.0
    seed: int = -1
    checkpoint: str = ""
    lora_name: str = ""
    lora_strength: float = 0.8
    use_hires_fix: bool = False
    controlnet_enabled: bool = False
    control_image_name: str = ""
    controlnet_name: str = "control_v11p_sd15_openpose.pth"


# ── API Endpoints ─────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    """Serve the main dashboard HTML."""
    return FileResponse(str(UI_DIR / "index.html"))


@app.get("/api/health")
async def health_check():
    """System health check."""
    comfyui_status = image_service.check_comfyui()
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "0.2.0",
        "services": {
            "image": "connected" if comfyui_status["connected"] else "disconnected",
            "video": "stub",
            "voice": "stub",
            "avatar": "stub",
        },
        "comfyui": comfyui_status,
        "config": {
            "comfyui": f"{config.comfyui.host}:{config.comfyui.port}",
            "voice_engine": config.voice.engine,
            "avatar_engine": config.avatar.engine,
        },
    }


@app.post("/api/generate/image")
async def generate_image(body: GenerateImageBody):
    """Generate an image using the character LoRA and scene prompt."""
    # Build full prompt using the prompt builder
    full_prompt = build_prompt(
        character=body.character_lora,
        lora_name=body.character_lora,
        lora_weight=body.lora_weight,
        location=body.prompt,
        camera_style=body.camera_style,
        lighting=body.lighting,
    )

    request = ImageRequest(
        prompt=full_prompt,
        character_lora=body.character_lora,
        lora_weight=body.lora_weight,
        width=body.width,
        height=body.height,
        steps=body.steps,
        cfg_scale=body.cfg_scale,
        seed=body.seed,
        negative_prompt=body.negative_prompt or build_negative_prompt(),
    )

    result = await image_service.generate(request)
    return {
        "success": True,
        "result": {
            "image_path": result.image_path,
            "prompt_used": result.prompt_used,
            "seed": result.seed,
            "timestamp": result.timestamp,
            "status": result.status,
        },
    }


@app.post("/api/generate/video")
async def generate_video(body: GenerateVideoBody):
    """Generate a short video/reel from a source image."""
    request = VideoRequest(
        source_image=body.source_image,
        prompt=body.prompt,
        frames=body.frames,
        fps=body.fps,
    )

    result = await video_service.generate(request)
    return {
        "success": True,
        "result": {
            "video_path": result.video_path,
            "frames_count": result.frames_count,
            "duration_seconds": result.duration_seconds,
            "timestamp": result.timestamp,
            "status": result.status,
        },
    }


@app.post("/api/generate/voice")
async def generate_voice(body: GenerateVoiceBody):
    """Generate speech audio from text."""
    request = VoiceRequest(
        text=body.text,
        voice_model=body.voice_model,
        speed=body.speed,
    )

    result = await voice_service.synthesize(request)
    return {
        "success": True,
        "result": {
            "audio_path": result.audio_path,
            "duration_seconds": result.duration_seconds,
            "text_length": result.text_length,
            "timestamp": result.timestamp,
            "status": result.status,
        },
    }


@app.post("/api/generate/avatar")
async def generate_avatar(body: GenerateAvatarBody):
    """Generate a talking avatar video."""
    request = AvatarRequest(
        face_image=body.face_image,
        audio_path=body.audio_path,
        engine=body.engine,
    )

    result = await avatar_service.generate(request)
    return {
        "success": True,
        "result": {
            "video_path": result.video_path,
            "duration_seconds": result.duration_seconds,
            "timestamp": result.timestamp,
            "status": result.status,
        },
    }


@app.post("/api/prompt/build")
async def build_prompt_endpoint(body: BuildPromptBody):
    """Build a formatted SD prompt from components."""
    prompt = build_prompt(
        character=body.character,
        lora_name=body.lora_name,
        lora_weight=body.lora_weight,
        location=body.location,
        activity=body.activity,
        camera_style=body.camera_style,
        lighting=body.lighting,
        style_modifiers=body.style_modifiers,
    )
    negative = build_negative_prompt()

    return {
        "prompt": prompt,
        "negative_prompt": negative,
    }


@app.get("/api/models")
async def get_models():
    """List all available models — queries ComfyUI with file-system fallback."""
    # Try ComfyUI API first (returns actual loaded models)
    comfy_checkpoints = image_service.client.get_available_checkpoints()
    comfy_loras = image_service.client.get_available_loras()

    # If ComfyUI returned results, use those (as string names)
    if comfy_checkpoints or comfy_loras:
        return {
            "loras": comfy_loras,
            "checkpoints": comfy_checkpoints,
        }

    # Fallback: scan local models directory (returns dicts → extract names)
    local_loras = list_models("loras")
    local_checkpoints = list_models("checkpoints")
    return {
        "loras": [m["name"] for m in local_loras],
        "checkpoints": [m["name"] for m in local_checkpoints],
    }


@app.get("/api/outputs/{category}")
async def get_outputs(category: str, limit: int = 20):
    """List recent outputs in a category."""
    if category not in ("images", "videos", "avatars", "audio"):
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    return {"outputs": list_outputs(category, limit)}


@app.get("/api/presets")
async def get_presets():
    """Get available preset options for the UI dropdowns."""
    return {
        "camera_styles": CAMERA_STYLES,
        "lighting_styles": LIGHTING_STYLES,
        "voice_models": voice_service.get_available_voices(),
        "avatar_engines": ["sadtalker", "wav2lip"],
    }


@app.post("/api/cleanup/{category}")
async def cleanup_outputs(category: str, keep_count: int = 100):
    """Clean up old outputs, keeping the most recent files."""
    if category not in ("images", "videos", "avatars", "audio"):
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    cleanup_old_outputs(category, keep_count)
    return {"message": f"Cleaned up {category}, kept latest {keep_count} files"}


# ── Phase 1: Character Management ─────────────────────────────────

@app.get("/api/characters")
async def api_list_characters():
    """List all saved characters."""
    chars = list_characters()
    active = get_active_character()
    return {
        "characters": chars,
        "active": active["name"] if active else None,
    }


@app.post("/api/characters")
async def api_create_character(body: CreateCharacterBody):
    """Create/register a new character."""
    result = create_character(
        name=body.name,
        trigger_word=body.trigger_word,
        description=body.description,
        lora_weight=body.lora_weight,
        tags=body.tags,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/characters/{name}")
async def api_get_character(name: str):
    """Get a character's details."""
    from dataclasses import asdict
    char = load_character(name)
    if char is None:
        raise HTTPException(status_code=404, detail=f"Character '{name}' not found")
    return asdict(char)


@app.put("/api/characters/{name}")
async def api_update_character(name: str, body: UpdateCharacterBody):
    """Update a character's details."""
    updates = {k: v for k, v in body.dict().items() if v is not None}
    result = update_character(name, updates)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.delete("/api/characters/{name}")
async def api_delete_character(name: str):
    """Delete a character."""
    result = delete_character(name)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/characters/{name}/activate")
async def api_activate_character(name: str):
    """Set a character as the active character."""
    result = set_active_character(name)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/characters/{name}/lora")
async def api_register_lora(name: str, lora_filename: str):
    """Register a trained LoRA file with a character."""
    result = register_trained_lora(name, lora_filename)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Phase 1: Dataset Tools ────────────────────────────────────────

@app.get("/api/dataset/guide")
async def api_dataset_guide():
    """Get the photography guide for preparing character images."""
    return get_dataset_guide()


@app.get("/api/dataset/guide/{character_name}")
async def api_shooting_guide(character_name: str):
    """Get the full shooting guide and save it for a character."""
    file_path = save_guide_json(character_name)
    guide = get_full_shooting_guide()
    return {"guide": guide, "saved_to": file_path}


@app.post("/api/dataset/validate")
async def api_validate_dataset(character_name: str):
    """Validate a character's dataset for training readiness."""
    from backend.utils.file_manager import PROJECT_ROOT
    dataset_dir = str(PROJECT_ROOT / "datasets" / character_name)
    result = validate_dataset(dataset_dir)
    return {
        "valid": result.valid,
        "total_images": result.total_images,
        "issues": result.issues,
        "warnings": result.warnings,
        "suggestions": result.suggestions,
        "stats": {
            "total_images": result.stats.total_images,
            "avg_width": result.stats.avg_width,
            "avg_height": result.stats.avg_height,
            "total_size_mb": round(result.stats.total_size_mb, 2),
            "resolutions": result.stats.resolutions,
        },
    }


@app.post("/api/dataset/analyze")
async def api_analyze_dataset(character_name: str):
    """Get comprehensive analysis of a character's dataset."""
    from backend.utils.file_manager import PROJECT_ROOT
    dataset_dir = str(PROJECT_ROOT / "datasets" / character_name)
    return analyze_dataset(dataset_dir)


@app.post("/api/dataset/prepare")
async def api_prepare_dataset(body: DatasetPrepareBody):
    """Resize images and generate captions for training."""
    from backend.utils.file_manager import PROJECT_ROOT
    raw_dir = str(PROJECT_ROOT / "datasets" / body.character_name)
    prepared_dir = str(PROJECT_ROOT / "datasets" / body.character_name / "prepared")

    # Step 1: Resize
    resize_result = resize_images(
        input_dir=raw_dir,
        output_dir=prepared_dir,
        size=body.resolution,
        maintain_aspect=body.maintain_aspect,
    )

    # Step 2: Auto-caption
    caption_result = auto_caption(
        image_dir=prepared_dir,
        trigger_word=body.trigger_word,
    )

    return {
        "resize": resize_result,
        "captions": caption_result,
        "prepared_dir": prepared_dir,
    }


# ── Phase 1: Training ─────────────────────────────────────────────

@app.post("/api/training/config")
async def api_training_config(body: TrainingConfigBody):
    """Generate a LoRA training configuration."""
    if body.use_recommended:
        # Auto-detect based on dataset + GPU
        from backend.utils.file_manager import PROJECT_ROOT
        from backend.utils.dataset_tools import scan_images
        dataset_dir = str(PROJECT_ROOT / "datasets" / body.character_name / "prepared")
        images = scan_images(dataset_dir)
        if not images:
            dataset_dir = str(PROJECT_ROOT / "datasets" / body.character_name)
            images = scan_images(dataset_dir)
        config = get_recommended_config(len(images), body.gpu_vram_gb)
        config.character_name = body.character_name
        config.trigger_word = body.trigger_word
        config.pretrained_model = body.pretrained_model
    else:
        config = TrainingConfig(
            character_name=body.character_name,
            trigger_word=body.trigger_word,
            pretrained_model=body.pretrained_model,
            network_rank=body.network_rank,
            network_alpha=body.network_alpha,
            resolution=body.resolution,
            batch_size=body.batch_size,
            epochs=body.epochs,
            learning_rate=body.learning_rate,
        )

    kohya_config = generate_kohya_config(config)
    config_path = save_training_config(config)

    return {
        "config": kohya_config,
        "config_path": config_path,
        "message": "Training config generated. Use /api/training/start to begin.",
    }


@app.post("/api/training/start")
async def api_start_training(body: TrainingConfigBody):
    """Launch LoRA training (generates config + command)."""
    config = TrainingConfig(
        character_name=body.character_name,
        trigger_word=body.trigger_word,
        pretrained_model=body.pretrained_model,
        network_rank=body.network_rank,
        network_alpha=body.network_alpha,
        resolution=body.resolution,
        batch_size=body.batch_size,
        epochs=body.epochs,
        learning_rate=body.learning_rate,
    )
    result = start_training(config)
    return result


@app.get("/api/training/status")
async def api_training_status():
    """Get current training progress."""
    return get_training_status()


@app.post("/api/training/stop")
async def api_stop_training():
    """Stop the current training run."""
    return stop_training()


# ── Phase 1: ComfyUI Status ───────────────────────────────────────

@app.get("/api/comfyui/status")
async def api_comfyui_status():
    """Check ComfyUI connection and available models."""
    status = image_service.check_comfyui()
    if status["connected"]:
        status["checkpoints"] = image_service.get_checkpoints()
        status["loras"] = image_service.get_loras()
    return status


# ── Phase 1: Face Discovery ──────────────────────────────────────

@app.get("/api/discovery/variations")
async def api_get_variations():
    """Get available face and body variation options."""
    return {
        "face": get_face_variations(),
        "body": get_body_variations(),
    }


@app.post("/api/discovery/face")
async def api_face_discovery(body: FaceDiscoveryBody):
    """Launch face discovery — generates diverse face images."""
    result = generate_face_discovery(
        character_name=body.character_name,
        base_description=body.base_description,
        checkpoint=body.checkpoint,
        lora_trigger=body.lora_trigger,
        lora_name=body.lora_name,
        lora_strength=body.lora_strength,
        angles=body.angles,
        lighting_styles=body.lighting,
        expressions=body.expressions,
        width=body.width,
        height=body.height,
        steps=body.steps,
        cfg_scale=body.cfg_scale,
        comfyui_host=config.comfyui.host,
        comfyui_port=config.comfyui.port,
        limit=body.limit,
    )

    if not result["success"]:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@app.get("/api/discovery/face/{character_name}")
async def api_get_face_results(character_name: str):
    """Get generated face images for a character."""
    return get_discovery_results(character_name)


@app.post("/api/discovery/face/{character_name}/select")
async def api_select_identity(character_name: str, body: SelectIdentityBody):
    """Select face images for the character identity."""
    result = select_identity(character_name, body.selected_indices)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Phase 1: Body Consistency ─────────────────────────────────────

@app.post("/api/discovery/body")
async def api_body_consistency(body: BodyConsistencyBody):
    """Launch body consistency — generates body images in various poses."""
    result = generate_body_set(
        character_name=body.character_name,
        base_description=body.base_description,
        checkpoint=body.checkpoint,
        lora_trigger=body.lora_trigger,
        lora_name=body.lora_name,
        lora_strength=body.lora_strength,
        poses=body.poses,
        framings=body.framings,
        outfits=body.outfits,
        width=body.width,
        height=body.height,
        steps=body.steps,
        cfg_scale=body.cfg_scale,
        comfyui_host=config.comfyui.host,
        comfyui_port=config.comfyui.port,
        limit=body.limit,
        control_image_name=body.control_image_name,
    )

    if not result["success"]:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@app.get("/api/discovery/body/{character_name}")
async def api_get_body_results(character_name: str):
    """Get generated body images for a character."""
    return get_body_results(character_name)


@app.post("/api/discovery/body/{character_name}/select")
async def api_copy_body_to_dataset(
    character_name: str,
    body: Optional[SelectIdentityBody] = None,
):
    """Copy body images to dataset (all or selected)."""
    indices = body.selected_indices if body else None
    result = copy_body_to_dataset(character_name, indices)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/view")
async def api_view_image(path: str):
    image_path = Path(path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(image_path), media_type="image/png")


@app.get("/api/discovery/image")
async def api_discovery_image(path: str):
    """Serve a discovery image by absolute path (used by image_urls in manifests)."""
    image_path = Path(path)
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(image_path), media_type="image/png")


# ── Phase 2: Content Studio ───────────────────────────────────────

@app.post("/api/studio/generate")
async def api_studio_generate(body: StudioGenerateBody):
    """Generate high-quality content via ContentEngine."""
    try:
        if body.controlnet_enabled and body.control_image_name:
            result = content_engine.generate_with_controlnet(
                prompt=body.prompt,
                control_image_name=body.control_image_name,
                controlnet_name=body.controlnet_name,
                negative_prompt=body.negative_prompt,
                width=body.width,
                height=body.height,
                steps=body.steps,
                cfg_scale=body.cfg_scale,
                checkpoint=body.checkpoint,
                lora_name=body.lora_name,
                lora_strength=body.lora_strength,
                seed=body.seed,
            )
        else:
            result = content_engine.generate(
                prompt=body.prompt,
                negative_prompt=body.negative_prompt,
                width=body.width,
                height=body.height,
                steps=body.steps,
                cfg_scale=body.cfg_scale,
                checkpoint=body.checkpoint,
                lora_name=body.lora_name,
                lora_strength=body.lora_strength,
                seed=body.seed,
                use_hires_fix=body.use_hires_fix,
            )
        return {"success": True, "result": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload/image")
async def api_upload_image(file: UploadFile = File(...)):
    """Upload an image to ComfyUI input directory."""
    try:
        contents = await file.read()
        filename = file.filename
        # Use ComfyUI client to upload
        resp = content_engine.client.upload_image(contents, filename)
        return {"success": True, "filename": resp.get("name", filename)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Training Lab Endpoints ─────────────────────────────────────────────

@app.post("/api/dataset/validate")
async def api_validate_dataset(character_name: str):
    """Validate if a dataset exists for the character."""
    dataset_dir = PROJECT_ROOT / "datasets" / character_name
    if not dataset_dir.exists():
        return {"valid": False, "issues": ["Dataset directory not found"], "total_images": 0}
    
    images = list(dataset_dir.glob("*.png")) + list(dataset_dir.glob("*.jpg")) + list(dataset_dir.glob("*.jpeg"))
    if not images:
        return {"valid": False, "issues": ["No images found in dataset"], "total_images": 0}
    
    return {"valid": True, "issues": [], "total_images": len(images)}


@app.post("/api/dataset/prepare")
async def api_prepare_dataset(body: dict):
    """Prepare dataset (copy images, resize, caption)."""
    try:
        character_name = body.get("character_name")
        if not character_name:
            raise HTTPException(status_code=400, detail="character_name is required")
            
        # 1. Ensure dataset directory exists
        dataset_dir = PROJECT_ROOT / "datasets" / character_name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Copy images from discovery/body results if dataset is empty
        # This is a simplified logic - normally user selects specific images
        # For now, we'll assume the user wants to train on ALL generated images if they haven't manually curated
        
        # Check source directories
        sources = [
            PROJECT_ROOT / "outputs" / "discovery" / character_name / "faces",
            PROJECT_ROOT / "outputs" / "discovery" / character_name / "bodies"
        ]
        
        copied_count = 0
        for source in sources:
            if source.exists():
                for img_path in source.glob("*.png"):
                    target_path = dataset_dir / img_path.name
                    if not target_path.exists():
                        shutil.copy2(img_path, target_path)
                        copied_count += 1
        
        # 3. Create caption files (simplified for now)
        trigger_word = body.get("trigger_word", "ohm_person")
        # Reuse existing images list logic but refresh it
        images = list(dataset_dir.glob("*.png")) + list(dataset_dir.glob("*.jpg"))
        
        for img in images:
            txt_path = img.with_suffix(".txt")
            if not txt_path.exists():
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"{trigger_word}, best quality, photorealistic")
                    
        return {
            "success": True, 
            "message": f"Prepared {len(images)} images", 
            "copied": copied_count,
            "total": len(images)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dataset/guide/{name}")
async def api_dataset_guide(name: str):
    """Return photography guide for the character."""
    return {
        "title": f"Photography Guide for {name}",
        "steps": [
            "1. Close-up portraits (face only) - 10 images",
            "2. Upper body shots (waist up) - 10 images", 
            "3. Full body shots (head to toe) - 10 images",
            "4. Varied angles (front, side, 3/4 view)",
            "5. Different lighting conditions (studio, outdoor, natural)",
            "6. Consistent clothing for style training, varied for character training"
        ]
    }


@app.post("/api/training/config")
async def api_training_config(body: dict):
    """Generate training configuration."""
    try:
        # Check for auto-optimization
        if body.get("use_recommended", False):
            from backend.services.training_service import get_recommended_config
            
            char_name = body.get("character_name")
            if char_name:
                dataset_dir = PROJECT_ROOT / "datasets" / char_name
                img_count = len(list(dataset_dir.glob("*.png")) + list(dataset_dir.glob("*.jpg")))
                
                # Get optimized config (defaults to 4GB VRAM optimization if passed or default)
                vram = body.get("gpu_vram_gb", 4) # Default to 4GB for safety if not specified
                rec_config = get_recommended_config(img_count, vram)
                
                # Merge into body (user overrides take precedence? Or recommended?)
                # Usually recommended should overwrite defaults, but keep user specifics.
                # However, since we are generating config, let's reset to recommended
                # but keep character name / triggers.
                
                rec_dict = asdict(rec_config)
                # Update body with recommended values, preserving identity
                for k, v in rec_dict.items():
                    if k not in ["character_name", "trigger_word"]:
                        body[k] = v

        # Convert dict to TrainingConfig object
        # Filter out unknown keys
        valid_keys = TrainingConfig.__annotations__.keys()
        filtered_body = {k: v for k, v in body.items() if k in valid_keys}
        
        config = TrainingConfig(**filtered_body)
        config_path = save_training_config(config)
        
        return {"success": True, "config_path": config_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/start")
async def api_start_training(body: dict):
    """Start training process."""
    try:
        # Check for auto-optimization
        if body.get("use_recommended", False):
            from backend.services.training_service import get_recommended_config
            
            char_name = body.get("character_name")
            if char_name:
                dataset_dir = PROJECT_ROOT / "datasets" / char_name
                img_count = len(list(dataset_dir.glob("*.png")) + list(dataset_dir.glob("*.jpg")))
                
                vram = body.get("gpu_vram_gb", 4)
                rec_config = get_recommended_config(img_count, vram)
                
                rec_dict = asdict(rec_config)
                for k, v in rec_dict.items():
                    if k not in ["character_name", "trigger_word"]:
                        body[k] = v

        # Convert dict to TrainingConfig object
        valid_keys = TrainingConfig.__annotations__.keys()
        filtered_body = {k: v for k, v in body.items() if k in valid_keys}
        
        config = TrainingConfig(**filtered_body)
        
        # For now, since we don't have Kohya installed, we return the command
        # and a message instructing the user
        result = start_training(config)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/training/stop")
async def api_stop_training():
    """Stop training process."""
    return stop_training()


@app.get("/api/training/status")
async def api_training_status():
    """Get training status."""
    return get_training_status()

