import re
from typing import Optional, List, Tuple, Callable

import numpy as np


def _bootstrap_ci(
    x: np.ndarray,
    fn: Callable[[np.ndarray], float] = np.mean,
    alpha: float = 0.05,
    n_boot: int = 2000,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[float, float, float]:
    if rng is None:
        rng = np.random.default_rng()
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return (np.nan, np.nan, np.nan)
    stat = fn(x)
    if x.size == 1:
        return (stat, stat, stat)
    n = x.size
    boots = np.empty(n_boot, dtype=float)
    idx = rng.integers(0, n, size=(n_boot, n))
    for i in range(n_boot):
        boots[i] = fn(x[idx[i]])
    lo = np.percentile(boots, 100 * (alpha / 2))
    hi = np.percentile(boots, 100 * (1 - alpha / 2))
    return (stat, lo, hi)

# -------- Aggregate per generation across runs --------------------------------
def aggregate_convergence(
    runs: List[List[float]],
    stat: str = "mean",                # "mean" or "median"
    band: str = "ci",                  # "ci" for bootstrap CI, or "iqr" for 25-75%
    alpha: float = 0.05,               # for CI
    n_boot: int = 2000,
    rng: Optional[np.random.Generator] = None,
):
    """
    Aligns runs by generation index and computes central tendency + variability.

    Returns dict with:
      gen: np.ndarray[int]          -> generation indices [0..max_len-1]
      center: np.ndarray[float]     -> mean/median at each generation
      lower: np.ndarray[float]      -> lower band (CI or 25th)
      upper: np.ndarray[float]      -> upper band (CI or 75th)
      n_at_gen: np.ndarray[int]     -> number of runs contributing at each generation
    """
    if rng is None:
        rng = np.random.default_rng()
    # Filter out empty sublists (e.g. from failed runs)
    runs = [r for r in runs if r]
    if not runs:
        empty = np.array([], dtype=float)
        return {
            "gen": np.array([], dtype=int),
            "center": empty,
            "lower": empty,
            "upper": empty,
            "n_at_gen": np.array([], dtype=int),
        }
    max_len = max(len(r) for r in runs)
    gens = np.arange(max_len)
    center, lower, upper, n_at_gen = [], [], [], []

    fn = np.mean if stat == "mean" else np.median

    for g in gens:
        vals = np.array([r[g] for r in runs if len(r) > g], dtype=float)
        n_at_gen.append(vals.size)
        if vals.size == 0:
            center.append(np.nan); lower.append(np.nan); upper.append(np.nan)
            continue

        if band == "ci":
            c, lo, hi = _bootstrap_ci(vals, fn=fn, alpha=alpha, n_boot=n_boot, rng=rng)
        else:  # "iqr" (50% central band)
            c = fn(vals)
            lo, hi = np.percentile(vals, [25, 75])

        center.append(c); lower.append(lo); upper.append(hi)
    return {
        "gen": gens,
        "center": np.array(center),
        "lower": np.array(lower),
        "upper": np.array(upper),
        "n_at_gen": np.array(n_at_gen),
    }

# -------- Gap-to-optimum convergence with carried-forward runs ----------------
GAP_FLOOR = 1e-16

# Known global minima (f*). Styblinski-Tang scales with the number of variables.
_ZERO_OPTIMUM_FUNCTIONS = ("ackley", "beale", "booth", "griewank", "himmelblau",
                           "rastrigin", "rosenbrock", "sphere")
_STYBLINSKI_TANG_PER_VARIABLE = -39.16616570377142


def known_optimum(experiment_name: str, n_vars: Optional[int] = None) -> Optional[float]:
    """
    Global minimum f* of a benchmark function identified by its experiment name
    (e.g. "Ackley Function (2 Variables, Saturation = 20)" or "ackley_func (2 variables, ...)").
    Returns None if the optimum is not known (e.g. the trigonometric use cases).
    """
    name = experiment_name.lower()
    if n_vars is None:
        m = re.search(r"(\d+)\s+variables", name)
        n_vars = int(m.group(1)) if m else None
    if "styblinski" in name:
        return _STYBLINSKI_TANG_PER_VARIABLE * n_vars if n_vars else None
    if any(f in name for f in _ZERO_OPTIMUM_FUNCTIONS):
        return 0.0
    return None


def resolve_optimum(experiment_name: str, runs_by_strategy: dict, n_vars: Optional[int] = None) -> Tuple[float, bool]:
    """
    Returns (f*, is_known). For functions without a known optimum, f* falls back to the best
    value observed in any run of any strategy, so the gap is relative to the best found.
    """
    f_star = known_optimum(experiment_name, n_vars)
    if f_star is not None:
        return f_star, True
    best = min(min(r) for runs in runs_by_strategy.values() for r in runs if len(r))
    return float(best), False


def aggregate_gap_convergence(
    runs: List[List[float]],
    length: int,
    optimum: float,
    floor: float = GAP_FLOOR,
    stat: str = "mean",                # "mean" or "median"
    band: str = "ci",                  # "ci" for bootstrap CI, or "iqr" for 25-75%
    alpha: float = 0.05,
    n_boot: int = 2000,
    rng: Optional[np.random.Generator] = None,
):
    """
    Best-so-far convergence over ALL runs: each run that stops early keeps its final value for
    every later generation, so each point averages the same set of runs (no survivorship bias
    from runs that stopped). Values are converted to a gap to the optimum, max(f - f*, floor),
    so they can be drawn on a log axis even when a run reaches the optimum exactly.

    `length` is the number of generations to cover (the end of the plotted range); it is raised to
    the longest run if that is longer.

    Returns the same dict as aggregate_convergence. `n_at_gen` still counts runs that are
    actually running (not carried forward) at each generation.
    """
    if rng is None:
        rng = np.random.default_rng()
    runs = [r for r in runs if len(r)]
    if not runs:
        empty = np.array([], dtype=float)
        return {"gen": np.array([], dtype=int), "center": empty, "lower": empty,
                "upper": empty, "n_at_gen": np.array([], dtype=int)}

    n = len(runs)
    length = max(int(length), max(len(r) for r in runs))
    gaps = np.empty((n, length), dtype=float)
    n_at_gen = np.zeros(length, dtype=int)
    for i, r in enumerate(runs):
        r = np.asarray(r, dtype=float)
        gaps[i, :len(r)] = r
        gaps[i, len(r):] = r[-1]          # carry the final value forward
        n_at_gen[:len(r)] += 1
    gaps = np.maximum(gaps - optimum, floor)

    if stat == "mean":
        center = gaps.mean(axis=0)
    else:
        center = np.median(gaps, axis=0)

    if band != "ci":
        lower, upper = np.percentile(gaps, [25, 75], axis=0)
    elif stat == "mean" and n > 1:
        # Bootstrap CI of the mean. All generations share the same set of runs, so one resample of
        # run indices serves every generation: boot means = (resample counts) @ gaps / n.
        idx = rng.integers(0, n, size=(n_boot, n))
        counts = np.stack([np.bincount(row, minlength=n) for row in idx]).astype(float)
        boots = counts @ gaps / n
        lower = np.percentile(boots, 100 * (alpha / 2), axis=0)
        upper = np.percentile(boots, 100 * (1 - alpha / 2), axis=0)
    else:
        lower, upper = np.empty(length), np.empty(length)
        for g in range(length):
            _, lower[g], upper[g] = _bootstrap_ci(gaps[:, g], fn=np.median if stat != "mean" else np.mean,
                                                  alpha=alpha, n_boot=n_boot, rng=rng)
    return {"gen": np.arange(length), "center": center, "lower": lower, "upper": upper,
            "n_at_gen": n_at_gen}
