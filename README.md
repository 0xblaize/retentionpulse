# RetentionPulse AI

RetentionPulse is a cinematic video-retention review tool. It scans an uploaded edit for visual dead air: shots with very little frame-to-frame change for longer than six seconds.

## Architecture

- **React + Vite** provides the primary responsive landing experience and frontend entry point.
- **Django** remains the Python browser/API layer for passkeys, sessions, CSRF, dashboard access, and upload proxying.
- **FastAPI** runs CPU-heavy OpenCV analysis in a worker thread.
- **Streamlit** remains available as a fallback demo in `app.py`.

## Run the app locally

Install Python dependencies:

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

Start the FastAPI analysis service:

```bash
uvicorn retentionpulse_api.main:app --host 127.0.0.1 --port 8001
```

Start Django in another terminal:

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Start the React frontend in a third terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173/` for the React landing page. Vite proxies `/api`, `/login`, and `/dashboard` to Django on port 8000. FastAPI is available at `http://127.0.0.1:8001`.

## Passkeys

Django owns passkey registration and authentication. The first workspace device can select **Register this device** on `/login/`; later visits use **Continue with passkey**. The server verifies the WebAuthn challenge, relying-party ID, origin, signature, user verification, and signature counter before creating a Django session.

Local development uses `http://127.0.0.1:8000` and RP ID `127.0.0.1`. For deployment, set:

```text
RETENTIONPULSE_RP_ID=your-domain.example
RETENTIONPULSE_ORIGIN=https://your-domain.example
RETENTIONPULSE_RP_NAME=RetentionPulse
```

Production passkeys require HTTPS.

## FastAPI endpoints

- `GET /health`
- `POST /analyze` with a multipart `video` field

FastAPI accepts MP4, MOV, and M4V files up to 250 MB by default. Uploaded files are written to a temporary path, analyzed, and deleted in a `finally` block.

## Detection assumptions

- Frames are sampled every 0.5 seconds.
- Frames are resized and converted to grayscale before comparison.
- A normalized mean absolute pixel difference of `0.015` or lower is considered low motion.
- A low-motion run must be longer than 6 seconds to be flagged.
- Results are visual review signals, not a guarantee of audience drop-off.

## Tests

```bash
python -m pytest -q
python manage.py check
cd frontend && npm run build
```

The analyzer is deterministic and does not require an LLM, transcript, database, or external AI API.
