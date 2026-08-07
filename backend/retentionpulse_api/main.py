from __future__ import annotations

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from retentionpulse.local_models import model_readiness
from retentionpulse.service import analyze_video_json

from .schemas import AnalysisResponse


load_dotenv(Path(__file__).resolve().parents[2] / ".env")
MAX_UPLOAD_BYTES = int(os.getenv("RETENTIONPULSE_MAX_UPLOAD_BYTES", str(250 * 1024 * 1024)))
SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".m4v"}
SUPPORTED_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-m4v", "application/octet-stream"}

app = FastAPI(title="RetentionPulse Analysis API", version="1.0.0")


def _extension(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def _analyze(path: str, mode: str = "auto") -> dict:
    return analyze_video_json(path, mode=mode)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/multimodal")
def multimodal_health() -> dict[str, object]:
    import shutil

    readiness = model_readiness()
    return {
        "status": "ok",
        "visual": True,
        "audio": shutil.which(os.getenv("RETENTIONPULSE_FFMPEG", "ffmpeg")) is not None,
        **readiness,
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(video: UploadFile = File(...), mode: str = Form("auto")) -> AnalysisResponse:
    extension = _extension(video.filename)
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supported video types are MP4, MOV, and M4V.")
    if video.content_type and video.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is not a supported video type.")

    temporary_path: str | None = None
    total = 0
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temporary_file:
            temporary_path = temporary_file.name
            while chunk := await video.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="The video exceeds the upload limit.")
                temporary_file.write(chunk)
        if mode not in {"visual", "multimodal", "auto"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Analysis mode must be visual, multimodal, or auto.")
        payload = await run_in_threadpool(_analyze, temporary_path, mode)
        return AnalysisResponse.model_validate(payload)
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    finally:
        await video.close()
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
