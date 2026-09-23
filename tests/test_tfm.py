"""Test suite for mavis-tfm."""
import sys
import time

sys.path.insert(0, "/workspace/repos/mavis-tfm")

from mavis_tfm import (
    fnv1a_64, time_seed, cell_state_at, time_between,
    confidence_from_shared_events, TFMClock, __version__,
)
from mavis_tfm.canary import canary


results = []
failures = []


def test(name, func):
    try:
        func()
        results.append((name, "PASS"))
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        failures.append(name)
    except Exception as e:
        results.append((name, f"ERROR: {type(e).__name__}: {e}"))
        failures.append(name)


# ─── Canary / version ───────────────────────────────────────

def t_canary():
    assert canary() == "0x24a555471370b18d"


def t_version():
    assert __version__ == "0.1.0"


def t_fnv1a_64():
    """FNV-1a 64-bit — matches substrate-rng canary."""
    h = fnv1a_64("cell-witness")
    assert isinstance(h, int)
    assert 0 <= h <= 0xffffffffffffffff


# ─── Time-seeded hash ────────────────────────────────────────

def t_time_seed_deterministic():
    """Same (tick, cell_id, axioms) → same seed."""
    s1 = time_seed(42, "cell-A")
    s2 = time_seed(42, "cell-A")
    assert s1 == s2


def t_time_seed_differs_by_tick():
    """Different tick → different seed."""
    s1 = time_seed(0, "cell-A")
    s2 = time_seed(1, "cell-A")
    assert s1 != s2


def t_time_seed_differs_by_cell():
    """Different cell → different seed."""
    s1 = time_seed(0, "cell-A")
    s2 = time_seed(0, "cell-B")
    assert s1 != s2


def t_time_seed_differs_by_axioms():
    """Different axioms → different seed."""
    s1 = time_seed(0, "cell-A", axioms=("witness",))
    s2 = time_seed(0, "cell-A", axioms=("forget",))
    assert s1 != s2


# ─── Cell state ──────────────────────────────────────────────

def t_cell_state_at():
    """Compute state at a specific tick."""
    s = cell_state_at(0, "cell-A")
    assert s["tick"] == 0
    assert s["cell_id"] == "cell-A"
    assert "seed" in s
    assert "amplitudes" in s
    assert "probabilities" in s


def t_cell_state_amplitudes():
    """4 amplitudes per state (cell has 4 tensor slots)."""
    s = cell_state_at(0, "cell-A")
    assert len(s["amplitudes"]) == 4


def t_cell_state_born_rule():
    """Probabilities sum to 1 (Born rule)."""
    s = cell_state_at(0, "cell-A")
    total = sum(s["probabilities"])
    assert abs(total - 1.0) < 0.001, f"Born rule violated: total={total}"


def t_cell_state_with_dials():
    """Dials modify the state."""
    s1 = cell_state_at(0, "cell-A", dials=[0.0, 0.0, 0.0, 0.0])
    s2 = cell_state_at(0, "cell-A", dials=[1.0, 1.0, 1.0, 1.0])
    assert s1["seed"] != s2["seed"]


def t_cell_state_dials_dont_break_born_rule():
    """Even with dials, probabilities sum to 1."""
    s = cell_state_at(0, "cell-A", dials=[1.0, 2.0, 3.0, 4.0])
    total = sum(s["probabilities"])
    assert abs(total - 1.0) < 0.001


# ─── Time-between / confidence ──────────────────────────────

def t_time_between():
    """Δt is positive integer."""
    assert time_between(0, 5) == 5
    assert time_between(5, 0) == 5  # absolute


def t_confidence_zero():
    assert confidence_from_shared_events(0, 0) == 0.0


def t_confidence_asymptotic():
    """Confidence rises with shared events, asymptotic to ~1.0."""
    c0 = confidence_from_shared_events(0, 10)
    c5 = confidence_from_shared_events(5, 10)
    c100 = confidence_from_shared_events(100, 10)
    assert c0 < c5 < c100
    assert c100 > 0.9


# ─── TFMClock ────────────────────────────────────────────────

def t_clock_initial_tick():
    c = TFMClock(cell_id="cell-A")
    assert c.current_tick == 0


def t_clock_advance():
    c = TFMClock(cell_id="cell-A")
    c.tick()
    c.tick()
    c.tick()
    assert c.current_tick == 3


def t_clock_state():
    c = TFMClock(cell_id="cell-A", axioms=("witness",))
    c.tick()
    state = c.state()
    assert state["tick"] == 1
    assert state["cell_id"] == "cell-A"


def t_clock_set_dial():
    c = TFMClock(cell_id="cell-A")
    c.tick()
    c.set_dial(0, 0.5)
    assert len(c.dial_history) == 1
    assert c.dial_history[0] == (1, 0.5)


def t_clock_state_at_past_tick():
    """Compute state at a past tick (deterministic)."""
    c = TFMClock(cell_id="cell-A")
    c.tick()  # tick = 1
    s = c.state_at(0)  # look at past tick
    assert s["tick"] == 0


def t_two_clocks_diverge_then_sync():
    """Two cells see different times; shared events build confidence."""
    c1 = TFMClock(cell_id="cell-A")
    c2 = TFMClock(cell_id="cell-B")
    for _ in range(10):
        c1.tick()
        c2.tick()
    # Both at tick 10
    assert c1.current_tick == 10
    assert c2.current_tick == 10
    # Confidence after 10 shared events
    conf = confidence_from_shared_events(10, 10)
    assert conf > 0.9


test("test_canary", t_canary)
test("test_version", t_version)
test("test_fnv1a_64", t_fnv1a_64)
test("test_time_seed_deterministic", t_time_seed_deterministic)
test("test_time_seed_differs_by_tick", t_time_seed_differs_by_tick)
test("test_time_seed_differs_by_cell", t_time_seed_differs_by_cell)
test("test_time_seed_differs_by_axioms", t_time_seed_differs_by_axioms)
test("test_cell_state_at", t_cell_state_at)
test("test_cell_state_amplitudes", t_cell_state_amplitudes)
test("test_cell_state_born_rule", t_cell_state_born_rule)
test("test_cell_state_with_dials", t_cell_state_with_dials)
test("test_cell_state_dials_dont_break_born_rule", t_cell_state_dials_dont_break_born_rule)
test("test_time_between", t_time_between)
test("test_confidence_zero", t_confidence_zero)
test("test_confidence_asymptotic", t_confidence_asymptotic)
test("test_clock_initial_tick", t_clock_initial_tick)
test("test_clock_advance", t_clock_advance)
test("test_clock_state", t_clock_state)
test("test_clock_set_dial", t_clock_set_dial)
test("test_clock_state_at_past_tick", t_clock_state_at_past_tick)
test("test_two_clocks_diverge_then_sync", t_two_clocks_diverge_then_sync)

print("\n=== mavis-tfm test results ===")
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n{len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)
