"""mavis-tfm — Time-First Models.

Time is the first axis. Cell state is derived from time-seeded hashes.
"""
from .clock import (
    fnv1a_64, time_seed, cell_state_at, time_between,
    confidence_from_shared_events, TFMClock,
)


__version__ = "0.1.0"


__all__ = [
    "__version__", "fnv1a_64", "time_seed", "cell_state_at", "time_between",
    "confidence_from_shared_events", "TFMClock",
]
