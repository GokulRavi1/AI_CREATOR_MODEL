
import os
import sys
from huggingface_hub import snapshot_download

MODEL_ID = "runwayml/stable-diffusion-v1-5"

def download_model():
    print(f"Starting SUPER-LITE download for: {MODEL_ID}")
    print("Excluding safety-checker and redundant files to save space.")
    print("Target size: ~3.5GB")
    
    try:
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        
        # Explicitly allow patterns for the diffusers folder structure
        # This prevents downloading the massive root checkpoints
        
        ignore_patterns = [
            # Legacy root files (huge)
            "v1-5-pruned*", 
            "sd-v1-5.ckpt", 
            "*.ckpt", 
            "*.h5", 
            "*.msgpack", 
            "*.bin", 
            "*.onnx", 
            "*.pb",
            # Variants inside unet/text_encoder/vae to save space
            "*.fp16.safetensors",
            "*.non_ema.safetensors",
            "*.fp16.bin",
            # Safety Checker (1.22GB) - NOT needed for training
            "safety_checker/*",
            "feature_extractor/*" # Usually not needed for simple training
        ]

        
        local_dir = snapshot_download(
            repo_id=MODEL_ID,
            resume_download=True,
            local_files_only=False,
            ignore_patterns=ignore_patterns,
        )
        print(f"\nSUCCESS! Model downloaded to: {local_dir}")
        
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_model()
