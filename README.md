# mavis-tfm

> Time-First Models — TIME IS THE FIRST AXIS.

**Principle (Casey's directive, Sept 23 round 11)**: "time-first thinking in all sorts of novel and tensor ways."

The cell's state at time `t` is derived from `hash(tick, cell_id, axioms, dials)`. Time is the first axis; everything else is derived.

## What it does

- `time_seed(tick, cell_id, axioms)` — deterministic seed at a given tick
- `cell_state_at(tick, cell_id, dials)` — full cell state (seed + 4 amplitudes + Born-rule probabilities)
- `time_between(t1, t2)` — Δt = witness-log sync signal
- `confidence_from_shared_events(n, total)` — asymptotic to 0.91+ (matches quilt-spreadsheet)
- `TFMClock(cell_id, axioms)` — a private cell clock with tick/state/set_dial

## Born rule

Probabilities of observation sum to 1.0 (Born rule interpretation).

## Cell state at a tick

```python
from mavis_tfm import cell_state_at, TFMClock

# One-shot
state = cell_state_at(tick=100, cell_id="image_resizer", dials=[0.1, 0.5, 0.3, 0.9])
print(state["amplitudes"])  # 4 tensor slots
print(state["probabilities"])  # Born-rule (sums to 1)

# With a private clock
clock = TFMClock(cell_id="image_resizer", axioms=("witness",))
clock.tick()
print(clock.state())
```

## Bedrock doctrines

- `time_is_first_axis`: every cell's state derives from time-seeded hash
- `born_rule_holds`: probabilities sum to 1
- `clock_skew_is_signal`: time-between-events is the sync signal across cells
- `confidence_asymptotic`: confidence rises with shared events, → ~1

## Source precursors

- `substrate-rng` — "Quilt cells need to be reproducible. Every cell's randomness is derived from its state hash."
- `substrate-quantum` — Born rule, cell=amplitude, witness=time register
- `quilt-spreadsheet` — "Distributed clocks with skew"; confidence rises asymptotically

Co-authored-by: Mavis <Mavis@superinstance.dev>
