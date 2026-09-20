#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_run_level_data.py

Exports reviewer-facing, machine-readable data for a single experiment session.

Produces, into <session>/output/:

  per_run_min_fitness.csv
      Tidy long format, one row per (function, dimension, saturation, strategy, run):
      function, number_of_variables, saturation_generations, strategy, run_index,
      min_fitness, stop_generation
      This is the raw material behind every significance statistic; the per-run minima
      are taken with the *same* loader the tests use, so the file is traceable by
      construction rather than by transcription.

  per_run_summary_by_comparison.csv
      Per (function x dimension x baseline): median min-fitness for each strategy,
      diversity-vs-baseline win rate, and tail counts above a fixed threshold for
      both strategies.

  significance_wilcoxon_export.csv
      The per-function-and-dimensionality Wilcoxon table with reviewer-facing column
      names: function, variables, baseline, N, W, p_raw, p_holm, r, significant

  significance_friedman_omnibus.csv / significance_friedman_posthoc_export.csv
      Friedman omnibus (chi_square, df, N, p) and post-hoc (baseline, W, p_holm, r,
      significant).

Usage:
    python -m research_experiments.utils.export_run_level_data --session results/<timestamp>
"""
from __future__ import annotations

import argparse
import glob
import os

import numpy as np
import pandas as pd

from research_experiments.utils.significance import (
    BASELINES,
    DIVERSITY,
    friedman_test_suite,
    load_run_level_minima,
    parse_experiment_label,
    wilcoxon_signed_rank_per_function_dimension,
)

TAIL_THRESHOLD = 0.1


def _stop_generations(csv_dir: str) -> pd.DataFrame:
    """Final recorded generation index per (function, dim, saturation, strategy, run)."""
    frames = []
    for path in sorted(glob.glob(os.path.join(csv_dir, "runs_*.csv"))):
        try:
            df = pd.read_csv(path)
        except (pd.errors.EmptyDataError, OSError):
            continue
        if not {"experiment", "strategy", "run", "generation"}.issubset(df.columns):
            continue
        g = df.groupby(["experiment", "strategy", "run"], as_index=False)["generation"].max()
        frames.append(g.rename(columns={"generation": "stop_generation"}))

    if not frames:
        return pd.DataFrame(columns=["function", "number_of_variables", "saturation",
                                     "strategy", "run", "stop_generation"])

    out = pd.concat(frames, ignore_index=True)
    parsed = out["experiment"].apply(parse_experiment_label)
    out = out[parsed.notna()].copy()
    parsed = parsed[parsed.notna()]
    out["function"] = [p[0] for p in parsed]
    out["number_of_variables"] = [p[1] for p in parsed]
    out["saturation"] = [p[2] for p in parsed]
    return out[["function", "number_of_variables", "saturation", "strategy", "run", "stop_generation"]]


def build_per_run_table(csv_dir: str) -> pd.DataFrame:
    """Tidy per-run minimum fitness, with stop generation where available."""
    mins = load_run_level_minima(csv_dir)
    if mins.empty:
        return mins

    stops = _stop_generations(csv_dir)
    merged = mins.merge(
        stops,
        on=["function", "number_of_variables", "saturation", "strategy", "run"],
        how="left",
    )
    merged = merged.rename(columns={"saturation": "saturation_generations", "run": "run_index"})
    return merged[[
        "function", "number_of_variables", "saturation_generations",
        "strategy", "run_index", "min_fitness", "stop_generation",
    ]].sort_values(
        ["function", "number_of_variables", "saturation_generations", "strategy", "run_index"]
    ).reset_index(drop=True)


def build_comparison_summary(per_run: pd.DataFrame, threshold: float = TAIL_THRESHOLD) -> pd.DataFrame:
    """Median / win-rate / tail statistics per (function, dimension, baseline)."""
    rows = []
    if per_run.empty:
        return pd.DataFrame()

    for (function, nvars), fdf in per_run.groupby(["function", "number_of_variables"]):
        div = fdf[fdf["strategy"] == DIVERSITY].set_index("run_index")["min_fitness"]
        if div.empty:
            continue
        for baseline in BASELINES:
            base = fdf[fdf["strategy"] == baseline].set_index("run_index")["min_fitness"]
            if base.empty:
                continue
            pair = pd.concat([div.rename("div"), base.rename("base")], axis=1).dropna()
            if pair.empty:
                continue
            diff = pair["base"] - pair["div"]  # positive => diversity better
            rows.append({
                "function": function,
                "number_of_variables": nvars,
                "baseline": baseline,
                "n_pairs": len(pair),
                "median_diversity": pair["div"].median(),
                "median_baseline": pair["base"].median(),
                "mean_diversity": pair["div"].mean(),
                "mean_baseline": pair["base"].mean(),
                "win_rate_diversity": float((diff > 0).mean()),
                "win_rate_baseline": float((diff < 0).mean()),
                "ties": int((diff == 0).sum()),
                f"n_diversity_above_{threshold}": int((pair["div"] > threshold).sum()),
                f"n_baseline_above_{threshold}": int((pair["base"] > threshold).sum()),
                "worst_diversity": pair["div"].max(),
                "worst_baseline": pair["base"].max(),
            })
    return pd.DataFrame(rows)


def export_session(session_dir: str, threshold: float = TAIL_THRESHOLD) -> dict[str, str]:
    csv_dir = os.path.join(session_dir, "csv")
    out_dir = os.path.join(session_dir, "output")
    os.makedirs(out_dir, exist_ok=True)
    written: dict[str, str] = {}

    # 1. Per-run tidy table.
    # Written with pandas' default float repr, which is the shortest text that
    # round-trips float64 exactly. NOTE for anyone reproducing the statistics from
    # this file: read it with
    #     pd.read_csv(path, float_precision="round_trip")
    # pandas' default CSV parser is off by up to one ULP, which is numerically
    # irrelevant but flips exact ties (diff == 0) on functions where both strategies
    # reach the same optimum, and therefore perturbs the Wilcoxon W.
    per_run = build_per_run_table(csv_dir)
    p = os.path.join(out_dir, "per_run_min_fitness.csv")
    per_run.to_csv(p, index=False)
    written["per_run"] = p

    # 2. Comparison summary (median / win-rate / tails)
    summary = build_comparison_summary(per_run, threshold)
    p = os.path.join(out_dir, "per_run_summary_by_comparison.csv")
    summary.to_csv(p, index=False)
    written["summary"] = p

    # 3. Wilcoxon, reviewer-facing column names
    mins = load_run_level_minima(csv_dir)
    wil = wilcoxon_signed_rank_per_function_dimension(mins)
    wil_export = wil.rename(columns={
        "number_of_variables": "variables",
        "compare_to": "baseline",
        "n_pairs": "N",
        "statistic": "W",
        "p_value": "p_raw",
        "p_value_holm": "p_holm",
        "effect_size_r": "r",
    })[["function", "variables", "baseline", "N", "W", "p_raw", "p_holm", "r", "significant"]]
    p = os.path.join(out_dir, "significance_wilcoxon_export.csv")
    wil_export.to_csv(p, index=False)
    written["wilcoxon"] = p

    # 4. Friedman omnibus + post-hoc
    merged_csv = os.path.join(csv_dir, "_final_results_merged.csv")
    fr = friedman_test_suite(pd.read_csv(merged_csv))
    p = os.path.join(out_dir, "significance_friedman_omnibus.csv")
    pd.DataFrame([{
        "chi_square": fr["statistic"],
        "df": fr.get("df"),
        "n_functions": fr["n_functions"],
        "k_strategies": fr["k_strategies"],
        "p_value": fr["p_value"],
        "significant": fr["significant"],
    }]).to_csv(p, index=False)
    written["friedman_omnibus"] = p

    ph = fr["post_hoc"].rename(columns={
        "compare_to": "baseline",
        "n_functions": "N",
        "statistic": "W",
        "p_value": "p_raw",
        "p_value_holm": "p_holm",
        "effect_size_r": "r",
    })[["baseline", "N", "W", "p_raw", "p_holm", "r", "significant"]]
    p = os.path.join(out_dir, "significance_friedman_posthoc_export.csv")
    ph.to_csv(p, index=False)
    written["friedman_posthoc"] = p

    return written


def main():
    ap = argparse.ArgumentParser(description="Export per-run and significance data for one session.")
    ap.add_argument("--session", required=True, help="Session folder, e.g. results/2026_08_21_09_09_34_134")
    ap.add_argument("--threshold", type=float, default=TAIL_THRESHOLD, help="Tail-count threshold")
    args = ap.parse_args()

    written = export_session(args.session, args.threshold)
    print("Wrote:")
    for k, v in written.items():
        print(f" - {v}")


if __name__ == "__main__":
    main()
