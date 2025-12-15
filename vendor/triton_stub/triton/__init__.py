"""Stub implementation of the Triton package for Jetson builds.

This module only exists to satisfy NeMo's dependency graph on platforms where the
real Triton compiler is not available (for example Jetson Thor's ARM64 stack).
Attempting to import any attribute will raise so that users are aware that
Triton-backed optimizations are disabled.
"""

class _Unsupported:
    def __getattr__(self, name):  # pragma: no cover - runtime guard
        raise RuntimeError(
            "The Triton compiler is not available on this platform. "
            "If you need Triton-backed optimizations, run on an x86_64 GPU host "
            "with the official Triton binaries."
        )


def __getattr__(name):  # pragma: no cover - runtime guard
    raise RuntimeError(
        "The Triton package is not available on this platform. "
        "This stub only exists to satisfy dependency resolution for NVIDIA NeMo."
    )


runtime = _Unsupported()
client = _Unsupported()
__all__ = ["runtime", "client"]
