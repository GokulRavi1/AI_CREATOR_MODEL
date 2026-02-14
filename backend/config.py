"""
Configuration loader for the AI Character Generation System.
Reads config.yaml and exposes settings as a singleton.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

import yaml
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


@dataclass
class ComfyUIConfig:
    host: str = "127.0.0.1"
    port: int = 8188
    workflow_dir: str = "./workflows"


@dataclass
class GenerationConfig:
    default_resolution: List[int] = field(default_factory=lambda: [512, 512])
    default_steps: int = 25
    default_cfg_scale: float = 7.5
    default_sampler: str = "euler_a"
    default_scheduler: str = "normal"
    model: str = "Realistic_Vision_V6.0_NV_B1_fp16.safetensors"


@dataclass
class LoRAConfig:
    default_weight: float = 0.8
    models_dir: str = "./models/loras"
    kohya_ss_path: str = "../kohya_ss"


@dataclass
class VoiceConfig:
    engine: str = "piper"
    model: str = "en_US-lessac-medium"
    sample_rate: int = 22050


@dataclass
class AvatarConfig:
    engine: str = "sadtalker"
    checkpoint_dir: str = "./models/sadtalker"


@dataclass
class VideoConfig:
    engine: str = "animatediff"
    fps: int = 8
    frames: int = 16
    motion_module: str = "mm_sd_v15_v2.ckpt"


@dataclass
class OutputConfig:
    base_dir: str = "./outputs"
    images_dir: str = "./outputs/images"
    videos_dir: str = "./outputs/videos"
    avatars_dir: str = "./outputs/avatars"
    audio_dir: str = "./outputs/audio"


@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True


@dataclass
class AppConfig:
    comfyui: ComfyUIConfig = field(default_factory=ComfyUIConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    lora: LoRAConfig = field(default_factory=LoRAConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    avatar: AvatarConfig = field(default_factory=AvatarConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


def _dict_to_dataclass(cls, data: dict):
    """Recursively populate a dataclass from a dict."""
    if data is None:
        return cls()
    fieldtypes = {f.name: f.type for f in cls.__dataclass_fields__.values()}
    kwargs = {}
    for key, value in data.items():
        if key in fieldtypes:
            kwargs[key] = value
    return cls(**kwargs)


def load_config() -> AppConfig:
    """Load configuration from config.yaml, falling back to defaults."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    else:
        raw = {}

    # Override with environment variables where applicable
    comfyui_data = raw.get("comfyui", {})
    comfyui_data["host"] = os.getenv("COMFYUI_HOST", comfyui_data.get("host", "127.0.0.1"))
    comfyui_data["port"] = int(os.getenv("COMFYUI_PORT", comfyui_data.get("port", 8188)))

    server_data = raw.get("server", {})
    server_data["host"] = os.getenv("SERVER_HOST", server_data.get("host", "0.0.0.0"))
    server_data["port"] = int(os.getenv("SERVER_PORT", server_data.get("port", 8000)))

    return AppConfig(
        comfyui=_dict_to_dataclass(ComfyUIConfig, comfyui_data),
        generation=_dict_to_dataclass(GenerationConfig, raw.get("generation")),
        lora=_dict_to_dataclass(LoRAConfig, raw.get("lora")),
        voice=_dict_to_dataclass(VoiceConfig, raw.get("voice")),
        avatar=_dict_to_dataclass(AvatarConfig, raw.get("avatar")),
        video=_dict_to_dataclass(VideoConfig, raw.get("video")),
        output=_dict_to_dataclass(OutputConfig, raw.get("output")),
        server=_dict_to_dataclass(ServerConfig, server_data),
    )


# Singleton instance
config = load_config()
