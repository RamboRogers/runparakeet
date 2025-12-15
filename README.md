# RUNPARAKEET

RunParakeet is an OpenAI `/v1` compatible transcription server that wraps the
[nvidia/parakeet-tdt-0.6b-v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)
ASR model. It exposes the standard `/v1/models` and `/v1/audio/transcriptions`
routes, adds a simple landing page with container details, and automatically
unloads the model when it sits idle (defaults to five minutes).

Target is Jetson Thor, but it should work on any NVIDIA GPU system with the NeMo
toolkit available.

## Features

- ✅ OpenAI compatible `/v1/models` + `/v1/audio/transcriptions`
- 🚀 Automatic lazy loading + configurable idle based unloading
- 🧠 Hugging Face Parakeet (`nvidia/parakeet-tdt-0.6b-v3`) behind the scenes
- 🧾 Landing page with health/status and sample usage

## Requirements

- Python 3.9+
- NVIDIA GPU with CUDA + drivers that satisfy NeMo requirements
- [NeMo Toolkit](https://github.com/NVIDIA/NeMo) (`pip install -r requirements.txt`)

## Installation

Create a local virtual environment named `.venv` (the provided run script will
pick it up automatically) and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Running the service

Use the convenience script to start the server. It will automatically prefer
`.venv/bin/python` (or anything pointed to by `PYTHON_BIN`) so you do not have
to activate the environment manually. Options can be supplied via environment
variables or CLI flags.

```bash
# default host=0.0.0.0, port=8000, idle unload after 300s
./run.sh

# override host/port/idle timeout
HOST=0.0.0.0 PORT=9000 IDLE_UNLOAD_SECONDS=60 ./run.sh

# pass extra flags through to python -m runparakeet (e.g. enable reload)
./run.sh --reload
```

Important environment variables (all optional):

| Variable | Description | Default |
| --- | --- | --- |
| `HOST` / `RUNPARAKEET_HOST` | Bind address for uvicorn | `0.0.0.0` |
| `PORT` / `RUNPARAKEET_PORT` | Port for uvicorn | `8000` |
| `MODEL` / `RUNPARAKEET_MODEL` | Model identifier | `nvidia/parakeet-tdt-0.6b-v3` |
| `IDLE_UNLOAD_SECONDS` / `RUNPARAKEET_IDLE_UNLOAD_SECONDS` | Seconds of inactivity before releasing GPU memory (`0` disables unloading) | `300` |
| `PYTHON_BIN` | Override interpreter path used by `run.sh` | auto-detect `.venv/bin/python` |

## Docker / NVIDIA runtime

You can containerize the service with the included `Dockerfile`. It defaults to
the x86 `nvcr.io/nvidia/pytorch:24.03-py3` base image but can be overridden for
Jetson Thor (L4T) builds. Make sure the
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
is installed on the host.

```bash
# x86_64 build (CUDA capable dGPU)
docker build -t runparakeet:latest .

# Jetson Thor / L4T base
docker build \
  --build-arg BASE_IMAGE=nvcr.io/nvidia/l4t-pytorch:r35.4.1-py3 \
  -t runparakeet:thor .
```

Run the container with the NVIDIA Container Runtime so the Parakeet model can
access the GPU:

```bash
# dGPU hosts
docker run --rm -p 8000:8000 --gpus all runparakeet:latest

# Jetson (runtime flag is still required)
docker run --rm -p 8000:8000 --runtime nvidia runparakeet:thor
```

The server listens on port `8000` inside the container and exposes the same
environment variables described above. Customize them with `-e VAR=value` as
needed (e.g., to change the unload timeout or landing page copy).

## API reference

- `GET /` — Landing page with status and usage instructions
- `GET /healthz` — Simple health/status report
- `GET /v1/models` — OpenAI compatible model response
- `POST /v1/audio/transcriptions` — Multipart upload compatible with the OpenAI client/SDKs

Example transcription request:

```bash
curl -s -X POST http://localhost:8000/v1/audio/transcriptions \
  -H "Authorization: Bearer test-token" \
  -F "model=nvidia/parakeet-tdt-0.6b-v3" \
  -F "file=@sample.wav" \
  -F "response_format=json"
```

## Programmatic usage

```python
import nemo.collections.asr as nemo_asr

asr_model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v3")
transcriptions = asr_model.transcribe(["file.wav"])
print(transcriptions[0])
```

The FastAPI server uses the same approach internally and unloads the model after
the configured idle timeout so GPU memory can be reclaimed automatically.


## ⚖️ License

<p>
GPU GPLv3 Licensed.<p><i> (c)Matthew Rogers 2025. All rights reserved. No Warranty. No Support. No Liability. No Refunds.</p<br>
</i><p>
<em>Free Software</em>
</p>

### Connect With Me 🤝

[![GitHub](https://img.shields.io/badge/GitHub-matthewrogers-181717?style=for-the-badge&logo=github)](https://github.com/matthewrogers)
[![Twitter](https://img.shields.io/badge/Twitter-@matthewrogers-1DA1F2?style=for-the-badge&logo=twitter)](https://x.com/matthewrogers)
[![Website](https://img.shields.io/badge/Web-matthewrogers.org-00ADD8?style=for-the-badge&logo=google-chrome)](https://matthewrogers.org)

![Matthew Rogers](https://github.com/RamboRogers/cyberpamnow/raw/master/media/ramborogers.png)

</div>