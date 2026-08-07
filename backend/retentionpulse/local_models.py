from __future__ import annotations

from pathlib import Path
from typing import Any


def transcribe_local(audio_path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    model_name = __import__("os").getenv("RETENTIONPULSE_WHISPER_MODEL", "").strip()
    if not model_name:
        return [], ["RETENTIONPULSE_WHISPER_MODEL is not configured; transcription is unavailable."]
    if not Path(model_name).exists():
        return [], ["Whisper model path is not present locally; transcription is unavailable in offline mode."]
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return [], ["faster-whisper is not installed; transcription is unavailable."]
    try:
        model = WhisperModel(model_name, device=__import__("os").getenv("RETENTIONPULSE_WHISPER_DEVICE", "cpu"), compute_type=__import__("os").getenv("RETENTIONPULSE_WHISPER_COMPUTE_TYPE", "int8"), download_root=__import__("os").getenv("RETENTIONPULSE_MODEL_CACHE", "./model-cache"))
        segments, _ = model.transcribe(str(audio_path), word_timestamps=True, vad_filter=True)
        transcript = []
        for segment in segments:
            words = [{"word": word.word.strip(), "start": word.start, "end": word.end, "probability": word.probability} for word in (segment.words or [])]
            transcript.append({"start": segment.start, "end": segment.end, "text": segment.text.strip(), "words": words})
        return transcript, []
    except Exception:
        return [], ["The local Whisper model could not process this audio track; transcription is unavailable."]


def embed_text_and_frames(text: str, frames: list[Any]) -> tuple[list[float] | None, list[list[float]], list[str]]:
    model_name = __import__("os").getenv("RETENTIONPULSE_EMBEDDING_MODEL", "").strip()
    if not model_name:
        return None, [], ["RETENTIONPULSE_EMBEDDING_MODEL is not configured; semantic drift is unavailable."]
    try:
        import torch
        from PIL import Image
        from transformers import CLIPModel, CLIPProcessor
    except ImportError:
        return None, [], ["The local CLIP dependencies are not installed; semantic drift is unavailable."]
    try:
        processor = CLIPProcessor.from_pretrained(model_name, local_files_only=True)
        model = CLIPModel.from_pretrained(model_name, local_files_only=True)
        images = [Image.fromarray(frame if getattr(frame, "ndim", 2) == 2 else frame[:, :, ::-1]) for frame in frames]
        inputs = processor(text=[text], images=images, return_tensors="pt", padding=True)
        with torch.no_grad():
            text_vector = model.get_text_features(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"])[0]
            image_vector = model.get_image_features(pixel_values=inputs["pixel_values"])
        text_vector = torch.nn.functional.normalize(text_vector, dim=0).tolist()
        image_vectors = torch.nn.functional.normalize(image_vector, dim=1).tolist()
        return text_vector, image_vectors, []
    except Exception:
        return None, [], ["The local CLIP model is not provisioned; semantic drift is unavailable."]
