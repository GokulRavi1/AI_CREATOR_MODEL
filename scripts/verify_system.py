
import sys
import os
from pathlib import Path
import subprocess
import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from backend.config import config
except ImportError:
    logger.error("Could not import backend.config. Run this script from the project root.")
    sys.exit(1)

def check_path(name, path_str, is_dir=True):
    path = Path(path_str)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    
    if path.exists():
        if is_dir and path.is_dir():
            logger.info(f"✅ {name}: Found at {path}")
            return True
        elif not is_dir and path.is_file():
            logger.info(f"✅ {name}: Found at {path}")
            return True
        else:
            logger.error(f"❌ {name}: Found at {path} but is not a {'directory' if is_dir else 'file'}")
            return False
    else:
        logger.error(f"❌ {name}: NOT FOUND at {path}")
        return False

def check_port(host, port, service_name):
    try:
        with socket.create_connection((host, port), timeout=2):
            logger.info(f"✅ {service_name}: Running on {host}:{port}")
            return True
    except (ConnectionRefusedError, socket.timeout):
        logger.warning(f"⚠️  {service_name}: Not reachable at {host}:{port} (might not be running yet)")
        return False

def verify_kohya_venv(kohya_path):
    venv_path = Path(kohya_path) / "venv"
    python_exe = venv_path / "Scripts" / "python.exe"
    
    if not python_exe.exists():
        logger.error(f"❌ Kohya Venv: Python executable not found at {python_exe}")
        return
        
    logger.info(f"✅ Kohya Venv: Found python at {python_exe}")
    
    # Check for Torch
    try:
        result = subprocess.run(
            [str(python_exe), "-c", "import torch; print(torch.__version__)"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            logger.info(f"✅ Kohya Torch: Version {result.stdout.strip()} installed")
        else:
            logger.error(f"❌ Kohya Torch: Failed to import. Error: {result.stderr}")
    except Exception as e:
        logger.error(f"❌ Kohya Torch Check: Failed to run. Error: {e}")

    # Check for xformers
    try:
        result = subprocess.run(
            [str(python_exe), "-c", "import xformers; print(xformers.__version__)"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            logger.info(f"✅ Kohya Xformers: Version {result.stdout.strip()} installed")
        else:
            logger.error(f"❌ Kohya Xformers: Failed to import. Error: {result.stderr}")
    except Exception as e:
        logger.error(f"❌ Kohya Xformers Check: Failed to run. Error: {e}")

def main():
    logger.info("=== Application Integration Verification ===")
    
    # 1. Directory Checks
    logger.info("--- Checking Critical Directories ---")
    # Check siblings relative to PROJECT_ROOT (ai_pipeline)
    check_path("ComfyUI", PROJECT_ROOT.parent / "ComfyUI")
    check_path("Kohya SS", PROJECT_ROOT.parent / "kohya_ss")
    
    check_path("Datasets Dir", "datasets")
    check_path("Outputs Dir", "outputs")
    
    # 2. Dependency Checks
    logger.info("--- Checking Kohya Integration ---")
    # Resolve ../kohya_ss from config relative to PROJECT_ROOT
    kohya_rel = Path(config.lora.kohya_ss_path)
    if not kohya_rel.is_absolute():
        kohya_full_path = (PROJECT_ROOT / kohya_rel).resolve()
    else:
        kohya_full_path = kohya_rel

    if kohya_full_path.exists():
        verify_kohya_venv(kohya_full_path)
    else:
        logger.error(f"❌ Skipping Kohya Venv check because Kohya dir is missing at {kohya_full_path}")

    # 3. Code Integration
    logger.info("--- Checking Config Integrity ---")
    logger.info(f"ℹ️  Unifying Config Loaded: {config.server.host}:{config.server.port}")
    logger.info(f"ℹ️  Kohya Path in Config: {config.lora.kohya_ss_path}")
    logger.info(f"ℹ️  Default Model: {config.generation.model}")

    # 4. Service Availability (Optional)
    logger.info("--- Checking Service Availability ---")
    check_port(config.comfyui.host, config.comfyui.port, "ComfyUI")
    check_port("127.0.0.1", 5432, "PostgreSQL") # Default PG port

    logger.info("=== Verification Complete ===")

if __name__ == "__main__":
    main()
