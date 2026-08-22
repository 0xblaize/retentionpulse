from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.concurrency import run_in_threadpool

from retentionpulse.local_models import model_readiness
from retentionpulse.service import analyze_video_json

from . import auth
from .schemas import AnalysisResponse


load_dotenv(Path(__file__).resolve().parents[2] / ".env")
MAX_UPLOAD_BYTES = int(os.getenv("RETENTIONPULSE_MAX_UPLOAD_BYTES", str(250 * 1024 * 1024)))
MAX_VIDEO_SECONDS = int(os.getenv("RETENTIONPULSE_MAX_VIDEO_SECONDS", "300"))
SUPPORTED_MODES = {"fast_preview", "visual", "multimodal", "auto"}

app = FastAPI(title="RetentionPulse API", version="2.0.0")
frontend_url = os.getenv("RETENTIONPULSE_FRONTEND_URL", "http://127.0.0.1:5173").rstrip("/")
allowed_origins = [origin.strip().rstrip("/") for origin in os.getenv("CORS_ALLOWED_ORIGINS", frontend_url).split(",") if origin.strip()]
app.add_middleware(SessionMiddleware, secret_key=os.getenv("RETENTIONPULSE_SECRET_KEY", "retentionpulse-local-secret-change-me"), same_site="none" if frontend_url.startswith("https://") else "lax", https_only=frontend_url.startswith("https://"))
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ---------------------------------------------------------------------------
# SQLite-backed job store — survives Render restarts / container recycles
# ---------------------------------------------------------------------------
_JOB_DB_PATH = Path(os.getenv("RETENTIONPULSE_DB_PATH", Path(__file__).resolve().parents[1] / "db.sqlite3"))


def _jobs_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_JOB_DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_job (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'queued',
                result TEXT,
                detail TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                duration REAL NOT NULL,
                health_score INTEGER NOT NULL,
                risk_seconds REAL NOT NULL,
                risk_ratio REAL NOT NULL,
                flagged_count INTEGER NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    except Exception:
        pass
    return conn


def _job_set(job_id: str, **fields: object) -> None:
    try:
        conn = _jobs_db()
        sets = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(f"UPDATE analysis_job SET {sets} WHERE job_id = ?", (*fields.values(), job_id))
        conn.commit()
        conn.close()
    except Exception:
        pass


def _job_get(job_id: str) -> sqlite3.Row | None:
    try:
        conn = _jobs_db()
        row = conn.execute("SELECT * FROM analysis_job WHERE job_id = ?", (job_id,)).fetchone()
        conn.close()
        return row
    except Exception:
        return None


def _job_create(job_id: str) -> None:
    try:
        conn = _jobs_db()
        conn.execute(
            "INSERT INTO analysis_job (job_id, status, created_at) VALUES (?, 'queued', ?)",
            (job_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _jobs_cleanup() -> None:
    """Delete jobs older than 1 hour to keep the DB small."""
    try:
        conn = _jobs_db()
        conn.execute(
            "DELETE FROM analysis_job WHERE created_at < datetime('now', '-1 hour')"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _history_save(
    history_id: str,
    filename: str,
    duration: float,
    health_score: int,
    risk_seconds: float,
    risk_ratio: float,
    flagged_count: int,
    result_json: str,
) -> None:
    try:
        conn = _jobs_db()
        conn.execute(
            """
            INSERT OR REPLACE INTO analysis_history
            (id, filename, duration, health_score, risk_seconds, risk_ratio, flagged_count, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                history_id,
                filename,
                duration,
                health_score,
                risk_seconds,
                risk_ratio,
                flagged_count,
                result_json,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _history_list() -> list[dict[str, object]]:
    try:
        conn = _jobs_db()
        rows = conn.execute(
            """
            SELECT id, filename, duration, health_score, risk_seconds, risk_ratio, flagged_count, created_at
            FROM analysis_history
            ORDER BY created_at DESC
            LIMIT 50
            """
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []


def _history_get(history_id: str) -> dict[str, object] | None:
    try:
        conn = _jobs_db()
        row = conn.execute(
            "SELECT * FROM analysis_history WHERE id = ?",
            (history_id,),
        ).fetchone()
        conn.close()
        if row is None:
            return None
        data = dict(row)
        data["result"] = json.loads(data["result"])
        return data
    except Exception:
        return None


def _history_delete(history_id: str) -> bool:
    try:
        conn = _jobs_db()
        cursor = conn.execute(
            "DELETE FROM analysis_history WHERE id = ?",
            (history_id,),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    except Exception:
        return False



def _extension(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def _analyze(path: str, mode: str = "auto") -> dict:
    return analyze_video_json(path, mode=mode)


async def _run_job(job_id: str, path: str, mode: str, filename: str = "Video") -> None:
    try:
        _job_set(job_id, status="processing")
        result = await run_in_threadpool(_analyze, path, mode)
        result_json = json.dumps(result)
        _job_set(job_id, status="complete", result=result_json)
        try:
            _history_save(
                history_id=job_id,
                filename=filename,
                duration=float(result.get("duration") or 0.0),
                health_score=int(result.get("health_score") or 0),
                risk_seconds=float(result.get("risk_seconds") or 0.0),
                risk_ratio=float(result.get("risk_ratio") or 0.0),
                flagged_count=len(result.get("segments") or []),
                result_json=result_json,
            )
        except Exception:
            pass
    except ValueError:
        _job_set(job_id, status="error", detail="This video could not be read. Try exporting it as a standard video file.")
    except Exception as exc:
        _job_set(job_id, status="error", detail=f"Analysis could not be completed for this video: {str(exc)[:160]}")
    finally:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        _jobs_cleanup()



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
    if video.content_type and not (video.content_type.startswith("video/") or video.content_type == "application/octet-stream"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a video file.")
    if mode not in SUPPORTED_MODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Analysis mode must be fast_preview, visual, multimodal, or auto.")

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
        try:
            payload = await asyncio.wait_for(run_in_threadpool(_analyze, temporary_path, mode), timeout=240)
        except asyncio.TimeoutError as error:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Analysis took too long. Try a shorter or smaller video.") from error
        return AnalysisResponse.model_validate(payload)
    except HTTPException:
        raise
    except ValueError as error:
        message = str(error)
        if message == "Video exceeds the five-minute limit":
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=message) from error
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="This video could not be read. Try exporting it as a standard video file.") from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Analysis could not be completed for this video. Try another file or a shorter export.") from error
    finally:
        await video.close()
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


@app.get("/api/auth/csrf/")
async def csrf(request: Request) -> JSONResponse:
    return await auth.csrf(request)


@app.get("/api/auth/session/")
async def auth_session(request: Request) -> dict[str, bool]:
    return auth.session(request)


@app.post("/api/auth/logout/")
async def auth_logout(request: Request) -> dict[str, bool]:
    auth.require_csrf(request)
    return auth.logout(request)


@app.post("/api/auth/access/")
async def auth_access(request: Request) -> JSONResponse:
    auth.require_csrf(request)
    return await auth.instant_access(request)



@app.post("/api/auth/passkey/register/options/")
async def passkey_register_options(request: Request) -> JSONResponse:
    auth.require_csrf(request)
    return await auth.register_options(request)


@app.post("/api/auth/passkey/register/verify/")
async def passkey_register_verify(request: Request) -> JSONResponse:
    auth.require_csrf(request)
    return await auth.register_verify(request)


@app.post("/api/auth/passkey/authenticate/options/")
async def passkey_auth_options(request: Request) -> JSONResponse:
    auth.require_csrf(request)
    return await auth.auth_options(request)


@app.post("/api/auth/passkey/authenticate/verify/")
async def passkey_auth_verify(request: Request) -> JSONResponse:
    auth.require_csrf(request)
    return await auth.auth_verify(request)


@app.post("/api/analyze/", response_model=AnalysisResponse)
async def protected_analyze(request: Request, video: UploadFile | None = File(None), mode: str = Form("auto")) -> AnalysisResponse:
    auth.require_auth(request)
    auth.require_csrf(request)
    if video is None:
        raise HTTPException(status_code=400, detail="Choose a video before scanning.")
    return await analyze(video, mode)


@app.post("/api/analyze/jobs/")
async def create_analysis_job(request: Request, video: UploadFile = File(...), mode: str = Form("auto")) -> dict[str, str]:
    auth.require_auth(request)
    auth.require_csrf(request)
    if mode not in SUPPORTED_MODES:
        raise HTTPException(status_code=400, detail="Analysis mode is invalid.")
    extension = _extension(video.filename)
    temporary_path: str | None = None
    total = 0
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temporary_file:
            temporary_path = temporary_file.name
            while chunk := await video.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="The video exceeds the upload limit.")
                temporary_file.write(chunk)
        job_id = uuid.uuid4().hex
        _job_create(job_id)
        original_filename = video.filename or "Uploaded Video"
        asyncio.create_task(_run_job(job_id, temporary_path, mode, filename=original_filename))
        temporary_path = None
        return {"jobId": job_id}
    finally:
        await video.close()
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


@app.get("/api/analyze/jobs/{job_id}")
async def analysis_job(request: Request, job_id: str) -> object:
    auth.require_auth(request)
    job = _job_get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job was not found or has expired.")
    if job["status"] == "error":
        raise HTTPException(status_code=422, detail=job["detail"])
    if job["status"] != "complete":
        return {"status": job["status"]}
    return {"status": "complete", "result": AnalysisResponse.model_validate(json.loads(job["result"])).model_dump()}


@app.get("/api/history/")
async def get_history(request: Request) -> list[dict[str, object]]:
    auth.require_auth(request)
    return _history_list()


@app.get("/api/history/{history_id}")
async def get_history_item(request: Request, history_id: str) -> dict[str, object]:
    auth.require_auth(request)
    item = _history_get(history_id)
    if item is None:
        raise HTTPException(status_code=404, detail="History item not found.")
    return item


@app.delete("/api/history/{history_id}")
async def delete_history_item(request: Request, history_id: str) -> dict[str, bool]:
    auth.require_auth(request)
    auth.require_csrf(request)
    deleted = _history_delete(history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History item not found.")
    return {"deleted": True}

