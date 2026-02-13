"""
Image Generation Service — Real ComfyUI Integration

Connects to a running ComfyUI instance to generate images using
LoRA-locked characters, configurable prompts, and various settings.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

from backend.services.comfyui_client import ComfyUIClient
from backend.utils.file_manager import PROJECT_ROOT


@dataclass
class ImageRequest:
    prompt: str
    character_lora: Optional[str] = None
    lora_weight: float = 0.8
    width: int = 512
    height: int = 512
    steps: int = 25
    cfg_scale: float = 7.5
    seed: int = -1
    negative_prompt: str = "blurry, low quality, distorted, deformed, ugly, bad anatomy"
    controlnet_module: Optional[str] = None
    controlnet_image: Optional[str] = None
    checkpoint: str = ""
    sampler: str = "euler_ancestral"
    scheduler: str = "normal"


@dataclass
class ImageResult:
    image_path: str
    prompt_used: str
    seed: int
    timestamp: str
    status: str = "success"
    images: Optional[List[str]] = None


class ImageService:
    """
    Handles image generation by communicating with ComfyUI's API.

    Builds workflow JSON, submits via WebSocket/HTTP, and returns
    real generated images.
    """

    def __init__(self, comfyui_host: str = "127.0.0.1", comfyui_port: int = 8188):
        self.client = ComfyUIClient(host=comfyui_host, port=comfyui_port)
        self.default_output = str(PROJECT_ROOT / "outputs" / "images")

    def check_comfyui(self) -> dict:
        """Check if ComfyUI is reachable."""
        return self.client.check_connection()

    def get_checkpoints(self) -> List[str]:
        """Get available SD checkpoints from ComfyUI."""
        return self.client.get_available_checkpoints()

    def get_loras(self) -> List[str]:
        """Get available LoRA models from ComfyUI."""
        return self.client.get_available_loras()

    async def generate(self, request: ImageRequest) -> ImageResult:
        """
        Generate an image using ComfyUI.

        If ComfyUI is not connected, returns a stub result with error status.
        """
        connection = self.client.check_connection()

        if not connection["connected"]:
            return ImageResult(
                image_path="",
                prompt_used=request.prompt,
                seed=request.seed if request.seed != -1 else 0,
                timestamp=datetime.now().isoformat(),
                status=f"ComfyUI not connected at {self.client.base_url}",
            )

        result = self.client.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            checkpoint=request.checkpoint,
            width=request.width,
            height=request.height,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            seed=request.seed,
            sampler=request.sampler,
            scheduler=request.scheduler,
            lora_name=request.character_lora or "",
            lora_strength=request.lora_weight,
            output_dir=self.default_output,
            prefix="gen",
        )

        if result["success"]:
            return ImageResult(
                image_path=result["images"][0] if result["images"] else "",
                prompt_used=request.prompt,
                seed=result.get("seed", request.seed),
                timestamp=result["timestamp"],
                status="success",
                images=result["images"],
            )
        else:
            return ImageResult(
                image_path="",
                prompt_used=request.prompt,
                seed=request.seed,
                timestamp=datetime.now().isoformat(),
                status=f"error: {result.get('error', 'Unknown')}",
            )

    async def generate_batch(self, requests: List[ImageRequest]) -> List[ImageResult]:
        """Generate multiple images in sequence."""
        results = []
        for req in requests:
            result = await self.generate(req)
            results.append(result)
        return results

    def get_available_loras(self) -> List[str]:
        """List available LoRA models from ComfyUI."""
        return self.client.get_available_loras()
