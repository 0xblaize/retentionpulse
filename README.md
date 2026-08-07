# RetentionPulse AI

> **Find the seconds that lose people.**
>
> RetentionPulse AI is an offline-first video-retention diagnostic tool for creators, editors, and production teams. Upload an edit, inspect its visual rhythm and audio pacing, identify moments where attention is likely to weaken, and export a structured repair manifest that an editor can act on immediately.

[![Status](https://img.shields.io/badge/status-hackathon%20build-5E0ED7)](#status)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB)](#architecture)
[![Backend](https://img.shields.io/badge/backend-Django%20%2B%20FastAPI-0C4B33)](#architecture)
[![Analysis](https://img.shields.io/badge/analysis-offline--first-111111)](#how-it-works)

## The problem

A video can be technically polished and still lose its audience in a few invisible seconds:

- a talking-head shot stays unchanged for too long;
- a sentence pauses while the image does nothing;
- the narration moves to a new idea but the visual support does not;
- the opening takes too long to establish momentum.

Traditional editing review often catches these issues only after someone watches the entire cut manually. RetentionPulse turns that review into a fast, explainable diagnostic pass.

## A practical example

Imagine a creator has edited a 45-second video explaining why modern servers need better cooling.

At the 12-second mark, the narration says **“high-density server hardware generates intense heat”**, but the video remains on the same wide talking-head shot for eight seconds. The voice continues, the frame barely changes, and the visual does not reinforce the idea being discussed.

RetentionPulse reports:

```text
12.0s ───────────────────────────────────────────── 20.0s
       RED: visual monotony + semantic drift
```

The dashboard makes the problem obvious with a red heatmap zone. The diagnostic payload records the timestamp, attention risk, motion level, semantic drift, and source reasons. The deterministic repair manifest recommends actions such as:

```json
{
  "start": 12.0,
  "end": 20.0,
  "category": "visual_monotony",
  "edit_type": "cut_or_b_roll",
  "instruction": "Cut to B-roll, add camera movement, or apply a purposeful punch-in zoom."
}
```

An optional Groq-powered advisor can then turn those facts into a short editor-facing plan, for example:

```text
1. Add server-rack B-roll at 12.0s to support the cooling explanation.
2. Use a 1.15x punch-in by 15.0s to break the static talking-head frame.
3. Trim the pause beginning at 18.0s or cover it with a visual beat.
```

The important design decision is that the written plan is optional. If the LLM is unavailable, the deterministic findings and JSON repair manifest still work.

## Why it is different

RetentionPulse is not a generic “paste your script into an AI” application. It combines measurable signals from the actual edit:

- **Visual rhythm:** frame differencing identifies static shots and low-motion runs.
- **Audio pacing:** FFmpeg extraction supports silence, pause, energy, and cadence metrics.
- **Local speech recognition:** optional faster-whisper produces transcript segments and word timestamps.
- **Shared multimodal alignment:** optional SigLIP text and image encoders compare narration and visual context in one compatible embedding space.
- **Explainable output:** every flagged zone carries timestamps, severity, risk, and reasons.
- **Editor-ready remediation:** findings become stable JSON actions rather than an unstructured score.
- **Graceful degradation:** missing models, FFmpeg, or LLM access never erase the deterministic visual result.

## How it works

```text
                 RAW VIDEO
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   Audio analysis             Frame analysis
   FFmpeg → WAV               OpenCV → 0.5s samples
        │                         │
        ▼                         ▼
   Whisper transcript          Motion / static-shot signals
        │                         │
        └────────────┬────────────┘
                     ▼
          Multimodal diagnostic layer
      speech metrics + semantic alignment
                     │
                     ▼
        Green / yellow / red heatmap zones
                     │
                     ▼
        Deterministic JSON repair manifest
                     │
                     ▼
          Optional Groq written repair plan
```

### Important embedding detail

For direct narration-to-frame comparison, RetentionPulse uses the text and image encoders from the same SigLIP-compatible model family. BGE Large EN may be useful for text-only topic analysis, but BGE vectors are not compared directly with SigLIP image vectors because they do not share a trained vector space.

## What the dashboard shows

The React dashboard is designed for a fast live demonstration:

1. Select or drag in a video.
2. Preview the actual uploaded edit in the browser.
3. Start the scan and see truthful upload/analysis status.
4. Read the health score and risk time.
5. See the green/yellow/red retention heatmap immediately.
6. Hover or keyboard-focus a zone to inspect its timestamp, risk, and reasons.
7. Open the table view for the complete timeline.
8. Review flagged segments and repair suggestions.
9. Download the remediation JSON for an editor or automation pipeline.

The visualization uses text labels and status markers in addition to color, with keyboard focus states, a table fallback, and reduced-motion support.

## Architecture

- **React + Vite** — responsive landing page and authenticated analysis dashboard.
- **Django** — passkeys, sessions, CSRF protection, dashboard access, and upload proxying.
- **FastAPI** — video validation, temporary-file lifecycle, and CPU-heavy analysis in a worker thread.
- **OpenCV + NumPy** — deterministic frame sampling and motion analysis.
- **FFmpeg** — optional audio extraction and normalized mono 16 kHz WAV generation.
- **faster-whisper** — optional local transcription with segment and word timestamps.
- **SigLIP-compatible Transformers model** — optional shared text/image semantic alignment.
- **Groq** — optional written repair-plan advisor using an OpenAI-compatible chat endpoint.
- **Streamlit** — fallback demo surface in `backend/app.py`.

## Quickstart

### 1. Install Python dependencies

From the repository root:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install the core backend:

```bash
pip install -r backend/requirements.txt
```

Optional local multimodal dependencies:

```bash
pip install -r backend/requirements-multimodal.txt
```

Install the frontend:

```bash
cd frontend
npm install
cd ..
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and adjust the values for your machine.

For the deterministic visual analyzer, no model weights or API key are required.

For local Whisper and embedding analysis, set paths to model directories that already exist locally:

```text
RETENTIONPULSE_WHISPER_MODEL=C:\models\whisper-large-v3-turbo
RETENTIONPULSE_EMBEDDING_MODEL=C:\models\siglip-so400m
```

For the optional Groq repair plan:

```text
RETENTIONPULSE_LLM_API_URL=https://api.groq.com/openai/v1/chat/completions
RETENTIONPULSE_LLM_API_KEY=your-groq-api-key
RETENTIONPULSE_LLM_MODEL=llama-3.3-70b-versatile
```

Keep the API key server-side. Never place it in React source code or expose it through a frontend environment variable.

### 3. Start the services

Terminal 1 — FastAPI analysis service:

```bash
cd backend
uvicorn retentionpulse_api.main:app --host 127.0.0.1 --port 8001
```

Terminal 2 — Django browser/API layer:

```bash
cd backend
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Terminal 3 — React frontend:

```bash
cd frontend
npm run dev
```

Open:

- React landing page: `http://127.0.0.1:5173/`
- Django login/dashboard: `http://127.0.0.1:8000/`
- FastAPI health: `http://127.0.0.1:8001/health`
- FastAPI multimodal readiness: `http://127.0.0.1:8001/health/multimodal`

## Offline and fallback behavior

The core analyzer does not need an LLM. It calculates deterministic visual and, when available, audio/multimodal diagnostics locally.

The optional written repair-plan advisor uses Groq when a valid `RETENTIONPULSE_LLM_API_KEY` is configured. If the key is missing, the endpoint is unreachable, the response is malformed, or the request fails, RetentionPulse still returns:

- health score;
- risk ratio and risk duration;
- timeline zones;
- flagged segments;
- speech metrics when available;
- deterministic remediation actions;
- downloadable JSON.

This separation keeps the live demo useful even when a network service or model is unavailable.

## API

### `GET /health`

Basic process health check:

```json
{"status":"ok"}
```

### `GET /health/multimodal`

Reports available local capabilities, including FFmpeg, transcription, and embeddings.

### `POST /analyze`

Submit a multipart video upload:

```bash
curl -X POST http://127.0.0.1:8001/analyze \
  -F "video=@sample.mp4" \
  -F "mode=auto"
```

Supported extensions:

- `.mp4`
- `.mov`
- `.m4v`

The default upload limit is 250 MB. Uploaded files are written to a temporary path and deleted in a `finally` block after analysis.

The response includes legacy fields plus the structured diagnostic fields:

```json
{
  "duration": 45.0,
  "risk_seconds": 8.0,
  "risk_ratio": 0.178,
  "health_score": 82,
  "timeline_zones": [],
  "segments": [],
  "suggestions": [],
  "remediation_actions": [],
  "ai_repair_plan": null
}
```

## Render deployment

`render.yaml` provisions separate Docker services:

- `retentionpulse-api` includes FFmpeg and optional multimodal dependencies;
- `retentionpulse-django` stays lightweight and handles browser/session traffic;
- the API receives a persistent `/app/model-cache` disk;
- the frontend remains deployable separately, such as through Vercel.

On Render, set the following environment variables in the appropriate service:

```text
RETENTIONPULSE_OFFLINE_MODE=1
RETENTIONPULSE_FFMPEG=ffmpeg
RETENTIONPULSE_MODEL_CACHE=/app/model-cache
RETENTIONPULSE_WHISPER_MODEL=/app/model-cache/whisper-large-v3-turbo
RETENTIONPULSE_EMBEDDING_MODEL=/app/model-cache/siglip-so400m
```

Provision the model directories before expecting transcription or semantic alignment. If they are absent, the API reports capability warnings and safely falls back to the available diagnostics.

For a Groq repair plan on Render, configure the API service with:

```text
RETENTIONPULSE_LLM_API_URL=https://api.groq.com/openai/v1/chat/completions
RETENTIONPULSE_LLM_API_KEY=your-groq-api-key
RETENTIONPULSE_LLM_MODEL=llama-3.3-70b-versatile
```

Do not commit `.env`, API keys, or model weights.

## Passkeys and security

Django owns passkey registration and authentication. The first workspace device can select **Register this device** on `/login/`; later visits use **Continue with passkey**. The server verifies the WebAuthn challenge, relying-party ID, origin, signature, user verification, and signature counter before creating a Django session.

Local development uses:

```text
RETENTIONPULSE_RP_ID=127.0.0.1
RETENTIONPULSE_ORIGIN=http://127.0.0.1:8000
RETENTIONPULSE_RP_NAME=RetentionPulse
```

Production passkeys require HTTPS. For deployment, use the production hostname for both `RETENTIONPULSE_RP_ID` and `RETENTIONPULSE_ORIGIN`.

## Detection assumptions and limitations

- Frames are sampled every 0.5 seconds.
- Visual motion uses resized grayscale frame differences.
- A normalized mean absolute pixel difference of `0.015` or lower is considered low motion.
- A low-motion run must be longer than six seconds to become a visual monotony segment.
- Timeline timestamps reflect the sampling grid; they are not millisecond-accurate measurements.
- Semantic drift depends on local model availability and checkpoint quality.
- Attention risk is an explainable diagnostic signal, not a guarantee of audience behavior or algorithmic distribution.
- The system does not automatically edit or re-encode the source video yet; it exports actions for an editor or downstream automation.

## Testing

Backend tests:

```bash
cd backend
python -m pytest -q
python manage.py check
python -m compileall -q retentionpulse retentionpulse_api tests
```

Frontend production build:

```bash
cd frontend
npm run build
```

The test suite covers deterministic analysis, multimodal fallback behavior, LLM provider failures, prompt evidence, API validation, and Django integration behavior.

## Project status

RetentionPulse is a working hackathon build focused on a reliable diagnostic loop:

- deterministic visual analysis is available without an LLM;
- optional audio and shared multimodal analysis are capability-aware;
- optional Groq repair-plan generation is isolated from the scoring path;
- the dashboard presents a video preview, retention heatmap, diagnostics, and JSON export;
- Render configuration separates the heavy analysis service from the Django web layer.

The next product step is downstream edit execution: turning remediation actions into editor integrations or carefully controlled FFmpeg operations.
