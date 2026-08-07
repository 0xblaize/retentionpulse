from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

from .analyzer import AnalysisResult
from .local_models import embed_text_and_frames, transcribe_local

ANALYZER_VERSION = "2.0.0-offline"
WINDOW_SECONDS = 0.5
LONG_PAUSE_SECONDS = 1.5


def _zone(score: float) -> str:
    if score >= 0.7:
        return "red"
    if score >= 0.35:
        return "yellow"
    return "green"


def _rms(samples: list[int]) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples)) / 32768.0


def _audio_windows(path: Path, duration: float) -> tuple[list[dict[str, float]], list[str], list[dict[str, Any]]]:
    warnings: list[str] = []
    ffmpeg = os.getenv("RETENTIONPULSE_FFMPEG", "ffmpeg")
    if shutil.which(ffmpeg) is None:
        return [], ["FFmpeg is unavailable; audio diagnostics were skipped."], []

    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temporary_file:
            temporary_path = temporary_file.name
        command = [ffmpeg, "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", temporary_path]
        result = subprocess.run(command, capture_output=True, timeout=60, check=False)
        if result.returncode != 0:
            return [], ["The audio track could not be extracted; audio diagnostics were skipped."], []
        with wave.open(temporary_path, "rb") as audio:
            sample_rate = audio.getframerate()
            samples_per_window = max(1, round(sample_rate * WINDOW_SECONDS))
            windows: list[dict[str, float]] = []
            index = 0
            while True:
                raw = audio.readframes(samples_per_window)
                if not raw:
                    break
                samples = [int.from_bytes(raw[offset:offset + 2], "little", signed=True) for offset in range(0, len(raw), 2)]
                energy = _rms(samples)
                windows.append({"timestamp": index * WINDOW_SECONDS, "energy": energy, "speech": 1.0 if energy >= 0.015 else 0.0})
                index += 1
            if not windows:
                return [], ["The audio track was empty; audio diagnostics were skipped."], []
            transcript, transcript_warnings = transcribe_local(temporary_path)
            return windows, warnings + transcript_warnings, transcript
    except (OSError, subprocess.SubprocessError, wave.Error):
        return [], ["The audio track could not be analyzed; audio diagnostics were skipped."], []
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def _speech_metrics(windows: list[dict[str, float]], duration: float, transcript: list[dict[str, Any]] | None = None) -> dict[str, float | int]:
    if not windows:
        return {"speech_ratio": 0.0, "pause_count": 0, "long_pause_count": 0, "pause_density": 0.0, "average_energy": 0.0, "energy_variance": 0.0, "words_per_minute": 0.0}
    speech_windows = [window for window in windows if window["speech"]]
    energies = [window["energy"] for window in windows]
    pauses = 0
    long_pauses = 0
    run = 0
    for window in windows:
        if not window["speech"]:
            run += 1
            if run == 1:
                pauses += 1
            if run * WINDOW_SECONDS >= LONG_PAUSE_SECONDS and (run - 1) * WINDOW_SECONDS < LONG_PAUSE_SECONDS:
                long_pauses += 1
        else:
            run = 0
    average = sum(energies) / len(energies)
    variance = sum((energy - average) ** 2 for energy in energies) / len(energies)
    speech_ratio = len(speech_windows) / len(windows)
    word_count = sum(len(segment.get("words", [])) for segment in (transcript or []))
    spoken_seconds = sum(max(0.0, float(segment.get("end", 0.0)) - float(segment.get("start", 0.0))) for segment in (transcript or []))
    words_per_minute = word_count / max(spoken_seconds / 60.0, 1 / 60.0)
    return {
        "speech_ratio": round(speech_ratio, 4),
        "pause_count": pauses,
        "long_pause_count": long_pauses,
        "pause_density": round(pauses / max(duration, WINDOW_SECONDS), 4),
        "average_energy": round(average, 5),
        "energy_variance": round(variance, 6),
        "words_per_minute": round(words_per_minute, 2),
    }


def analyze_multimodal(video_path: str | Path, result: AnalysisResult) -> dict[str, Any]:
    path = Path(video_path)
    audio_windows, warnings, transcript = _audio_windows(path, result.duration)
    speech_metrics = _speech_metrics(audio_windows, result.duration, transcript)
    transcription_available = bool(transcript)
    visual_by_timestamp = {round(sample.timestamp, 2): score for sample, score in zip(result.samples, result.motion_scores)}
    audio_by_timestamp = {round(window["timestamp"], 2): window for window in audio_windows}
    points: list[dict[str, Any]] = []
    remediation: list[dict[str, Any]] = []
    transcript_text = " ".join(segment["text"] for segment in transcript)
    text_embedding, image_embeddings, embedding_warnings = embed_text_and_frames(transcript_text, [sample.frame for sample in result.samples]) if transcript_text else (None, [], ["No transcript text is available; semantic drift is unavailable."])
    warnings.extend(embedding_warnings)
    embedding_available = text_embedding is not None and bool(image_embeddings)

    for index, (sample, motion_score) in enumerate(zip(result.samples, result.motion_scores)):
        timestamp = round(sample.timestamp, 2)
        semantic_drift = None
        if embedding_available and index < len(image_embeddings):
            semantic_similarity = sum(left * right for left, right in zip(text_embedding, image_embeddings[index]))
            semantic_drift = round(max(0.0, 1.0 - semantic_similarity), 4)
        audio = audio_by_timestamp.get(timestamp, {"energy": 0.0, "speech": 0.0})
        static_risk = 1.0 if any(segment.start <= sample.timestamp < segment.end for segment in result.static_segments) else 0.0
        pause_risk = 1.0 if not audio["speech"] else 0.0
        drift_risk = semantic_drift or 0.0
        risk_score = min(1.0, static_risk * 0.55 + pause_risk * 0.2 + drift_risk * 0.15 + max(0.0, 0.015 - motion_score) / 0.015 * 0.1)
        zone = _zone(risk_score)
        reasons = (["visual_monotony"] if static_risk else []) + (["long_pause_or_silence"] if pause_risk else []) + (["semantic_drift"] if drift_risk >= 0.5 else [])
        points.append({"timestamp": timestamp, "position": round((timestamp / result.duration * 100) if result.duration else 0.0, 3), "visual_motion": round(motion_score, 5), "audio_energy": audio["energy"], "semantic_drift": semantic_drift, "attention_risk": round(risk_score, 4), "zone": zone, "reasons": reasons})

    for index, segment in enumerate(result.static_segments):
        remediation.append({"id": f"visual-{index + 1}", "start": segment.start, "end": segment.end, "severity": "red", "category": "visual_monotony", "edit_type": "cut_or_b_roll", "title": "Break the static shot", "rationale": f"Visual motion stayed low for {segment.duration:.1f} seconds.", "instruction": "Cut to B-roll, add camera movement, or apply a purposeful punch-in zoom.", "priority": "high"})

    return {"analyzer_version": ANALYZER_VERSION, "mode": "multimodal", "capabilities": {"visual": True, "audio": bool(audio_windows), "transcription": transcription_available, "embeddings": embedding_available, "semantic_drift": embedding_available}, "warnings": warnings + ([] if transcription_available else ["Local Whisper is not installed or provisioned; transcript and word-level cadence are unavailable."]) + ([] if embedding_available else ["Local shared text/image embeddings are not installed or provisioned; semantic drift is unavailable."]), "transcript": transcript, "speech_metrics": speech_metrics, "timeline_zones": points, "remediation_actions": remediation}
