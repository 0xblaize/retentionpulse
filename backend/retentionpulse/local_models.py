from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any


_model_lock = threading.Lock()
_whisper_cache: dict[tuple[str, str, str, str], Any] = {}
_embedding_cache: dict[tuple[str], tuple[Any, Any]] = {}

# Single key drives both the LLM repair plan and Groq Whisper transcription.
_GROQ_KEY_ENV = "RETENTIONPULSE_LLM_API_KEY"
_GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"
_GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


def model_readiness() -> dict[str, bool]:
    whisper_model = os.getenv("RETENTIONPULSE_WHISPER_MODEL", "").strip()
    embedding_model = os.getenv("RETENTIONPULSE_EMBEDDING_MODEL", "").strip()
    groq_key = os.getenv(_GROQ_KEY_ENV, "").strip()
    return {
        # Transcription is available if a local model exists OR a Groq key is set.
        "transcription": (bool(whisper_model) and Path(whisper_model).exists()) or bool(groq_key),
        "embeddings": bool(embedding_model) and Path(embedding_model).exists(),
    }


def _transcribe_via_groq(audio_path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Transcribe audio using Groq's hosted Whisper API.

    Uses RETENTIONPULSE_LLM_API_KEY (same key as the repair plan).
    Groq Whisper supports up to 25 MB per request; a 5-min 16 kHz mono WAV
    is ~9.6 MB, well within the limit.
    """
    api_key = os.getenv(_GROQ_KEY_ENV, "").strip()
    if not api_key:
        return [], ["No Groq API key configured (RETENTIONPULSE_LLM_API_KEY); transcription unavailable."]

    try:
        import httpx
    except ImportError:
        return [], ["httpx is not installed; Groq transcription unavailable."]

    try:
        audio_bytes = Path(audio_path).read_bytes()
        response = httpx.post(
            _GROQ_TRANSCRIPTION_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            # Use list-of-tuples so httpx preserves duplicate keys for array params.
            data=[
                ("model", _GROQ_WHISPER_MODEL),
                ("response_format", "verbose_json"),
                ("timestamp_granularities[]", "word"),
                ("timestamp_granularities[]", "segment"),
            ],
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            timeout=httpx.Timeout(120.0, connect=10.0),
        )
        response.raise_for_status()
        body = response.json()
    except Exception as exc:
        return [], [f"Groq Whisper transcription failed: {str(exc)[:200]}"]

    # Map Groq response → internal transcript shape.
    all_words: list[dict[str, Any]] = body.get("words") or []
    transcript: list[dict[str, Any]] = []
    for segment in body.get("segments") or []:
        seg_start = float(segment.get("start", 0.0))
        seg_end = float(segment.get("end", 0.0))
        seg_words = [
            {
                "word": str(w.get("word", "")).strip(),
                "start": float(w.get("start", 0.0)),
                "end": float(w.get("end", 0.0)),
                "probability": float(w.get("probability", 1.0)),
            }
            for w in all_words
            if float(w.get("start", 0.0)) >= seg_start - 0.05
            and float(w.get("end", 0.0)) <= seg_end + 0.05
        ]
        transcript.append({
            "start": seg_start,
            "end": seg_end,
            "text": str(segment.get("text", "")).strip(),
            "words": seg_words,
        })
    return transcript, []


def transcribe_local(audio_path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Transcribe audio. Priority order:
    1. Local faster-whisper model (RETENTIONPULSE_WHISPER_MODEL must point to existing dir).
    2. Groq hosted Whisper API  (RETENTIONPULSE_LLM_API_KEY must be set).
    3. Unavailable — empty transcript + warning returned.
    """
    model_name = os.getenv("RETENTIONPULSE_WHISPER_MODEL", "").strip()

    # ── 1. Local faster-whisper ──────────────────────────────────────────────
    if model_name and Path(model_name).exists():
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            pass  # fall through to Groq
        else:
            device = os.getenv("RETENTIONPULSE_WHISPER_DEVICE", "cpu")
            compute_type = os.getenv("RETENTIONPULSE_WHISPER_COMPUTE_TYPE", "int8")
            cache_root = os.getenv("RETENTIONPULSE_MODEL_CACHE", "./model-cache")
            key = (model_name, device, compute_type, cache_root)
            try:
                with _model_lock:
                    model = _whisper_cache.get(key)
                    if model is None:
                        model = WhisperModel(
                            model_name, device=device,
                            compute_type=compute_type, download_root=cache_root,
                        )
                        _whisper_cache[key] = model
                segments, _ = model.transcribe(str(audio_path), word_timestamps=True, vad_filter=True)
                transcript = []
                for segment in segments:
                    words = [
                        {
                            "word": word.word.strip(),
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability,
                        }
                        for word in (segment.words or [])
                    ]
                    transcript.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip(),
                        "words": words,
                    })
                return transcript, []
            except Exception:
                pass  # fall through to Groq

    # ── 2. Groq hosted Whisper API ───────────────────────────────────────────
    return _transcribe_via_groq(audio_path)


def embed_text_and_frames(text: str, frames: list[Any]) -> tuple[list[float] | None, list[list[float]], list[str]]:
    model_name = os.getenv("RETENTIONPULSE_EMBEDDING_MODEL", "").strip()
    if not model_name:
        return None, [], ["RETENTIONPULSE_EMBEDDING_MODEL is not configured; semantic drift is unavailable."]
    try:
        import torch
        from PIL import Image
        from transformers import AutoModel, AutoProcessor
    except ImportError:
        return None, [], ["The local CLIP dependencies are not installed; semantic drift is unavailable."]
    try:
        with _model_lock:
            cached = _embedding_cache.get((model_name,))
            if cached is None:
                processor = AutoProcessor.from_pretrained(model_name, local_files_only=True)
                model = AutoModel.from_pretrained(model_name, local_files_only=True)
                model.eval()
                _embedding_cache[(model_name,)] = (processor, model)
            else:
                processor, model = cached
        images = [Image.fromarray(frame if getattr(frame, "ndim", 2) == 2 else frame[:, :, ::-1]) for frame in frames]
        text_inputs = processor(text=[text], return_tensors="pt", padding=True)
        image_inputs = processor(images=images, return_tensors="pt")
        with torch.no_grad():
            text_vector = model.get_text_features(**text_inputs)[0]
            image_vector = model.get_image_features(**image_inputs)
        text_vector = torch.nn.functional.normalize(text_vector, dim=-1).tolist()
        image_vectors = torch.nn.functional.normalize(image_vector, dim=-1).tolist()
        return text_vector, image_vectors, []
    except Exception:
        return None, [], ["The local CLIP model is not provisioned; semantic drift is unavailable."]

