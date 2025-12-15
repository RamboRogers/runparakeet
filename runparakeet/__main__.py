from __future__ import annotations

import argparse
import logging
from typing import Optional

import uvicorn

from .app import create_app
from .config import Settings, ENV_DEFAULTS, env_default


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Parakeet transcription API server")
    parser.add_argument("--host", default=env_default("RUNPARAKEET_HOST", ENV_DEFAULTS["RUNPARAKEET_HOST"]))
    parser.add_argument("--port", type=int, default=int(env_default("RUNPARAKEET_PORT", ENV_DEFAULTS["RUNPARAKEET_PORT"])))
    parser.add_argument("--model", default=env_default("RUNPARAKEET_MODEL", ENV_DEFAULTS["RUNPARAKEET_MODEL"]))
    parser.add_argument(
        "--idle-unload-seconds",
        type=int,
        default=int(env_default("RUNPARAKEET_IDLE_UNLOAD_SECONDS", ENV_DEFAULTS["RUNPARAKEET_IDLE_UNLOAD_SECONDS"])),
        help="Seconds of inactivity before releasing the model (0 to keep loaded)",
    )
    parser.add_argument(
        "--landing-title",
        default=env_default("RUNPARAKEET_LANDING_TITLE", ENV_DEFAULTS["RUNPARAKEET_LANDING_TITLE"]),
    )
    parser.add_argument(
        "--landing-tagline",
        default=env_default("RUNPARAKEET_LANDING_TAGLINE", ENV_DEFAULTS["RUNPARAKEET_LANDING_TAGLINE"]),
    )
    parser.add_argument(
        "--log-level",
        default=env_default("RUNPARAKEET_LOG_LEVEL", ENV_DEFAULTS["RUNPARAKEET_LOG_LEVEL"]),
        help="Python logging level passed to uvicorn",
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto reload (development only)")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    settings = Settings.from_namespace(args)
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=getattr(args, "reload", False),
    )


if __name__ == "__main__":
    main()
