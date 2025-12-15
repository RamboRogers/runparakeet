# syntax=docker/dockerfile:1
ARG BASE_IMAGE=nvcr.io/nvidia/pytorch:24.03-py3
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VENV_PATH=/opt/runparakeet/.venv \
    RUNPARAKEET_HOST=0.0.0.0 \
    RUNPARAKEET_PORT=8000 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

WORKDIR /app

COPY requirements.txt ./

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        sox \
        libsndfile1 \
        python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv ${VENV_PATH} \
    && ${VENV_PATH}/bin/pip install --upgrade pip \
    && ${VENV_PATH}/bin/pip install --no-cache-dir \
        --extra-index-url https://pypi.ngc.nvidia.com \
        -r requirements.txt

COPY runparakeet ./runparakeet
COPY run.sh README.md ./

RUN chmod +x run.sh

ENV PATH="${VENV_PATH}/bin:${PATH}"

EXPOSE 8000

ENTRYPOINT ["./run.sh"]
