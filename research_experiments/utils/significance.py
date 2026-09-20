"""
significance.py

Non-parametric significance testing for GA strategy comparisons (Diversity mutation
vs Adaptive / Random / Differential Evolution baselines), as requested for
IEEE TEVC / SWEVO-tier reporting:

- Wilcoxon signed-rank test per function and per dimensionality (number of variables),
  using the paired per-run minimum-fitness samples (matched by run index) recorded in
  the raw `runs_*.csv` files.
- Friedman test across the whole benchmark suite (functions = blocks, strategies =
  treatments), followed by a Holm-Bonferroni-corrected pairwise Wilcoxon signed-rank
  post-hoc between Diversity mutation and each baseline (functions as matched pairs).

Both procedures follow the nonparametric testing guidance for evolutionary
computation comparisons (Demsar, 2006; Derrac et al., 2011).
"""
from __future__ import annotations

import glob
import os
import re
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, rankdata, wilcoxon

BASELINES = ("adaptive mutation", "random mutation", "differential evolution")
DIVERSITY = "diversity mutation"

_LABEL_RE = re.compile(r"^(.*)\s*\((\d+)\s*Variables,\s*Saturation\s*=\s*(\d+)\)\s*$", re.IGNORECASE)


def parse_experiment_label(label: str) -> tuple[str, int, int] | None:
    """Parse 'Sphere Function (20 Variables, Saturation = 60)' into
    ('Sphere Function', 20, 60). Returns None if the label doesn't match."""
    m = _LABEL_RE.match(str(label).strip())
    if not m:
        return None
    name, nvars, sat = m.groups()
    return name.strip(), int(nvars), int(sat)


def holm_bonferroni(pvalues: Iterable[float]) -> list[float]:
    """Holm-Bonferroni step-down adjustment. NaNs pass through as NaN."""
    pvals = list(pvalues)
    n = len(pvals)
    indexed = [(p, i) for i, p in enumerate(pvals) if not (p is None or np.isnan(p))]
    indexed.sort(key=lambda t: t[0])

    adjusted = [np.nan] * n
    running_max = 0.0
    for rank, (p, i) in enumerate(indexed):
        m = n - rank
        candidate = min(1.0, p * m)
        running_max = max(running_max, candidate)
        adjusted[i] = running_max
    return adjusted


def _signed_rank_stats(diffs: np.ndarray) -> dict:
    """Wilcoxon signed-rank test on paired differences, plus a matched-pairs
    rank-biserial effect size (positive => first sample tends larger)."""
    diffs = np.asarray(diffs, dtype=float)
    diffs = diffs[~np.isnan(diffs)]
    nonzero = diffs[diffs != 0]
    n = nonzero.size

    if n < 1:
        return {
            "n_pairs": diffs.size,
            "statistic": np.nan,
            "p_value": np.nan,
            "effect_size_r": np.nan,
        }

    ranks = rankdata(np.abs(nonzero))
    w_plus = ranks[nonzero > 0].sum()
    w_minus = ranks[nonzero < 0].sum()
    effect_size_r = (w_plus - w_minus) / (w_plus + w_minus) if (w_plus + w_minus) > 0 else np.nan

    try:
        statistic, p_value = wilcoxon(nonzero, zero_method="wilcox", alternative="two-sided", method="auto")
    except ValueError:
        statistic, p_value = np.nan, np.nan

    return {
        "n_pairs": diffs.size,
        "statistic": statistic,
        "p_value": p_value,
        "effect_size_r": effect_size_r,
    }


def load_run_level_minima(csv_dir: str) -> pd.DataFrame:
    """Scan `runs_*.csv` raw per-generation files in csv_dir and reduce each
    (experiment label, strategy, run) triple to its minimum fitness.

    Returns columns: function, number_of_variables, saturation, strategy, run, min_fitness
    """
    rows = []
    for path in sorted(glob.glob(os.path.join(csv_dir, "runs_*.csv"))):
        try:
            df = pd.read_csv(path)
        except (pd.errors.EmptyDataError, OSError):
            continue
        required = {"experiment", "strategy", "run", "cost"}
        if not required.issubset(df.columns):
            continue

        mins = df.groupby(["experiment", "strategy", "run"], as_index=False)["cost"].min()
        mins = mins.rename(columns={"cost": "min_fitness"})
        rows.append(mins)

    if not rows:
        return pd.DataFrame(columns=["function", "number_of_variables", "saturation", "strategy", "run", "min_fitness"])

    all_mins = pd.concat(rows, ignore_index=True)

    parsed = all_mins["experiment"].apply(parse_experiment_label)
    all_mins = all_mins[parsed.notna()].copy()
    parsed = parsed[parsed.notna()]
    all_mins["function"] = [p[0] for p in parsed]
    all_mins["number_of_variables"] = [p[1] for p in parsed]
    all_mins["saturation"] = [p[2] for p in parsed]

    return all_mins[["function", "number_of_variables", "saturation", "strategy", "run", "min_fitness"]]


def wilcoxon_signed_rank_per_function_dimension(
    run_df: pd.DataFrame,
    baselines: tuple[str, ...] = BASELINES,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """One paired Wilcoxon signed-rank test per (function, number_of_variables,
    baseline), so each benchmark function is tested separately at every
    dimensionality it was run at.

    Matched per-run pairs are formed by run index; when a function/dimensionality
    was run at several saturation values, those configurations are pooled into the
    single test for that dimensionality.

    Holm-Bonferroni correction is applied across the whole family of tests
    (function x dimensionality x baseline).

    Positive effect_size_r => Diversity mutation has lower (better) minimum
    fitness than the baseline.
    """
    results = []
    if run_df.empty:
        return pd.DataFrame(columns=[
            "function", "number_of_variables", "compare_to", "n_pairs", "statistic",
            "p_value", "p_value_holm", "effect_size_r", "significant"
        ])

    for (function, nvars), fdf in run_df.groupby(["function", "number_of_variables"]):
        for baseline in baselines:
            diffs_all = []
            for sat, cdf in fdf.groupby("saturation"):
                div = cdf[cdf["strategy"] == DIVERSITY][["run", "min_fitness"]]
                base = cdf[cdf["strategy"] == baseline][["run", "min_fitness"]]
                if div.empty or base.empty:
                    continue
                merged = div.merge(base, on="run", suffixes=("_div", "_base"))
                if merged.empty:
                    continue
                # lower fitness is better => positive diff means Diversity is better
                diffs_all.append((merged["min_fitness_base"] - merged["min_fitness_div"]).to_numpy())

            if not diffs_all:
                continue
            diffs = np.concatenate(diffs_all)
            stats = _signed_rank_stats(diffs)
            results.append({
                "function": function,
                "number_of_variables": nvars,
                "compare_to": baseline,
                "n_pairs": stats["n_pairs"],
                "statistic": stats["statistic"],
                "p_value": stats["p_value"],
                "effect_size_r": stats["effect_size_r"],
            })

    out = pd.DataFrame(results)
    if out.empty:
        return out

    out["p_value_holm"] = holm_bonferroni(out["p_value"].tolist())
    out["significant"] = out["p_value_holm"] < alpha
    return out.sort_values(["function", "number_of_variables", "compare_to"]).reset_index(drop=True)


def friedman_test_suite(
    merged_df: pd.DataFrame,
    value_col: str = "avg_min_fitness",
    baselines: tuple[str, ...] = BASELINES,
    alpha: float = 0.05,
) -> dict:
    """Friedman test across the whole suite: blocks = functions (each function's
    configurations averaged into one score per strategy), treatments = strategies.
    Followed by a Holm-corrected pairwise Wilcoxon signed-rank post-hoc between
    Diversity mutation and each baseline (functions as matched pairs).
    """
    strategies = (DIVERSITY,) + baselines
    per_function = (
        merged_df[merged_df["strategy"].isin(strategies)]
        .groupby(["experiment", "strategy"])[value_col]
        .mean()
        .reset_index()
    )
    pivot = per_function.pivot(index="experiment", columns="strategy", values=value_col)
    complete = pivot.dropna(subset=list(strategies))

    n_functions = len(complete)
    if n_functions < 2:
        return {
            "n_functions": n_functions,
            "k_strategies": len(strategies),
            "statistic": np.nan,
            "p_value": np.nan,
            "significant": False,
            "post_hoc": pd.DataFrame(columns=[
                "compare_to", "n_functions", "statistic", "p_value", "p_value_holm",
                "effect_size_r", "significant"
            ]),
        }

    samples = [complete[s].to_numpy() for s in strategies]
    statistic, p_value = friedmanchisquare(*samples)

    post_hoc_rows = []
    for baseline in baselines:
        diffs = (complete[baseline] - complete[DIVERSITY]).to_numpy()
        stats = _signed_rank_stats(diffs)
        post_hoc_rows.append({
            "compare_to": baseline,
            "n_functions": stats["n_pairs"],
            "statistic": stats["statistic"],
            "p_value": stats["p_value"],
            "effect_size_r": stats["effect_size_r"],
        })

    post_hoc = pd.DataFrame(post_hoc_rows)
    post_hoc["p_value_holm"] = holm_bonferroni(post_hoc["p_value"].tolist())
    post_hoc["significant"] = post_hoc["p_value_holm"] < alpha

    return {
        "n_functions": n_functions,
        "k_strategies": len(strategies),
        "df": len(strategies) - 1,
        "statistic": statistic,
        "p_value": p_value,
        "significant": bool(p_value < alpha) if not np.isnan(p_value) else False,
        "post_hoc": post_hoc,
    }
