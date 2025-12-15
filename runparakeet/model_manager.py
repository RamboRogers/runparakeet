from __future__ import annotations

import asyncio
import contextlib
import gc
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional


LOGGER = logging.getLogger("runparakeet.model_manager")


class ParakeetModelManager:
    """Lazy loader that keeps the Parakeet model alive while it is in use."""

    def __init__(self, model_name: str, idle_unload_seconds: int = 300) -> None:
        self.model_name = model_name
        self.idle_unload_seconds = idle_unload_seconds
        self._model = None
        self._load_lock = asyncio.Lock()
        self._unload_task: Optional[asyncio.Task] = None
        self._last_loaded: Optional[datetime] = None

    async def ensure_loaded(self):
        """Load the model if needed and reschedule auto unload."""

        if self._model is None:
            async with self._load_lock:
                if self._model is None:
                    loop = asyncio.get_running_loop()
                    LOGGER.info("Loading Parakeet model %s", self.model_name)
                    self._model = await loop.run_in_executor(None, self._load_model)
                    self._last_loaded = datetime.now(timezone.utc)
        self._schedule_auto_unload()
        return self._model

    async def unload(self) -> None:
        """Explicitly dispose the currently loaded model."""

        if self._unload_task and not self._unload_task.done():
            self._unload_task.cancel()
        async with self._load_lock:
            if self._model is None:
                return
            model = self._model
            self._model = None
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._dispose_model, model)

    def _schedule_auto_unload(self) -> None:
        if self.idle_unload_seconds <= 0:
            return
        if self._unload_task and not self._unload_task.done():
            self._unload_task.cancel()
        self._unload_task = asyncio.create_task(self._auto_unload())

    async def _auto_unload(self) -> None:
        try:
            await asyncio.sleep(self.idle_unload_seconds)
            LOGGER.info(
                "Model idle for %s seconds. Releasing GPU memory.",
                self.idle_unload_seconds,
            )
            await self.unload()
        except asyncio.CancelledError:
            return

    def get_status(self) -> dict:
        return {
            "model_name": self.model_name,
            "loaded": self._model is not None,
            "idle_unload_seconds": self.idle_unload_seconds,
            "last_loaded": self._last_loaded.isoformat() if self._last_loaded else None,
        }

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> str:
        model = await self.ensure_loaded()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._transcribe_blocking,
            model,
            audio_bytes,
            filename,
            language,
            prompt,
        )

    def _load_model(self):
        try:
            import nemo.collections.asr as nemo_asr
        except Exception as exc:  # pragma: no cover - import error introspection
            raise RuntimeError(
                "Unable to import nemo.collections.asr. Ensure NeMo toolkit is installed."
            ) from exc
        return nemo_asr.models.ASRModel.from_pretrained(model_name=self.model_name)

    def _transcribe_blocking(
        self,
        model,
        audio_bytes: bytes,
        filename: str,
        language: Optional[str],
        prompt: Optional[str],
    ) -> str:
        suffix = os.path.splitext(filename)[-1] or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            LOGGER.debug(
                "Running transcription (language=%s, prompt=%s)",
                language,
                bool(prompt),
            )
            # NeMo expects paths to files.
            result = model.transcribe(paths2audio_files=[tmp_path])
            if not result:
                raise RuntimeError("Model returned no transcription output")
            text = result[0]
            if isinstance(text, (list, tuple)):
                text = " ".join(part for part in text if part)
            return str(text)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp_path)

    def _dispose_model(self, model) -> None:
        try:
            LOGGER.info("Unloading Parakeet model")
            if hasattr(model, "release_memory"):
                model.release_memory()
        except Exception:  # pragma: no cover - best effort cleanup
            LOGGER.exception("Error while releasing model memory")
        finally:
            del model
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():  # pragma: no cover - depends on hardware
                    torch.cuda.empty_cache()
            except Exception:
                LOGGER.debug("torch cleanup step skipped", exc_info=True)
