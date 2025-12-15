from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from .config import Settings
from .model_manager import ParakeetModelManager

LOGGER = logging.getLogger("runparakeet.app")


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        title=settings.landing_title,
        description=settings.landing_tagline,
        version="1.0.0",
    )
    manager = ParakeetModelManager(
        model_name=settings.model_name, idle_unload_seconds=settings.idle_unload_seconds
    )
    app.state.settings = settings
    app.state.manager = manager

    @app.get("/", response_class=HTMLResponse)
    async def landing_page() -> str:
        status = manager.get_status()
        return _landing_page_html(settings, status)

    @app.get("/healthz")
    async def healthcheck() -> dict:
        return {"status": "ok", **manager.get_status()}

    @app.get("/v1/models")
    async def list_models() -> dict:
        status = manager.get_status()
        last_loaded = status.get("last_loaded")
        created_ts = 0
        if last_loaded:
            try:
                created_ts = int(datetime.fromisoformat(last_loaded).timestamp())
            except ValueError:
                created_ts = 0
        return {
            "object": "list",
            "data": [
                {
                    "id": settings.model_name,
                    "object": "model",
                    "owned_by": "nvidia",
                    "created": created_ts,
                    "permission": [],
                }
            ],
        }

    @app.post("/v1/audio/transcriptions")
    async def transcribe_audio(
        file: UploadFile = File(...),
        model: str = Form(default=settings.model_name),
        prompt: Optional[str] = Form(default=None),
        response_format: str = Form(default="json"),
        temperature: float = Form(default=0.0),
        language: Optional[str] = Form(default=None),
    ):
        if model != settings.model_name:
            raise HTTPException(status_code=404, detail=f"Unknown model '{model}'")
        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="Empty audio payload")
        LOGGER.info(
            "Transcribing %s (%s bytes, language=%s, temperature=%s)",
            file.filename,
            len(payload),
            language,
            temperature,
        )
        text = await manager.transcribe(
            audio_bytes=payload,
            filename=file.filename or "audio.wav",
            language=language,
            prompt=prompt,
        )
        return _format_transcription_response(
            text=text,
            response_format=response_format,
            settings=settings,
            language=language,
        )

    @app.on_event("shutdown")
    async def _shutdown_event() -> None:
        await manager.unload()

    return app


def _format_transcription_response(
    *,
    text: str,
    response_format: str,
    settings: Settings,
    language: Optional[str],
):
    created = int(datetime.now(timezone.utc).timestamp())
    base = {
        "text": text,
        "model": settings.model_name,
        "language": language or "unknown",
        "created": created,
    }
    fmt = response_format.lower()
    if fmt in {"json", "json_object"}:
        return JSONResponse(base)
    if fmt == "verbose_json":
        verbose = {
            **base,
            "duration": None,
            "segments": [
                {
                    "id": 0,
                    "seek": 0,
                    "start": 0.0,
                    "end": 0.0,
                    "text": text,
                    "tokens": [],
                    "temperature": 0.0,
                    "avg_logprob": 0.0,
                    "compression_ratio": 0.0,
                    "no_speech_prob": 0.0,
                }
            ],
        }
        return JSONResponse(verbose)
    if fmt == "text":
        return PlainTextResponse(text)
    if fmt == "srt":
        body = "1\n00:00:00,000 --> 00:00:00,000\n" + text + "\n"
        return PlainTextResponse(body, media_type="application/x-subrip")
    if fmt == "vtt":
        body = "WEBVTT\n\n00:00:00.000 --> 00:00:00.000\n" + text + "\n"
        return PlainTextResponse(body, media_type="text/vtt")
    raise HTTPException(status_code=400, detail=f"Unsupported response_format '{response_format}'")


def _landing_page_html(settings: Settings, status: dict) -> str:
    idle = status.get("idle_unload_seconds")
    loaded_state = "Loaded" if status.get("loaded") else "Not loaded"
    last_loaded = status.get("last_loaded") or "Never"
    endpoint = f"http://localhost:{settings.port}/v1/audio/transcriptions"
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{settings.landing_title}</title>
  <style>
    body {{
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0b1b2b;
      color: #f1f5f9;
      margin: 0;
      padding: 2rem;
      line-height: 1.6;
    }}
    .card {{
      max-width: 800px;
      margin: 0 auto;
      padding: 2rem;
      background: rgba(255, 255, 255, 0.04);
      border-radius: 16px;
      backdrop-filter: blur(4px);
      box-shadow: 0 30px 40px rgba(0, 0, 0, 0.2);
    }}
    h1 {{
      margin-top: 0;
      font-size: 2.25rem;
    }}
    code {{
      background: rgba(15, 118, 110, 0.2);
      padding: 0.2rem 0.4rem;
      border-radius: 6px;
      font-size: 0.95rem;
    }}
    section {{
      margin-top: 1.5rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
    }}
    .pill {{
      background: rgba(71, 85, 105, 0.4);
      padding: 0.5rem 0.75rem;
      border-radius: 999px;
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>{settings.landing_title}</h1>
    <p>{settings.landing_tagline}</p>

    <section>
      <h2>Status</h2>
      <div class=\"grid\">
        <div class=\"pill\">Model: <strong>{settings.model_name}</strong></div>
        <div class=\"pill\">State: <strong>{loaded_state}</strong></div>
        <div class=\"pill\">Idle unload: <strong>{idle}s</strong></div>
        <div class=\"pill\">Last loaded: <strong>{last_loaded}</strong></div>
      </div>
    </section>

    <section>
      <h2>OpenAI compatible endpoints</h2>
      <p>
        <code>GET /v1/models</code>
        lists the available Parakeet model.
      </p>
      <p>
        <code>POST /v1/audio/transcriptions</code>
        accepts the same multipart payload as the OpenAI API.
      </p>
      <ol>
        <li>Send a multipart request with your file as <code>file</code>.</li>
        <li>Set <code>model</code> to <code>{settings.model_name}</code>.</li>
        <li>Optionally include <code>response_format</code> or <code>language</code>.</li>
      </ol>
    </section>

    <section>
      <h2>Sample curl</h2>
      <pre><code>curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "model={settings.model_name}" \
  -F "response_format=json" \
  -F "file=@example.wav" \
  {endpoint}</code></pre>
    </section>
  </div>
</body>
</html>
"""
