"""
LoRA Training Service — Kohya SS Integration

Generates training configs, launches Kohya SS training,
and monitors progress for creating character LoRA models.
"""

import json
import subprocess
import threading
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime

from backend.utils.file_manager import PROJECT_ROOT
from backend.config import config as app_config



@dataclass
class TrainingConfig:
    """Configuration for Kohya SS LoRA training."""

    # Identity
    character_name: str = "character"
    trigger_word: str = "ohm_person"

    # Model
    pretrained_model: str = "runwayml/stable-diffusion-v1-5"
    output_name: str = "character_lora"

    # Network
    network_rank: int = 32
    network_alpha: int = 32
    network_module: str = "networks.lora"

    # Training
    resolution: int = 512
    batch_size: int = 1
    epochs: int = 12
    learning_rate: float = 1e-4
    text_encoder_lr: float = 5e-5
    unet_lr: float = 1e-4
    lr_scheduler: str = "cosine"
    lr_warmup_steps: int = 100

    # Optimizer
    optimizer_type: str = "AdamW8bit"

    # Data
    train_data_dir: str = ""
    reg_data_dir: str = ""

    # Saving
    save_every_n_epochs: int = 4
    save_model_as: str = "safetensors"

    # Performance
    mixed_precision: str = "fp16"
    gradient_checkpointing: bool = True
    gradient_accumulation_steps: int = 1
    max_token_length: int = 75
    xformers: bool = False # Disabled due to PyTorch 2.5.1 incompatibility
    cache_latents: bool = True

    # Misc
    seed: int = 42
    clip_skip: int = 1
    max_train_steps: int = 0  # 0 = use epochs instead
    sample_prompts: str = ""
    sample_every_n_epochs: int = 4
    
    # Data Loading (CPU Offloading)
    dataloader_num_workers: int = 8
    persistent_workers: bool = True


@dataclass
class TrainingStatus:
    """Status of an ongoing or completed training run."""
    state: str = "idle"  # idle, running, completed, failed
    status: str = "idle" # Alias for frontend compatibility
    current_epoch: int = 0
    total_epochs: int = 0
    current_step: int = 0
    total_steps: int = 0
    loss: float = 0.0
    loss_history: List[float] = field(default_factory=list)
    eta_seconds: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None


# Global training status
_current_status = TrainingStatus()
_training_process: Optional[subprocess.Popen] = None


def generate_kohya_config(config: TrainingConfig) -> dict:
    """
    Generate a Kohya SS TOML-compatible config dict.

    This produces the full set of parameters needed by
    Kohya SS's train_network.py script.
    """
    # Resolve paths
    if not config.train_data_dir:
        config.train_data_dir = str(PROJECT_ROOT / "datasets" / config.character_name)

    output_dir = str(PROJECT_ROOT / "models" / "loras")

    kohya_config = {
        # Model
        "pretrained_model_name_or_path": config.pretrained_model,
        "output_dir": output_dir,
        "output_name": config.output_name,
        "save_model_as": config.save_model_as,

        # Network
        "network_module": config.network_module,
        "network_dim": config.network_rank,
        "network_alpha": config.network_alpha,

        # Training
        "resolution": f"{config.resolution},{config.resolution}",
        "train_batch_size": config.batch_size,
        "max_train_epochs": config.epochs,
        "learning_rate": config.learning_rate,
        "text_encoder_lr": config.text_encoder_lr,
        "unet_lr": config.unet_lr,
        "lr_scheduler": config.lr_scheduler,
        "lr_warmup_steps": config.lr_warmup_steps,

        # Optimizer
        "optimizer_type": config.optimizer_type,

        # Data
        "train_data_dir": config.train_data_dir,
        "max_token_length": config.max_token_length,

        # Saving
        "save_every_n_epochs": config.save_every_n_epochs,

        # Performance
        "mixed_precision": config.mixed_precision,
        "gradient_checkpointing": config.gradient_checkpointing,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "xformers": config.xformers,
        "cache_latents": config.cache_latents,

        # Misc
        "seed": config.seed,
        "clip_skip": config.clip_skip,
        "shuffle_caption": True,
        "keep_tokens": 1,  # Keep trigger word fixed
        "caption_extension": ".txt",
        "enable_bucket": True,
        "min_bucket_reso": 256,
        "max_bucket_reso": 1024,

        # CPU Offloading
        "dataloader_num_workers": config.dataloader_num_workers,
        "persistent_workers": config.persistent_workers,
    }

    # Optional fields
    if config.reg_data_dir:
        kohya_config["reg_data_dir"] = config.reg_data_dir
    if config.max_train_steps > 0:
        kohya_config["max_train_steps"] = config.max_train_steps
        del kohya_config["max_train_epochs"]
    if config.sample_prompts:
        kohya_config["sample_prompts"] = config.sample_prompts
        kohya_config["sample_every_n_epochs"] = config.sample_every_n_epochs

    return kohya_config


def save_training_config(config: TrainingConfig) -> str:
    """
    Save training config to a JSON file in the character's directory.
    Returns the file path.
    """
    kohya_config = generate_kohya_config(config)

    # Save directory
    config_dir = PROJECT_ROOT / "datasets" / config.character_name
    config_dir.mkdir(parents=True, exist_ok=True)

    import toml
    
    config_path = config_dir / "training_config.toml"
    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump(kohya_config, f)

    return str(config_path)


def build_training_command(config: TrainingConfig, kohya_path: str = "") -> str:
    """
    Build the shell command to launch Kohya SS training.

    Args:
        config:     Training configuration
        kohya_path: Path to Kohya SS installation (if empty, assumes it's in PATH)

    Returns:
        Command string ready to execute.
    """
    config_path = save_training_config(config)

    if kohya_path:
        script = str(Path(kohya_path) / "train_network.py")
    else:
        script = "train_network.py"

    cmd = f'python "{script}" --config_file "{config_path}"'
    return cmd


import re

def get_training_status() -> dict:
    """Get current training status with log parsing."""
    global _current_status, _training_process
    
    # Check process status if running
    if _training_process:
        retcode = _training_process.poll()
        if retcode is not None:
            # Process finished
            if retcode == 0:
                _current_status.state = "completed"
            else:
                _current_status.state = "failed"
                _current_status.status = "failed"
                _current_status.error = f"Process exited with code {retcode}"
            
            _current_status.completed_at = datetime.now().isoformat()
            _training_process = None
            
        # Keep status in sync with state
        _current_status.status = _current_status.state
        
        # Parse log for progress
        if _current_status.output_path and Path(_current_status.output_path).exists():
            try:
                with open(_current_status.output_path, "r") as f:
                    # Read all lines (inefficient for huge logs, but okay for training logs)
                    lines = f.readlines()
                    
                    # Parse latest lines for progress
                    # Increase window to 100 lines to skip through warning noise on Windows
                    for line in reversed(lines[-100:]):
                        # Support both direct loss and average loss (newer Kohya)
                        loss_match = re.search(r"(?:avr_)?loss=([0-9.]+)", line)
                        if loss_match:
                            _current_status.loss = float(loss_match.group(1))
                            
                        # Epoch parsing
                        epoch_match = re.search(r"epoch\s+(\d+)/(\d+)", line.lower())
                        if epoch_match:
                            _current_status.current_epoch = int(epoch_match.group(1))
                            _current_status.total_epochs = int(epoch_match.group(2))

                        # Step parsing (tqdm format: 10/100)
                        # Flexible pattern to catch: "|  13/1600 [" or "13/1600 [" or "steps: 13/1600"
                        step_match = re.search(r"(\d+)/(\d+)\s+\[", line)
                        if not step_match:
                            step_match = re.search(r"steps:\s*(\d+)/(\d+)", line.lower())
                        
                        if step_match:
                            current = int(step_match.group(1))
                            total = int(step_match.group(2))
                            if total > 0:
                                _current_status.current_step = current
                                _current_status.total_steps = total
                                # Stop once we find the latest progress line
                                break
            except Exception:
                pass

    return asdict(_current_status)


def start_training(config: TrainingConfig, kohya_path: str = "") -> dict:
    """
    Launch LoRA training as a background process.

    NOTE: Requires Kohya SS to be installed separately.
    This builds the config and command, then launches it.

    Returns:
        Status dict with command and state info.
    """
    global _current_status, _training_process

    if _current_status.state == "running":
        return {
            "success": False,
            "error": "Training already in progress",
            "status": asdict(_current_status),
        }

    # Determine paths
    if not kohya_path:
        # Use configured path
        configured_path = Path(app_config.lora.kohya_ss_path)
        if not configured_path.is_absolute():
            # Resolve relative to PROJECT_ROOT (e.g. "../kohya_ss")
            # Note: PROJECT_ROOT is ai_pipeline/. Parent is workspace root.
            # If config is "../kohya_ss", we want ai_pipeline/../kohya_ss which is workspace/kohya_ss
            configured_path = (PROJECT_ROOT / configured_path).resolve()
            
        if configured_path.exists():
            kohya_path = str(configured_path)
    
    cmd = build_training_command(config, kohya_path)
    config_path = save_training_config(config)

    # Launch process if Kohya is available
    if kohya_path:
        venv_python = Path(kohya_path) / "venv" / "Scripts" / "python.exe"
        script_path = Path(kohya_path) / "sd-scripts" / "train_network.py"
        
        print(f"DEBUG: Checking Kohya paths:")
        print(f"DEBUG: Kohya Path: {kohya_path}")
        print(f"DEBUG: Venv Python ({venv_python.exists()}): {venv_python}")
        print(f"DEBUG: Script Path ({script_path.exists()}): {script_path}")
        
        if venv_python.exists() and script_path.exists():
            # Construct actual command with full paths
            full_cmd = [
                str(venv_python),
                str(script_path),
                "--config_file",
                str(config_path)
            ]
            
            # Create log file
            log_dir = PROJECT_ROOT / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = open(log_dir / f"training_{config.character_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", "w")
            
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                
                # Write debug info to log file instead of print (safeguard against console encoding errors)
                log_file.write(f"DEBUG: Launching training with command: {full_cmd}\n")
                log_file.write(f"DEBUG: CWD: {PROJECT_ROOT}\n")
                log_file.write(f"DEBUG: Env PYTHONIOENCODING: {env.get('PYTHONIOENCODING')}\n")
                log_file.flush()

                # Create separate error log
                error_log_path = log_dir / f"training_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                error_file = open(error_log_path, "w")
                
                # Check if script exists
                script_path = full_cmd[1] if len(full_cmd) > 1 else ""
                log_file.write(f"DEBUG: Script existence check: {os.path.exists(script_path)}\n")
                log_file.flush()

                _training_process = subprocess.Popen(
                    full_cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT, 
                    cwd=str(PROJECT_ROOT),
                    env=env
                )
                
                # Close file handle in parent process so it can be read by status checker
                log_file.close()
                
                # Update status
                _current_status = TrainingStatus(
                    state="running",
                    current_epoch=0,
                    total_epochs=config.epochs,
                    started_at=datetime.now().isoformat(),
                    output_path=str(log_file.name)
                )
                
                return {
                    "success": True,
                    "message": "Training started in background",
                    "pid": _training_process.pid,
                    "status": asdict(_current_status)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to start training process: {str(e)}",
                    "status": asdict(_current_status)
                }

    # Fallback if no Kohya found
    return {
        "success": True,
        "message": "Training configuration generated (Kohya not found for auto-start)",
        "config_path": config_path,
        "command": cmd,
        "status": asdict(_current_status),
        "instructions": (
            "To start training, run the command above in a terminal with "
            "Kohya SS installed. The trained LoRA will be saved to models/loras/"
        ),
    }


def stop_training() -> dict:
    """Stop the current training process."""
    global _current_status, _training_process

    if _training_process and _training_process.poll() is None:
        _training_process.terminate()
        _training_process = None

    _current_status.state = "stopped"
    _current_status.completed_at = datetime.now().isoformat()

    return {"success": True, "status": asdict(_current_status)}


def get_recommended_config(image_count: int, gpu_vram_gb: int = 8) -> TrainingConfig:
    """
    Get recommended training config based on dataset size and GPU.
    Optimized for RTX 3050 (4GB) and similar low-VRAM cards.
    """
    config = TrainingConfig()

    # Adjust based on VRAM
    if gpu_vram_gb <= 4:
        # Ultra-Low VRAM Mode (4GB) - User's RTX 3050 Case
        config.resolution = 512
        config.batch_size = 1
        config.mixed_precision = "fp16"
        config.gradient_checkpointing = True
        config.cache_latents = True
        config.optimizer_type = "AdamW8bit"
        config.network_rank = 16   # Lower rank saves VRAM
        config.network_alpha = 8   # Lower alpha for stability
        config.xformers = False    # Disable xformers (use PyTorch SDPA)
        
        # CPU Optimization
        config.dataloader_num_workers = 8 # Maximize Ryzen 7 usage
        config.persistent_workers = True
        
    elif gpu_vram_gb <= 6:
        config.resolution = 512
        config.batch_size = 1
        config.mixed_precision = "fp16"
        config.gradient_checkpointing = True
        config.cache_latents = True
        config.network_rank = 32
        config.network_alpha = 16
        config.xformers = False
        config.dataloader_num_workers = 8
        
    elif gpu_vram_gb <= 8:
        config.resolution = 512
        config.batch_size = 1
        config.network_rank = 32
        config.network_alpha = 32
        config.xformers = False
        config.dataloader_num_workers = 8
        
    elif gpu_vram_gb <= 12:
        config.resolution = 768
        config.batch_size = 2
        config.network_rank = 32
        config.network_alpha = 32
        config.dataloader_num_workers = 8
        
    else:
        config.resolution = 768
        config.batch_size = 4
        config.network_rank = 64
        config.network_alpha = 64
        config.dataloader_num_workers = 8

    # Adjust epochs based on dataset size
    if image_count < 20:
        config.epochs = 15
    elif image_count < 40:
        config.epochs = 12
    else:
        config.epochs = 10

    return config
