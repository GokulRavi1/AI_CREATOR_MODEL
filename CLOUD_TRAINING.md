# AI Pipeline - Cloud Training Guide

## ⚠️ DO NOT PUSH `ComfyUI` or `kohya_ss` to GitHub!
These folders are too large (GBs) and will break your GitHub upload. 
Instead, we **re-install** them fresh in the cloud using the scripts below.

## 🚀 Option 1: Google Colab (Best for Beginners)
**Pros**: Free T4 GPU, easy to use, integrates with Drive.
**Cons**: Disconnects after ~12 hours, sometimes no GPUs available.

**Instructions**:
1.  **Repo Setup**: Push ONLY this `ai_pipeline` folder to GitHub.
2.  **Go to Colab**: [colab.research.google.com](https://colab.research.google.com/) -> New Notebook.
3.  **Runtime**: Runtime > Change runtime type > **T4 GPU**.
4.  **Copy-Paste** the following cells:

### Cell 1: Setup & Clone
```python
from google.colab import drive
import os

# 1. Mount Google Drive (to save your trained models!)
drive.mount('/content/drive')

# 2. Install Dependencies (Kohya & Requirements)
!apt-get -y install -qq aria2
!git clone https://github.com/bmaltais/kohya_ss.git
%cd kohya_ss
!./setup.sh -n

# 3. Clone YOUR Code
# Replace with your actual repo URL!
%cd /content
!git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git ai_pipeline

# 4. Install Project Requirements
%cd /content/ai_pipeline
!pip install -r requirements.txt
```

### Cell 2: Configure & Train
```python
import os

# Define Paths
os.environ['KOHYA_DIR'] = "/content/kohya_ss"
os.environ['PROJECT_DIR'] = "/content/ai_pipeline"
os.environ['OUTPUT_DIR'] = "/content/drive/MyDrive/AI_Pipeline_Outputs"

# Create Output Dir in Drive
!mkdir -p "$OUTPUT_DIR"

# Run Training (Adjusted for Colab T4)
!accelerate launch --num_cpu_threads_per_process=2 \
    "$KOHYA_DIR/sd-scripts/train_network.py" \
    --pretrained_model_name_or_path="runwayml/stable-diffusion-v1-5" \
    --dataset_config="$PROJECT_DIR/config/dataset_config.toml" \
    --output_dir="$OUTPUT_DIR" \
    --output_name="my_cloud_model" \
    --save_model_as=safetensors \
    --prior_loss_weight=1.0 \
    --max_train_epochs=10 \
    --learning_rate=1e-4 \
    --optimizer_type="AdamW8bit" \
    --xformers \
    --mixed_precision="fp16"
```

## ⚡ Option 2: Kaggle Kernels (More Power)
**Pros**: Often gives **2x T4 GPUs**, 30 hours/week usage limit (reset weekly).
**Cons**: Slightly more complex interface than Colab.

**Instructions**:
1.  Go to [Kaggle](https://www.kaggle.com/) -> Create -> New Notebook.
2.  **Settings** (Right sidebar): Accelerator -> **GPU T4 x2**.
3.  Use the same code blocks as Colab (start from `# 2. Install Dependencies` since Drive mounting is different).

## 🌩️ Option 3: Other Free "Powerful VMs"

### Lightning.ai (Studio)
- **What**: A cloud IDE that feels like VS Code in the browser.
- **Free Tier**: ~22 GPU hours/month.
- **Why**: Persistent environment (files don't vanish as easily as Colab).

### Oracle Cloud "Always Free" (ARM Only)
- **What**: Ampere A1 Compute (4 OCPUs, 24GB RAM).
- **Pros**: **It is a real VM** (VPS), runs 24/7 forever.
- **Cons**: **NO GPU** in the always-free tier. Good for hosting the *backend* or database, but **too slow for training SD**.

### Paperspace Gradient
- **What**: Free GPU Jupyter notebooks.
- **Cons**: Very hard to get a free machine allocated (often "Out of Capacity").

## 📦 What to Push to GitHub?
- [x] `ai_pipeline/` (Your code)
- [x] `requirements.txt`
- [x] `config/` (Your configs)

## ❌ What NOT to Push?
- [ ] `ComfyUI/` (Too big, install in cloud if needed)
- [ ] `kohya_ss/` (Too big, install in cloud)
- [ ] `venv/` (Local only)
- [ ] `models/` (Download in cloud or use Drive)
