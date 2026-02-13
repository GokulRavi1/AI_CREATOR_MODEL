"""
Content Engine — Advanced Generation Workflows for Content Studio

Handles complex ComfyUI workflows including:
- High-Resolution Generation (Hires. Fix)
- ControlNet (Pose/Structure guidance)
- Inpainting (Mask-based editing)
- Image-to-Image transformation
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.services.comfyui_client import ComfyUIClient
from backend.utils.file_manager import PROJECT_ROOT


class ContentEngine:
    """
    Engine for high-quality, controlled image generation.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        self.client = ComfyUIClient(host, port)
        self.output_dir = PROJECT_ROOT / "outputs" / "studio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def check_status(self) -> dict:
        """Check connection and available models."""
        return self.client.check_connection()

    def get_models(self) -> dict:
        """Get all available models (checkpoints, LoRAs, ControlNets)."""
        return {
            "checkpoints": self.client.get_available_checkpoints(),
            "loras": self.client.get_available_loras(),
            "controlnets": self.client.get_available_controlnets(),
        }

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 768,
        steps: int = 25,
        cfg_scale: float = 7.0,
        checkpoint: str = "",
        lora_name: str = "",
        lora_strength: float = 0.8,
        seed: int = -1,
        use_hires_fix: bool = False,
        upscale_by: float = 1.5,
        denoise: float = 0.55,
    ) -> dict:
        """
        Main generation entry point for Txt2Img / Hires Fix.
        """
        # Prefix for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"studio_{timestamp}"
        
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        # Select workflow builder
        if use_hires_fix:
            workflow = self.client.build_hires_fix_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                checkpoint=checkpoint,
                width=width,
                height=height,
                steps=steps,
                cfg_scale=cfg_scale,
                seed=seed,
                lora_name=lora_name,
                lora_strength=lora_strength,
                upscale_by=upscale_by,
                denoise=denoise
            )
            prefix += "_hires"
        else:
            workflow = self.client.build_txt2img_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                checkpoint=checkpoint,
                width=width,
                height=height,
                steps=steps,
                cfg_scale=cfg_scale,
                seed=seed,
                lora_name=lora_name,
                lora_strength=lora_strength
            )

        return self.client.execute_workflow(
            workflow=workflow,
            output_dir=str(self.output_dir),
            prefix=prefix,
            seed=seed
        )

    def generate_with_controlnet(
        self,
        prompt: str,
        control_image_name: str,
        controlnet_name: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 768,
        steps: int = 25,
        cfg_scale: float = 7.0,
        checkpoint: str = "",
        lora_name: str = "",
        lora_strength: float = 0.8,
        control_strength: float = 1.0,
        seed: int = -1,
    ) -> dict:
        """
        Generate using ControlNet (e.g., OpenPose).
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"studio_cn_{timestamp}"

        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        workflow = self.client.build_controlnet_workflow(
            prompt=prompt,
            control_image_name=control_image_name,
            controlnet_name=controlnet_name,
            negative_prompt=negative_prompt,
            checkpoint=checkpoint,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            seed=seed,
            lora_name=lora_name,
            lora_strength=lora_strength,
            control_strength=control_strength
        )

        return self.client.execute_workflow(
            workflow=workflow,
            output_dir=str(self.output_dir),
            prefix=prefix,
            seed=seed
        )
