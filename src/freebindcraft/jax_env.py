"""Process environment for JAX / XLA — apply before ``jax`` is first imported."""

from __future__ import annotations

import os


def apply_default_xla_memory_env() -> None:
    """Prefer on-demand GPU memory growth instead of a large up-front reservation.

    JAX with CUDA often preallocates most VRAM when the runtime starts, which
    looks like “unused” memory in ``nvidia-smi``. If ``XLA_PYTHON_CLIENT_PREALLOCATE``
    is not already set in the environment, we set it to ``false`` so allocation
    tracks actual use. Users can export ``XLA_PYTHON_CLIENT_PREALLOCATE=true`` to
    restore the default eager reservation behavior.
    """
    if "XLA_PYTHON_CLIENT_PREALLOCATE" not in os.environ:
        os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
