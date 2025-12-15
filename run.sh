#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-${RUNPARAKEET_HOST:-0.0.0.0}}"
PORT="${PORT:-${RUNPARAKEET_PORT:-8000}}"
MODEL="${MODEL:-${RUNPARAKEET_MODEL:-nvidia/parakeet-tdt-0.6b-v3}}"
IDLE_UNLOAD_SECONDS="${IDLE_UNLOAD_SECONDS:-${RUNPARAKEET_IDLE_UNLOAD_SECONDS:-300}}"
LOG_LEVEL="${LOG_LEVEL:-${RUNPARAKEET_LOG_LEVEL:-info}}"
LANDING_TITLE="${LANDING_TITLE:-${RUNPARAKEET_LANDING_TITLE:-RunParakeet}}"
LANDING_TAGLINE="${LANDING_TAGLINE:-${RUNPARAKEET_LANDING_TAGLINE:-OpenAI compatible transcription server powered by NVIDIA Parakeet}}"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PY_BIN="$PYTHON_BIN"
elif [[ -x ".venv/bin/python" ]]; then
  PY_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY_BIN="$(command -v python3)"
else
  PY_BIN="$(command -v python)"
fi

exec "$PY_BIN" -m runparakeet \
  --host "$HOST" \
  --port "$PORT" \
  --model "$MODEL" \
  --idle-unload-seconds "$IDLE_UNLOAD_SECONDS" \
  --log-level "$LOG_LEVEL" \
  --landing-title "$LANDING_TITLE" \
  --landing-tagline "$LANDING_TAGLINE" \
  "$@"
