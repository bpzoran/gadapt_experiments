"""
plot_from_csv.py

Regenerates the per-experiment convergence plots from the CSV files of a finished session,
without re-running any experiment.

Reads, from <session>/csv/:
  aggregated_data_<experiment>.csv  -> convergence curves (gen, center, lower, upper, n_at_gen)
  final_results_<experiment>.csv    -> avg generations (vertical lines) and the metrics for AFI

All plots share one x-axis range: the longest curve found in any experiment of the session
(override with --x-max).

Usage:
    python -m research_experiments.utils.plot_from_csv --csv-dir results/<timestamp>/csv
    python -m research_experiments.utils.plot_from_csv --csv-dir results/<timestamp>/csv \
        --outdir results/<timestamp>/plot_regenerated --x-max 600
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

from research_experiments.utils.experiment_utils import get_fitness_range
from research_experiments.utils.plot_fitness_per_generation import plot_convergence_curve

AGG_PREFIX = "aggregated_data_"
FINAL_PREFIX = "final_results_"


def _load_agg(path: str) -> dict[str, dict[str, np.ndarray]]:
    df = pd.read_csv(path)
    agg: dict[str, dict[str, np.ndarray]] = {}
    for strategy, sub in df.groupby("strategy", sort=False):
        sub = sub.sort_values("gen")
        agg[strategy] = {
            "gen": sub["gen"].to_numpy(dtype=float),
            "center": sub["center"].to_numpy(dtype=float),
            "lower": sub["lower"].to_numpy(dtype=float),
            "upper": sub["upper"].to_numpy(dtype=float),
            "n_at_gen": sub["n_at_gen"].to_numpy(dtype=float),
        }
    return agg


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


def regenerate_plots(csv_dir: str, outdir: str, x_max: float | None = None,
                     formats: tuple[str, ...] = ("png",)) -> list[str]:
    names = sorted(
        f[len(AGG_PREFIX):-len(".csv")]
        for f in os.listdir(csv_dir)
        if f.startswith(AGG_PREFIX) and f.endswith(".csv")
    )
    if not names:
        raise FileNotFoundError(f"No '{AGG_PREFIX}*.csv' files in {csv_dir}")

    data = {}
    for name in names:
        agg_path = os.path.join(csv_dir, f"{AGG_PREFIX}{name}.csv")
        final_path = os.path.join(csv_dir, f"{FINAL_PREFIX}{name}.csv")
        if not os.path.exists(final_path):
            print(f"Skipping '{name}': missing {os.path.basename(final_path)}", file=sys.stderr)
            continue
        data[name] = (_load_agg(agg_path), _load_summary(final_path))

    if x_max is None:
        x_max = max(len(s["gen"]) for agg, _ in data.values() for s in agg.values())
    print(f"x-axis range: 0..{x_max:g} generations (shared by all plots)")

    os.makedirs(outdir, exist_ok=True)
    saved: list[str] = []
    for name, (runs, summary) in data.items():
        all_uppers = np.concatenate([s["upper"] for s in runs.values() if len(s["upper"])])
        all_lowers = np.concatenate([s["lower"] for s in runs.values() if len(s["lower"])])
        lowest, highest = np.nanmin(all_lowers), np.nanmax(all_uppers)
        max_len = max(len(s["center"]) for s in runs.values())

        results = {"Experiment": {st: {"Average fitness": m["avg_min_fitness"]} for st, m in summary.items()}}
        y_low, y_high = get_fitness_range(results, lowest, highest)

        saved += plot_convergence_curve(
            agg=runs,
            x0={st: summary[st]["avg_generations"] for st in runs if st in summary},
            lowest=y_low,
            highest=y_high,
            max_len=max_len,
            description=name,
            outdir=outdir,
            save=True,
            basename=name,
            formats=formats,
            metrics_by_strategy=summary,
            x_max=x_max,
        )
        print(f"Plotted {name}")
    return saved


def main():
    p = argparse.ArgumentParser(description="Regenerate convergence plots from a session's CSV files.")
    p.add_argument("--csv-dir", required=True, help="Session csv directory (contains aggregated_data_*.csv).")
    p.add_argument("--outdir", default=None,
                   help="Where to write plots (default: <csv-dir>/../plot_regenerated).")
    p.add_argument("--x-max", type=float, default=None,
                   help="Shared x-axis maximum (default: longest curve in the session).")
    p.add_argument("--formats", nargs="+", default=["png"], help="Image formats, e.g. png pdf.")
    a = p.parse_args()
    csv_dir = os.path.abspath(a.csv_dir)
    outdir = a.outdir or os.path.join(os.path.dirname(csv_dir), "plot_regenerated")
    saved = regenerate_plots(csv_dir, outdir, a.x_max, tuple(a.formats))
    print(f"Done. {len(saved)} files written to {outdir}")


if __name__ == "__main__":
    main()
