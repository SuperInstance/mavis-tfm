"""mavis-tfm — Time-First Models.

Per Casey's directive (Sept 23 round 11):
"they have a lot of the components as raw ideas that didn't think in
cellular terms yet but did have many elements like first-person view...
or time-first thinking in all sorts of novel and tensor ways."

TFM principle: TIME IS THE FIRST AXIS.
- Every cell's state is derived from its time-seeded hash
- Cell state at time t = hash(seed, t, axioms, dials)
- The "Born rule": probability of observation = |amplitude|²
- Time-between-events is the witness-log signal
- Distributed clocks with skew (time-between-events is sync)

The cell's RNG is its time-axis. Each "tick" produces a deterministic-
but-unpredictable output from the time-seeded hash.
"""
import hashlib
import struct
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


def fnv1a_64(s: str) -> int:
    """FNV-1a 64-bit hash (matches substrate-rng canary derivation)."""
    h = 0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h = h ^ b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h


def time_seed(tick: int, cell_id: str, axioms: Tuple = ()) -> int:
    """A cell's time-seeded hash at tick `tick`.

    Combines:
    - tick (the global time axis)
    - cell_id (the cell's identity)
    - axioms (immutable cell DNA)
    """
    h = hashlib.sha256()
    h.update(struct.pack(">Q", tick))  # tick as 8 bytes
    h.update(cell_id.encode("utf-8"))
    for ax in axioms:
        h.update(str(ax).encode("utf-8"))
        h.update(b"|")  # separator
    digest = h.digest()
    return int.from_bytes(digest[:8], "big")  # take first 8 bytes as u64


def cell_state_at(tick: int, cell_id: str, axioms: Tuple = (),
                  dials: Optional[List[float]] = None) -> Dict[str, Any]:
    """Compute a cell's state at tick `tick`.

    The state is a function of (time, cell_id, axioms, dials).
    Time is the first axis; everything else is derived.

    Returns: dict with seed, hash, amplitudes (Born rule interpretation)
    """
    seed = time_seed(tick, cell_id, axioms)
    if dials:
        # Mix in dials — these are mutable but deterministic given their values
        dial_str = ",".join(f"{d:.6f}" for d in dials)
        seed = (seed ^ fnv1a_64(dial_str)) & 0xffffffffffffffff

    # Generate 4 "amplitudes" — these are the cell's tensor slots at this time
    amplitudes = []
    for i in range(4):
        amp = ((seed >> (i * 16)) & 0xFFFF) / 0xFFFF  # 16-bit fraction
        amplitudes.append(amp)

    # Born rule: probabilities sum to 1
    total = sum(a * a for a in amplitudes)
    if total > 0:
        probs = [(a * a) / total for a in amplitudes]
    else:
        probs = [0.25] * 4

    return {
        "tick": tick,
        "cell_id": cell_id,
        "seed": seed,
        "amplitudes": amplitudes,
        "probabilities": probs,
        "dials": dials or [],
    }


def time_between(tick1: int, tick2: int) -> int:
    """Δt between two events. This is the witness-log sync signal."""
    return abs(tick2 - tick1)


def confidence_from_shared_events(shared_events: int, total_events: int) -> float:
    """Confidence rises with shared events (asymptotic to 0.91+).

    From quilt-spreadsheet: "Confidence rises asymptotically from 0.5 to 0.91."
    """
    if total_events == 0:
        return 0.0
    # Asymptotic convergence: 0.5 + 0.5 * (1 - exp(-n/k))
    import math
    k = 5  # rate constant
    return 0.5 + 0.5 * (1 - math.exp(-shared_events / k))


@dataclass
class TFMClock:
    """A private clock for a cell.

    Each cell has its OWN clock. The cell sees time through this clock.
    Other cells' clocks are external — only witness logs are shared.
    """
    cell_id: str
    axioms: Tuple = ()
    current_tick: int = 0
    dial_history: List[Tuple[int, float]] = field(default_factory=list)

    def tick(self) -> int:
        """Advance the clock by one tick."""
        self.current_tick += 1
        return self.current_tick

    def state(self, dials: Optional[List[float]] = None) -> Dict:
        """Compute current state at current_tick."""
        return cell_state_at(self.current_tick, self.cell_id, self.axioms, dials)

    def set_dial(self, dial_index: int, value: float) -> None:
        """Update a dial. The dial history is a record of (tick, value)."""
        self.dial_history.append((self.current_tick, value))

    def state_at(self, tick: int, dials: Optional[List[float]] = None) -> Dict:
        """Compute state at a specific tick (possibly in the past)."""
        return cell_state_at(tick, self.cell_id, self.axioms, dials)
