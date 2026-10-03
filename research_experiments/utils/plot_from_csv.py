"""
plot_from_csv.py

Regenerates the per-experiment convergence plots from the CSV files of a finished session,
without re-running any experiment.

Reads, from <session>/csv/:
  runs_<experiment>.csv             -> every run's best-so-far values; the curves are built from these:
                                       stopped runs keep their final value up to the end of the plotted
                                       range, and the mean gap to the optimum is drawn on a log axis
  final_results_<experiment>.csv    -> avg generations (vertical-line labels) and the metrics for AFI
  aggregated_data_<experiment>.csv  -> only used to find the longest curve (shared x-axis range)

All plots share one x-axis range: the longest curve found in any experiment of the session
(override with --x-max).

Usage:
    python -m research_experiments.utils.plot_from_csv --csv-dir results/<timestamp>/csv
    python -m research_experiments.utils.plot_from_csv --csv-dir results/<timestamp>/csv \
        --outdir results/<timestamp>/plot_regenerated --x-max 600
"""
import argparse
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from PIL import Image

from research_experiments.utils.data_aggregation import GAP_FLOOR, aggregate_gap_convergence, resolve_optimum
from research_experiments.utils.plot_fitness_per_generation import plot_convergence_curve

_NAME_RE = re.compile(r"^(?P<func>.+?) \((?P<nvars>\d+) Variables, Saturation = (?P<sat>\d+)\)$")
AGG_PREFIX = "aggregated_data_"
FINAL_PREFIX = "final_results_"
RUNS_PREFIX = "runs_"


def _agg_length(path: str) -> int:
    """Number of generations of the longest curve in an aggregated_data file."""
    return int(pd.read_csv(path, usecols=["gen"])["gen"].max()) + 1


def _load_runs(path: str) -> dict[str, list[np.ndarray]]:
    """Per-run best-so-far values per strategy from a runs_<experiment>.csv file."""
    df = pd.read_csv(path, usecols=["strategy", "run", "generation", "cost"],
                     dtype={"strategy": "category", "run": "int32", "generation": "int32", "cost": "float64"})
    df = df.sort_values(["strategy", "run", "generation"], kind="stable")
    runs: dict[str, list[np.ndarray]] = {}
    for strategy, sub in df.groupby("strategy", sort=False, observed=True):
        costs = sub["cost"].to_numpy()
        starts = np.flatnonzero(np.r_[True, np.diff(sub["run"].to_numpy()) != 0])
        runs[str(strategy)] = np.split(costs, starts[1:])
    return runs


def _load_summary(path: str) -> dict[str, dict[str, float]]:
    df = pd.read_csv(path)
    return {
        row["strategy"]: {
            "avg_min_fitness": float(row["avg_min_fitness"]),
            "avg_fitness_after_first": float(row["avg_fitness_after_first"]),
            "avg_generations": float(row["avg_generations"]),
        }
        for _, row in df.iterrows()
    }


def combine_per_function(plot_paths: list[str], outdir: str) -> list[str]:
    """
    Stack the per-experiment PNGs of each function (same name and saturation) into one image:
    fewest variables on top, most at the bottom. Panels keep their native resolution; narrower
    panels are centred on a white background. Functions with a single dimension are skipped.
    """
    groups: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    for path in plot_paths:
        base = os.path.basename(path)
        if not base.lower().endswith(".png") or base.endswith("_counts.png"):
            continue
        m = _NAME_RE.match(base[:-len(".png")])
        if m:
            groups[(m["func"], m["sat"])].append((int(m["nvars"]), path))

    saved: list[str] = []
    for (func, sat), items in sorted(groups.items()):
        if len(items) < 2:
            continue
        items.sort()
        images = [Image.open(path).convert("RGB") for _, path in items]
        width = max(im.width for im in images)
        canvas = Image.new("RGB", (width, sum(im.height for im in images)), "white")
        y = 0
        for im in images:
            canvas.paste(im, ((width - im.width) // 2, y))
            y += im.height
        nvars = ", ".join(str(n) for n, _ in items)
        out = os.path.join(outdir, f"{func} ({nvars} Variables, Saturation = {sat}).png")
        canvas.save(out, dpi=(300, 300))
        saved.append(out)
        print(f"Combined {os.path.basename(out)}")
    return saved


def regenerate_plots(csv_dir: str, outdir: str, x_max: float | None = None,
                     formats: tuple[str, ...] = ("png",), floor: float = GAP_FLOOR,
                     stat: str = "mean", band: str = "ci", seed: int = 0) -> list[str]:
    names = sorted(
        f[len(AGG_PREFIX):-len(".csv")]
        for f in os.listdir(csv_dir)
        if f.startswith(AGG_PREFIX) and f.endswith(".csv")
    )
    if not names:
        raise FileNotFoundError(f"No '{AGG_PREFIX}*.csv' files in {csv_dir}")

    usable = []
    for name in names:
        needed = [f"{FINAL_PREFIX}{name}.csv", f"{RUNS_PREFIX}{name}.csv"]
        missing = [f for f in needed if not os.path.exists(os.path.join(csv_dir, f))]
        if missing:
            print(f"Skipping '{name}': missing {', '.join(missing)}", file=sys.stderr)
            continue
        usable.append(name)

    if x_max is None:
        x_max = max(_agg_length(os.path.join(csv_dir, f"{AGG_PREFIX}{n}.csv")) for n in usable)
    print(f"x-axis range: 0..{x_max:g} generations (shared by all plots)")

    rng = np.random.default_rng(seed)
    os.makedirs(outdir, exist_ok=True)
    saved: list[str] = []
    for name in usable:
        summary = _load_summary(os.path.join(csv_dir, f"{FINAL_PREFIX}{name}.csv"))
        runs = _load_runs(os.path.join(csv_dir, f"{RUNS_PREFIX}{name}.csv"))
        f_star, f_star_known = resolve_optimum(name, runs)
        curves = {
            strategy: aggregate_gap_convergence(strategy_runs, int(x_max), f_star, floor=floor,
                                                stat=stat, band=band, rng=rng)
            for strategy, strategy_runs in runs.items()
        }
        saved += plot_convergence_curve(
            agg=curves,
            # average generations exactly as reported in final_results
            x0={st: summary[st]["avg_generations"] for st in curves if st in summary},
            description=name,
            outdir=outdir,
            save=True,
            basename=name,
            formats=formats,
            metrics_by_strategy=summary,
            x_max=x_max,
            gap_floor=floor,
            gap_label="Gap to optimum f \u2212 f*" if f_star_known else "Gap to best found",
        )
        print(f"Plotted {name}")
    saved += combine_per_function(saved, outdir)
    return saved


def main():
    p = argparse.ArgumentParser(description="Regenerate convergence plots from a session's CSV files.")
    p.add_argument("--csv-dir", required=True, help="Session csv directory (contains aggregated_data_*.csv).")
    p.add_argument("--outdir", default=None,
                   help="Where to write plots (default: <csv-dir>/../plot_regenerated).")
    p.add_argument("--x-max", type=float, default=None,
                   help="Shared x-axis maximum (default: longest curve in the session).")
    p.add_argument("--floor", type=float, default=GAP_FLOOR, help="Floor for the gap on the log axis.")
    p.add_argument("--formats", nargs="+", default=["png"], help="Image formats, e.g. png pdf.")
    a = p.parse_args()
    csv_dir = os.path.abspath(a.csv_dir)
    outdir = a.outdir or os.path.join(os.path.dirname(csv_dir), "plot_regenerated")
    saved = regenerate_plots(csv_dir, outdir, a.x_max, tuple(a.formats), floor=a.floor)
    print(f"Done. {len(saved)} files written to {outdir}")


if __name__ == "__main__":
    main()
