"""
Voice / TTS Service — Piper TTS Stub

Phase 4 will connect this to:
- Piper TTS (lightweight, fast, offline)
- Coqui TTS (alternative, supports voice cloning)
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class VoiceRequest:
    text: str
    voice_model: str = "en_US-lessac-medium"
    speed: float = 1.0
    output_format: str = "wav"


@dataclass
class VoiceResult:
    audio_path: str
    duration_seconds: float
    text_length: int
    timestamp: str
    status: str = "success"


class VoiceService:
    """
    Text-to-Speech engine for generating character voice audio.

    In Phase 4 this will:
    - Load a Piper TTS ONNX voice model
    - Synthesize speech from input text
    - Save audio to WAV/MP3
    - Optionally support voice cloning with Coqui TTS
    """

    def __init__(self, engine: str = "piper", model: str = "en_US-lessac-medium"):
        self.engine = engine
        self.model = model

    async def synthesize(self, request: VoiceRequest) -> VoiceResult:
        """
        Convert text to speech audio.

        TODO (Phase 4):
        - Initialize Piper TTS with selected voice model
        - Synthesize audio from text
        - Save to output directory
        """
        estimated_duration = len(request.text.split()) * 0.4  # ~0.4s per word
        return VoiceResult(
            audio_path="outputs/audio/placeholder.wav",
            duration_seconds=estimated_duration,
            text_length=len(request.text),
            timestamp=datetime.now().isoformat(),
            status="stub — TTS engine not connected yet",
        )

    def get_available_voices(self):
        """
        List available voice models.

        TODO (Phase 4): Scan models directory for Piper .onnx files
        """
        return [
            {"name": "en_US-lessac-medium", "language": "English (US)", "quality": "medium"},
            {"name": "en_US-amy-medium", "language": "English (US)", "quality": "medium"},
        ]
