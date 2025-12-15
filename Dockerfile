# syntax=docker/dockerfile:1
ARG BASE_IMAGE=nvcr.io/nvidia/pytorch:24.03-py3
FROM ${BASE_IMAGE}
ARG INSTALL_TRITON_STUB=0

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

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        ffmpeg \
        libsndfile1 \
        ninja-build \
        python3-dev \
        python3-venv \
        python3-wheel \
        sox \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv ${VENV_PATH} \
    && ${VENV_PATH}/bin/pip install --upgrade pip \
    && ${VENV_PATH}/bin/pip install --no-cache-dir "Cython<3" \
    && ${VENV_PATH}/bin/pip install --no-cache-dir --no-build-isolation \
        --extra-index-url https://pypi.ngc.nvidia.com \
        youtokentome==1.0.6 \
    && if [ "${INSTALL_TRITON_STUB}" = "1" ]; then \
           ${VENV_PATH}/bin/pip install ./vendor/triton_stub; \
       fi \
    && ${VENV_PATH}/bin/pip install --no-cache-dir \
        --extra-index-url https://pypi.ngc.nvidia.com \
        -r requirements.txt

COPY runparakeet ./runparakeet
COPY run.sh README.md ./

RUN chmod +x run.sh

ENV PATH="${VENV_PATH}/bin:${PATH}"

EXPOSE 8000

ENTRYPOINT ["./run.sh"]
