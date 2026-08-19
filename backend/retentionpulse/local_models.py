from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any


_model_lock = threading.Lock()
_whisper_cache: dict[tuple[str, str, str, str], Any] = {}
_embedding_cache: dict[tuple[str], tuple[Any, Any]] = {}


def model_readiness() -> dict[str, bool]:
    whisper_model = os.getenv("RETENTIONPULSE_WHISPER_MODEL", "").strip()
    embedding_model = os.getenv("RETENTIONPULSE_EMBEDDING_MODEL", "").strip()
    return {
        "transcription": bool(whisper_model) and Path(whisper_model).exists(),
        "embeddings": bool(embedding_model) and Path(embedding_model).exists(),
    }


def transcribe_local(audio_path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    model_name = os.getenv("RETENTIONPULSE_WHISPER_MODEL", "").strip()
    if not model_name:
        return [], ["RETENTIONPULSE_WHISPER_MODEL is not configured; transcription is unavailable."]
    if not Path(model_name).exists():
        return [], ["Whisper model directory is not present locally; transcription is unavailable in offline mode."]
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return [], ["faster-whisper is not installed; transcription is unavailable."]
    device = os.getenv("RETENTIONPULSE_WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("RETENTIONPULSE_WHISPER_COMPUTE_TYPE", "int8")
    cache_root = os.getenv("RETENTIONPULSE_MODEL_CACHE", "./model-cache")
    key = (model_name, device, compute_type, cache_root)
    try:
        with _model_lock:
            model = _whisper_cache.get(key)
            if model is None:
                model = WhisperModel(model_name, device=device, compute_type=compute_type, download_root=cache_root)
                _whisper_cache[key] = model
        segments, _ = model.transcribe(str(audio_path), word_timestamps=True, vad_filter=True)
        transcript = []
        for segment in segments:
            words = [{"word": word.word.strip(), "start": word.start, "end": word.end, "probability": word.probability} for word in (segment.words or [])]
            transcript.append({"start": segment.start, "end": segment.end, "text": segment.text.strip(), "words": words})
        return transcript, []
    except Exception:
        return [], ["The local Whisper model could not process this audio track; transcription is unavailable."]


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
