# syntax=docker/dockerfile:1
ARG BASE_IMAGE=nvcr.io/nvidia/pytorch:24.03-py3
FROM ${BASE_IMAGE}
ARG INSTALL_TRITON_STUB=0
ARG TORCH_EXTRA_INDEX_URL=
ARG CUDA_PYTHON_VERSION=12.6

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

COPY vendor ./vendor
COPY requirements.txt ./

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ffmpeg \
        libsndfile1 \
        ninja-build \
        python3-dev \
        python3-venv \
        python3-wheel \
        sox; \
    rm -rf /var/lib/apt/lists/*; \
    python3 -m venv "${VENV_PATH}"; \
    PIP_BIN="${VENV_PATH}/bin/pip"; \
    "${PIP_BIN}" install --upgrade pip; \
    if [ -n "${TORCH_EXTRA_INDEX_URL}" ]; then \
        TORCH_INDEX_FLAGS="--extra-index-url ${TORCH_EXTRA_INDEX_URL}"; \
    else \
        TORCH_INDEX_FLAGS=""; \
    fi; \
    "${PIP_BIN}" install --no-cache-dir ${TORCH_INDEX_FLAGS} torch torchvision; \
    "${PIP_BIN}" install --no-cache-dir ${TORCH_INDEX_FLAGS} "cuda-python==${CUDA_PYTHON_VERSION}"; \
    if [ "${INSTALL_TRITON_STUB}" = "1" ]; then \
        "${PIP_BIN}" install ./vendor/triton_stub; \
    fi; \
    "${PIP_BIN}" install --no-cache-dir \
        --extra-index-url https://pypi.ngc.nvidia.com \
        -r requirements.txt

COPY runparakeet ./runparakeet
COPY run.sh README.md ./

RUN chmod +x run.sh

ENV PATH="${VENV_PATH}/bin:${PATH}"

EXPOSE 8000

ENTRYPOINT ["./run.sh"]
