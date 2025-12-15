from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class Settings:
    """Application configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    model_name: str = "nvidia/parakeet-tdt-0.6b-v3"
    idle_unload_seconds: int = 300
    landing_title: str = "RunParakeet"
    landing_tagline: str = "OpenAI compatible transcription server powered by NVIDIA Parakeet"
    log_level: str = "info"

    @classmethod
    def from_namespace(cls, args: object) -> "Settings":
        return cls(
            host=getattr(args, "host", cls.host),
            port=int(getattr(args, "port", cls.port)),
            model_name=getattr(args, "model", cls.model_name),
            idle_unload_seconds=int(getattr(args, "idle_unload_seconds", cls.idle_unload_seconds)),
            landing_title=getattr(args, "landing_title", cls.landing_title),
            landing_tagline=getattr(args, "landing_tagline", cls.landing_tagline),
            log_level=getattr(args, "log_level", cls.log_level),
        )


ENV_DEFAULTS = {
    "RUNPARAKEET_HOST": "0.0.0.0",
    "RUNPARAKEET_PORT": "8000",
    "RUNPARAKEET_MODEL": "nvidia/parakeet-tdt-0.6b-v3",
    "RUNPARAKEET_IDLE_UNLOAD_SECONDS": "300",
    "RUNPARAKEET_LANDING_TITLE": "RunParakeet",
    "RUNPARAKEET_LANDING_TAGLINE": "OpenAI compatible transcription server powered by NVIDIA Parakeet",
    "RUNPARAKEET_LOG_LEVEL": "info",
}


def env_default(name: str, fallback: str) -> str:
    """Return default value honoring overrides and environment variables."""

    return os.getenv(name, fallback)
