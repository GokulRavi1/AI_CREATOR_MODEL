# 🎭 AI Character Studio

> **Fixed AI Character Generation System** — Generate consistent character images, videos, and talking avatars from a single trained identity.

---

## 📋 Overview

A full-stack pipeline for creating and maintaining a permanent AI character identity through:

| Phase | Module | Status |
|-------|--------|--------|
| **0** | Project Setup & Backend | ✅ Ready |
| **1** | Character Identity Lock (LoRA Training) | 🔲 Planned |
| **2** | Image Generation (ComfyUI) | 🔲 Planned |
| **3** | Video/Reel Generation (AnimateDiff) | 🔲 Planned |
| **4** | Talking Avatar (SadTalker + TTS) | 🔲 Planned |
| **5** | Batch Automation | 🔲 Planned |
| **6** | Full UI Dashboard | 🔲 Planned |

---

## 🗂️ Project Structure

```
ai_pipeline/
├── backend/              # FastAPI server
│   ├── main.py           # App entry point + API endpoints
│   ├── config.py         # Configuration loader
│   ├── services/         # Generation service modules
│   │   ├── image_service.py
│   │   ├── video_service.py
│   │   ├── voice_service.py
│   │   └── avatar_service.py
│   └── utils/
│       ├── prompt_builder.py  # SD prompt construction
│       └── file_manager.py    # I/O helpers
├── ui/                   # Frontend dashboard
│   ├── index.html
│   ├── style.css
│   └── app.js
├── models/               # LoRA, checkpoints (gitignored)
├── datasets/             # Training images (gitignored)
├── workflows/            # ComfyUI workflow JSONs
├── outputs/              # Generated content (gitignored)
├── automation/
│   └── batch_generate.py # Batch content generation
├── logs/                 # Runtime logs (gitignored)
├── config.yaml           # Central configuration
├── requirements.txt      # Python dependencies
└── .env.example          # Environment template
```

---

## 🚀 Quick Start

### 1. Create virtual environment
```bash
cd ai_pipeline
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure (optional)
```bash
copy .env.example .env
# Edit .env and config.yaml as needed
```

### 4. Start the server
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 5. Open the dashboard
Navigate to **http://localhost:8000** in your browser.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check |
| `POST` | `/api/generate/image` | Generate character image |
| `POST` | `/api/generate/video` | Generate short video/reel |
| `POST` | `/api/generate/voice` | Text-to-speech synthesis |
| `POST` | `/api/generate/avatar` | Talking avatar video |
| `POST` | `/api/prompt/build` | Preview constructed prompt |
| `GET` | `/api/models` | List available models |
| `GET` | `/api/outputs/{category}` | List generated outputs |
| `GET` | `/api/presets` | Get UI preset options |
| `POST` | `/api/cleanup/{category}` | Clean up old outputs |

---

## ⚡ Phase Roadmap

### Phase 1 — Character Identity Lock
- Generate face discovery images → select best identity
- Prepare dataset (30–50 images, multiple angles/poses)
- Train LoRA with Kohya SS → `character.safetensors`

### Phase 2 — Image Generation
- Connect to ComfyUI API
- ControlNet integration (OpenPose, Depth, Canny)
- Prompt template engine with presets

### Phase 3 — Video Generation
- AnimateDiff motion modules
- Frame-to-video encoding
- Short reel generation (2–4 seconds)

### Phase 4 — Talking Avatar
- Piper TTS for speech synthesis
- SadTalker for facial animation
- Audio → lip-synced video pipeline

### Phase 5 — Automation
- Batch content generation from scene lists
- Randomized prompt diversity
- Weekly content scheduling

### Phase 6 — Full UI
- Complete React or enhanced HTML dashboard
- Real-time generation progress
- Content management & export

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | NVIDIA 6GB VRAM | NVIDIA 12GB+ VRAM |
| RAM | 16 GB | 32 GB |
| Storage | 40 GB SSD | 100 GB+ SSD |
| Python | 3.10+ | 3.10.x |
| OS | Windows 10/11 | Windows 11 |

---

## 📝 License

Private project — all rights reserved.
