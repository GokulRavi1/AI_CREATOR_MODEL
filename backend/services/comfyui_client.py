"""
ComfyUI Client — Real HTTP + WebSocket integration

Connects to a running ComfyUI instance to:
- Queue image generation workflows
- Monitor progress via WebSocket
- Retrieve generated images
- Save outputs to disk
"""

import io
import json
import uuid
import struct
import urllib.request
import urllib.parse
import urllib.error
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from PIL import Image

from backend.utils.file_manager import PROJECT_ROOT
from backend.config import config


class ComfyUIClient:
    """
    Client for ComfyUI's REST + WebSocket API.

    Usage:
        client = ComfyUIClient("127.0.0.1", 8188)
        if client.check_connection():
            prompt_id = client.queue_prompt(workflow)
            client.wait_for_completion(prompt_id)
            images = client.get_images(prompt_id)
            paths = client.save_images(images, "outputs/images")
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.client_id = str(uuid.uuid4())

    # ── Connection ───────────────────────────────────────────────

    def check_connection(self) -> dict:
        """Check if ComfyUI is reachable and get system info."""
        try:
            req = urllib.request.Request(f"{self.base_url}/system_stats")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            return {
                "connected": True,
                "url": self.base_url,
                "system_stats": data,
            }
        except Exception as e:
            return {
                "connected": False,
                "url": self.base_url,
                "error": str(e),
            }

    def get_available_checkpoints(self) -> List[str]:
        """Get list of available SD checkpoints from ComfyUI."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/object_info/CheckpointLoaderSimple"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            ckpts = data.get("CheckpointLoaderSimple", {}).get(
                "input", {}
            ).get("required", {}).get("ckpt_name", [[]])[0]
            return ckpts if isinstance(ckpts, list) else []
        except Exception:
            return []

    def get_available_loras(self) -> List[str]:
        """Get list of available LoRA models from ComfyUI."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/object_info/LoraLoader"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            loras = data.get("LoraLoader", {}).get(
                "input", {}
            ).get("required", {}).get("lora_name", [[]])[0]
            return loras if isinstance(loras, list) else []
        except Exception:
            return []
    def get_available_controlnets(self) -> List[str]:
        """Get list of available ControlNet models."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/object_info/ControlNetLoader"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
            cns = data.get("ControlNetLoader", {}).get(
                "input", {}
            ).get("required", {}).get("control_net_name", [[]])[0]
            return cns if isinstance(cns, list) else []
        except Exception:
            return []

    def upload_image(self, image_data: bytes, filename: str) -> dict:
        """Upload an image to ComfyUI input directory."""
        try:
            files = {"image": (filename, image_data)}
            data = {"overwrite": "true"}
            response = requests.post(
                f"{self.base_url}/upload/image",
                files=files,
                data=data
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}


    # ── Workflow Building ────────────────────────────────────────

    def build_txt2img_workflow(
        self,
        prompt: str,
        negative_prompt: str = "blurry, low quality, distorted, deformed, ugly, bad anatomy",
        checkpoint: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 25,
        cfg_scale: float = 7.5,
        seed: int = -1,
        sampler: str = "euler_ancestral",
        scheduler: str = "normal",
        lora_name: str = "",
        lora_strength: float = 0.8,
        batch_size: int = 1,
    ) -> dict:
        """
        Build a txt2img workflow in ComfyUI API format.

        Node layout:
        [4] Checkpoint Loader
            → [6] CLIP Text Encode (positive)
            → [7] CLIP Text Encode (negative)
            → [3] KSampler
            → [8] VAE Decode
            → [9] Save Image

        If lora_name is provided, a LoRA Loader node [10] is inserted
        between the checkpoint and the text encoders.
        """
        import random

        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": checkpoint or config.generation.model,
                },
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": prompt,
                    "clip": ["4", 1],
                },
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["4", 1],
                },
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": batch_size,
                },
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2],
                },
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "ai_pipeline",
                    "images": ["8", 0],
                },
            },
        }

        # Insert LoRA loader if specified
        if lora_name:
            workflow["10"] = {
                "class_type": "LoraLoader",
                "inputs": {
                    "lora_name": lora_name,
                    "strength_model": lora_strength,
                    "strength_clip": lora_strength,
                    "model": ["4", 0],
                    "clip": ["4", 1],
                },
            }
            # Rewire: KSampler model → LoRA output
            workflow["3"]["inputs"]["model"] = ["10", 0]
            # Rewire: CLIP text encoders → LoRA CLIP output
            workflow["6"]["inputs"]["clip"] = ["10", 1]
            workflow["7"]["inputs"]["clip"] = ["10", 1]

        return workflow

    def build_hires_fix_workflow(
        self,
        prompt: str,
        negative_prompt: str = "blurry, low quality",
        checkpoint: str = "",
        width: int = 512,
        height: int = 768,
        steps: int = 25,
        cfg_scale: float = 7.5,
        seed: int = -1,
        lora_name: str = "",
        lora_strength: float = 0.8,
        upscale_by: float = 1.5,
        denoise: float = 0.55,
    ) -> dict:
        """
        Build a 2-pass Hires Fix workflow (Latent Upscale).
        
        Pass 1: Txt2Img (low res)
        Pass 2: Latent Upscale -> KSampler (finetune)
        """
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        # Base Txt2Img workflow
        workflow = self.build_txt2img_workflow(
            prompt, negative_prompt, checkpoint, width, height,
            steps, cfg_scale, seed, lora_name=lora_name, lora_strength=lora_strength
        )
        
        # Add Latent Upscale [11]
        workflow["11"] = {
            "class_type": "LatentUpscaleBy",
            "inputs": {
                "upscale_method": "nearest-exact",
                "scale_by": upscale_by,
                "samples": ["3", 0],  # From first KSampler
            }
        }
        
        # Add Second KSampler [12]
        workflow["12"] = {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": int(steps * 0.6) + 10, # Slightly more steps for refiner
                "cfg": cfg_scale,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": denoise,
                "model": workflow["3"]["inputs"]["model"],      # Same model
                "positive": workflow["3"]["inputs"]["positive"], # Same prompt
                "negative": workflow["3"]["inputs"]["negative"], # Same negative
                "latent_image": ["11", 0], # From Upscaler
            }
        }
        
        # Update VAE Decode to use second sampler output
        workflow["8"]["inputs"]["samples"] = ["12", 0]
        
        return workflow

    def build_controlnet_workflow(
        self,
        prompt: str,
        control_image_name: str,
        controlnet_name: str,
        negative_prompt: str = "blurry, low quality",
        checkpoint: str = "",
        width: int = 512,
        height: int = 768,
        steps: int = 25,
        cfg_scale: float = 7.5,
        seed: int = -1,
        lora_name: str = "",
        lora_strength: float = 0.8,
        control_strength: float = 1.0,
    ) -> dict:
        """
        Build a ControlNet workflow.
        
        Requires `control_image_name` to be present in ComfyUI input directory.
        """
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)

        # Base Txt2Img
        workflow = self.build_txt2img_workflow(
            prompt, negative_prompt, checkpoint, width, height,
            steps, cfg_scale, seed, lora_name=lora_name, lora_strength=lora_strength
        )
        
        # [14] ControlNet Loader
        workflow["14"] = {
            "class_type": "ControlNetLoader",
            "inputs": {
                "control_net_name": controlnet_name
            }
        }
        
        # [16] Load Reference Image
        workflow["16"] = {
            "class_type": "LoadImage",
            "inputs": {
                "image": control_image_name
            }
        }
        
        # [15] ControlNet Apply
        workflow["15"] = {
            "class_type": "ControlNetApply",
            "inputs": {
                "strength": control_strength,
                "conditioning": ["6", 0], # Positive conditioning from CLIP
                "control_net": ["14", 0],
                "image": ["16", 0]
            }
        }
        
        # Rewire KSampler positive to ControlNet output
        workflow["3"]["inputs"]["positive"] = ["15", 0]
        
        return workflow

    # ── Queue & Execute ──────────────────────────────────────────

    def queue_prompt(self, workflow: dict) -> str:
        """
        Submit a workflow to ComfyUI for execution.

        Returns the prompt_id for tracking.
        """
        payload = json.dumps({
            "prompt": workflow,
            "client_id": self.client_id,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        return data["prompt_id"]

    def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> dict:
        """
        Wait for a queued prompt to finish via WebSocket.

        Returns status dict with 'success' or 'error'.
        """
        import websocket
        import time

        ws_url = f"ws://{self.host}:{self.port}/ws?clientId={self.client_id}"
        ws = websocket.WebSocket()

        try:
            ws.connect(ws_url)
            ws.settimeout(timeout)

            start = time.time()
            progress = {"current": 0, "total": 0}

            while True:
                if time.time() - start > timeout:
                    return {"success": False, "error": "Timeout waiting for completion"}

                try:
                    out = ws.recv()
                except websocket.WebSocketTimeoutException:
                    return {"success": False, "error": "WebSocket timeout"}

                if isinstance(out, str):
                    msg = json.loads(out)
                    msg_type = msg.get("type", "")

                    if msg_type == "progress":
                        d = msg.get("data", {})
                        progress["current"] = d.get("value", 0)
                        progress["total"] = d.get("max", 0)

                    elif msg_type == "executing":
                        d = msg.get("data", {})
                        if d.get("node") is None and d.get("prompt_id") == prompt_id:
                            # Execution complete
                            return {"success": True, "progress": progress}

                    elif msg_type == "execution_error":
                        d = msg.get("data", {})
                        return {
                            "success": False,
                            "error": d.get("exception_message", "Unknown error"),
                        }
        finally:
            ws.close()

    def get_history(self, prompt_id: str) -> dict:
        """Get the execution history for a prompt."""
        req = urllib.request.Request(
            f"{self.base_url}/history/{prompt_id}"
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        return data.get(prompt_id, {})

    def get_images(self, prompt_id: str) -> List[dict]:
        """
        Fetch all generated images for a completed prompt.

        Returns list of dicts with 'filename', 'subfolder', 'type', 'image_data'.
        """
        history = self.get_history(prompt_id)
        outputs = history.get("outputs", {})

        images = []
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for img_info in node_output["images"]:
                    params = urllib.parse.urlencode({
                        "filename": img_info["filename"],
                        "subfolder": img_info.get("subfolder", ""),
                        "type": img_info.get("type", "output"),
                    })
                    req = urllib.request.Request(
                        f"{self.base_url}/view?{params}"
                    )
                    with urllib.request.urlopen(req) as resp:
                        image_data = resp.read()

                    images.append({
                        "filename": img_info["filename"],
                        "subfolder": img_info.get("subfolder", ""),
                        "type": img_info.get("type", "output"),
                        "image_data": image_data,
                    })

        return images

    def save_images(
        self,
        images: List[dict],
        output_dir: str,
        prefix: str = "gen",
    ) -> List[str]:
        """
        Save fetched images to disk.

        Returns list of saved file paths.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        saved = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, img in enumerate(images):
            filename = f"{prefix}_{timestamp}_{i:03d}.png"
            filepath = out_path / filename

            # Convert to PIL and save as PNG
            pil_img = Image.open(io.BytesIO(img["image_data"]))
            pil_img.save(str(filepath), "PNG")
            saved.append(str(filepath))

        return saved

    # ── High-Level Generate ──────────────────────────────────────

    def execute_workflow(
        self,
        workflow: dict,
        output_dir: str,
        prefix: str = "gen",
        seed: int = -1,
    ) -> dict:
        """
        Execute an arbitrary workflow: queue → wait → save.
        """
        # Queue
        prompt_id = self.queue_prompt(workflow)

        # Wait
        result = self.wait_for_completion(prompt_id)
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error", "Generation failed"),
                "prompt_id": prompt_id,
            }

        # Fetch images
        images = self.get_images(prompt_id)

        # Save to disk
        saved_paths = self.save_images(images, output_dir, prefix)

        return {
            "success": True,
            "images": saved_paths,
            "count": len(saved_paths),
            "prompt_id": prompt_id,
            "seed": seed,
            "timestamp": datetime.now().isoformat(),
        }

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        checkpoint: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 25,
        cfg_scale: float = 7.5,
        seed: int = -1,
        sampler: str = "euler_ancestral",
        scheduler: str = "normal",
        lora_name: str = "",
        lora_strength: float = 0.8,
        output_dir: str = "",
        prefix: str = "gen",
        batch_size: int = 1,
    ) -> dict:
        """
        Full generate pipeline: build workflow → queue → wait → save.

        Returns dict with 'success', 'images' (file paths), 'seed', etc.
        """
        if not negative_prompt:
            negative_prompt = (
                "blurry, low quality, distorted, deformed, ugly, "
                "bad anatomy, bad hands, missing fingers, extra fingers"
            )

        if not output_dir:
            output_dir = str(PROJECT_ROOT / "outputs" / "images")

        workflow = self.build_txt2img_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            checkpoint=checkpoint,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            seed=seed,
            sampler=sampler,
            scheduler=scheduler,
            lora_name=lora_name,
            lora_strength=lora_strength,
            batch_size=batch_size,
        )

        return self.execute_workflow(workflow, output_dir, prefix, seed)

    def generate_batch(
        self,
        prompts: List[dict],
        output_dir: str = "",
        checkpoint: str = "",
    ) -> List[dict]:
        """
        Generate multiple images from a list of prompt configs.

        Each item in prompts should have at minimum: {'prompt': '...'}
        Optional keys: negative_prompt, width, height, steps, cfg_scale,
                        seed, lora_name, lora_strength, prefix
        """
        results = []
        for i, p in enumerate(prompts):
            result = self.generate(
                prompt=p["prompt"],
                negative_prompt=p.get("negative_prompt", ""),
                checkpoint=checkpoint or p.get("checkpoint", ""),
                width=p.get("width", 512),
                height=p.get("height", 512),
                steps=p.get("steps", 25),
                cfg_scale=p.get("cfg_scale", 7.5),
                seed=p.get("seed", -1),
                lora_name=p.get("lora_name", ""),
                lora_strength=p.get("lora_strength", 0.8),
                output_dir=output_dir or p.get("output_dir", ""),
                prefix=p.get("prefix", f"batch_{i:03d}"),
            )
            results.append(result)
        return results
