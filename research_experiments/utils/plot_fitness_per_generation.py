# ---- MUST be first: pick a headless-safe backend BEFORE importing pyplot ----
import os

# Respect a user-specified backend if set; otherwise default to Agg (safe for RDP/headless).
if "MPLBACKEND" not in os.environ:
    # Setting via matplotlib.use() must happen before importing pyplot.
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend avoids Tk/Qt crashes on headless/RDP
else:
    import matplotlib  # still import to access get_backend later if needed

# -----------------------------------------------------------------------------

import matplotlib.pyplot as plt
import numpy as np

from research_experiments.utils.experiment_utils import transform_function_string

# Fixed figure geometry (inches) shared by every plot: the axes box has the same size in all
# images, regardless of tick labels, legends or annotations. Text that does not fit in the
# axes (e.g. "Avg gen = ...") spills into the margins instead of resizing the plot.
FIG_W, FIG_H = 8.7, 6.7
AX_LEFT, AX_BOTTOM, AX_W, AX_H = 1.0, 1.7, 6.4, 4.4


STRATEGY_ORDER = ("differential evolution", "random mutation", "diversity mutation", "adaptive mutation")


def _fixed_figure_and_axes():
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([AX_LEFT / FIG_W, AX_BOTTOM / FIG_H, AX_W / FIG_W, AX_H / FIG_H])
    return fig, ax


def compute_afi_percent(metrics_by_strategy, baseline, ref="diversity mutation", eps=1e-12):
    """
    AFI (%) = ((f_base_min - f_div_min) / (f_first - f_div_min)) * 100
    where:
      f_first    = metrics_by_strategy[ref]['avg_fitness_after_first']
      f_div_min  = metrics_by_strategy[ref]['avg_min_fitness']
      f_base_min = metrics_by_strategy[baseline]['avg_min_fitness']
    """
    # Check if metrics_by_strategy is None or empty
    if not metrics_by_strategy:
        return np.nan
    
    # Check if ref and baseline exist in metrics
    if ref not in metrics_by_strategy or baseline not in metrics_by_strategy:
        return np.nan

    ref_metrics = metrics_by_strategy[ref]
    base_metrics = metrics_by_strategy[baseline]

    # Check that all required keys exist
    if "avg_fitness_after_first" not in ref_metrics or "avg_min_fitness" not in ref_metrics or "avg_min_fitness" not in base_metrics:
        return np.nan

    f_first   = float(ref_metrics["avg_fitness_after_first"])
    f_div_min = float(ref_metrics["avg_min_fitness"])
    f_base_min= float(base_metrics["avg_min_fitness"])

    # Guard against NaN values
    if np.isnan(f_first) or np.isnan(f_div_min) or np.isnan(f_base_min):
        return np.nan

    denom = f_first - f_div_min
    if abs(denom) < eps:
        return np.nan  # undefined or negligible margin from first gen to div minimum

    return 100.0 * (f_base_min - f_div_min) / denom

def plot_convergence_curve(
    agg,
    x0,
    lowest: float | None = None,
    highest: float | None = None,
    max_len: float | None = None,
    #description: str = "GA Convergence (central tendency ± variability)",
    description: str = "GA Convergence (central tendency)",
    ylabel: str | None = None,
    xlabel: str = "Generation",
    annotate_counts: bool = True,  # plot diagnostic figure with #runs per generation
    vline_kw: dict | None = None,
    text_kw: dict | None = None,
    # --- NEW ---
    save: bool = False,
    outdir: str | None = None,
    basename: str = "convergence",
    formats: tuple[str, ...] = ("png",),
    metrics_by_strategy: dict | None = None,
    x_max: float | None = None,
    gap_floor: float | None = None,
    gap_label: str = "Gap to optimum f \u2212 f*",
):
    """
    agg:
      - single: {"gen","center","lower","upper"}
      - multi:  {label: {"gen","center","lower","upper","n_at_gen"(opt)}}
    x0:
      - single: float
      - multi:  {label: float}

    Y axis:
      - gap_floor=None: linear fitness axis spanning [lowest, highest].
      - gap_floor=<float>: `agg` holds the gap to the optimum (see aggregate_gap_convergence),
        drawn on a log axis whose lower limit is derived from the data (never below gap_floor).
        `gap_label` names the quantity on the axis.

    Saving:
      If save=True, figures are saved to `outdir` using `basename` and `formats`
      (e.g., basename.png, basename_counts.png) and not shown. Returns the list
      of saved file paths. If save=False, figures are shown and [] is returned.
    """
    description = transform_function_string(description)
    log_gap = gap_floor is not None
    if max_len is None:
        series = [agg] if "gen" in agg else list(agg.values())
        max_len = max((len(s["gen"]) for s in series), default=0)
    if not log_gap and (lowest is None or highest is None):
        raise ValueError("lowest and highest are required for a linear y-axis (gap_floor=None).")
    # x-axis spans the generation cap shared by all experiments (x_max) when given, so plots are
    # comparable across functions; otherwise the longest curve of any series in this plot.
    max_len = max(max_len, x_max) if x_max is not None else max_len
    len_border = round(max_len)

    # Normalize to multi-series dict: label -> series_dict
    is_single = isinstance(agg, dict) and {"gen", "center", "lower", "upper"} <= set(agg.keys())
    if is_single:
        series_dict = {"Series": agg}
        x0_map = {"Series": float(x0)}
    else:
        if not isinstance(x0, dict):
            raise TypeError("When agg contains multiple series, x0 must be a dict keyed like agg.")
        # fixed strategy order so every strategy keeps the same colour in all plots
        order = {name: i for i, name in enumerate(STRATEGY_ORDER)}
        series_dict = dict(sorted(agg.items(), key=lambda kv: order.get(kv[0], len(order))))
        x0_map = {k: float(v) for k, v in x0.items()}

    # --- Figure with a caption row ---
    fig, ax = _fixed_figure_and_axes()
    ax.xaxis.labelpad = 6
    fig.text((AX_LEFT + AX_W / 2) / FIG_W, 0.3 / FIG_H, description, ha='center', va='center')

    # Global limits
    xpad_left = round(len_border / 20)
    ax.set_xlim(0 - xpad_left, len_border)
    if log_gap:
        centers = np.concatenate([np.asarray(s["center"], dtype=float) for s in series_dict.values()])
        uppers = np.concatenate([np.asarray(s["upper"], dtype=float) for s in series_dict.values()])
        y_lo = max(np.nanmin(centers) / 3.0, gap_floor / 10.0)
        y_hi = max(np.nanmax(uppers), np.nanmax(centers)) * 3.0
        ax.set_yscale("log")
        ax.set_ylim(y_lo, y_hi)
        ylabel = ylabel or f"{gap_label} (log scale)"
        ax.set_title("GA Convergence (mean gap to optimum)")
    else:
        ypad_bottom = (highest - lowest) / 20 if highest != lowest else 1.0
        ax.set_ylim(lowest - ypad_bottom, highest + ypad_bottom)
        ylabel = ylabel or "Fitness"
        ax.set_title("GA Convergence (central tendency)")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # --- Shade the REC window: first n = 25% of the smallest avg-generations ---
    min_avg_gens = min(x0_map.values()) if x0_map else None
    if min_avg_gens is not None:
        n_rec = int(round(0.25 * min_avg_gens))
        if n_rec > 0:
            ax.axvspan(0, n_rec, alpha=0.08, color='0.5', label="_nolegend_")
            ax.text(n_rec, ax.get_ylim()[0], f" REC window: 0–{n_rec} gen",
                    va='bottom', ha='right', fontsize=8, color='0.3')

    # Common styles
    vk = dict(linestyle='--', linewidth=1.5, color='0.35')
    if vline_kw: vk.update(vline_kw)
    tk = dict(ha='left', va='center')
    if text_kw: tk.update(text_kw)

    # Plot all series; store colors and x0 for stacked annotations later
    colors_by_label: dict[str, str] = {}
    vline_info: list[tuple[str, float, str]] = []  # (label, line x position, color)

    for label, s in series_dict.items():
        gen = np.asarray(s["gen"], dtype=float)
        center = np.asarray(s["center"], dtype=float)
        low = np.asarray(s["lower"], dtype=float)
        up = np.asarray(s["upper"], dtype=float)

        # sort by gen and trim NaNs
        order = np.argsort(gen)
        gen, center, low, up = gen[order], center[order], low[order], up[order]
        valid = ~np.isnan(center)
        if not valid.any():
            continue
        first = np.argmax(valid)
        last = len(valid) - np.argmax(valid[::-1]) - 1
        gen, center, low, up = gen[first:last+1], center[first:last+1], low[first:last+1], up[first:last+1]

        # band & line
        ax.fill_between(gen, low, up, alpha=0.15, label="_nolegend_")
        line, = ax.plot(gen, center, lw=2, label=label)
        line_color = line.get_color()
        colors_by_label[label] = line_color

        # vline in same color

        if label in x0_map:
            x0_val = x0_map[label] - 1  # adjust to align with gen index (0-based)
            if gen.min() <= x0_val <= gen.max():
                ax.axvline(x0_val, **{**vk, "color": line_color})
                vline_info.append((label, x0_val, line_color))


    # legend in a row below the axes so it never covers curves or labels
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.16), ncol=4, fontsize=9, frameon=False,
              columnspacing=1.2, handlelength=1.6)

    # ---- Stack "Avg gen =" annotations so they don't overlap ----
    # Labels show the average generation count as reported in the results tables (x0); the dashed
    # line sits one generation earlier because generations are plotted 0-based.
    if vline_info:
        vline_info.sort(key=lambda t: t[1])  # left -> right
        top_anchor_frac = 0.95
        stack_band_frac = 0.25
        n = len(vline_info)
        dy_frac = stack_band_frac / max(n, 1)
        x_min, x_max_ax = ax.get_xlim()

        for i, (label, x0_val, color) in enumerate(vline_info):
            y_frac = top_anchor_frac - i * dy_frac
            place_left = x0_val > (x_min + 0.85 * (x_max_ax - x_min))
            dx = -6 if place_left else 6
            # y in axes-fraction so the stacking also works on a log axis
            ax.annotate(f"Avg gen = {round(x0_map[label]):g}",
                        xy=(x0_val, y_frac), xycoords=("data", "axes fraction"),
                        xytext=(dx, 0), textcoords='offset points',
                        color=color, ha='left', va='center')
    afi_vs_adaptive = compute_afi_percent(metrics_by_strategy, baseline="adaptive mutation")
    afi_vs_random = compute_afi_percent(metrics_by_strategy, baseline="random mutation")
    afi_vs_differential = compute_afi_percent(metrics_by_strategy, baseline="differential evolution")

    # Build AFI text with available comparisons
    afi_text_lines = []
    if not np.isnan(afi_vs_adaptive):
        afi_text_lines.append(f"AFI vs adaptive: {afi_vs_adaptive:.2f}%")
    if not np.isnan(afi_vs_random):
        afi_text_lines.append(f"AFI vs random: {afi_vs_random:.2f}%")
    if not np.isnan(afi_vs_differential):
        afi_text_lines.append(f"AFI vs differential: {afi_vs_differential:.2f}%")
    
    afi_text = "\n".join(afi_text_lines) if afi_text_lines else "AFI: N/A"
    
    # After you've drawn the curves and set titles/labels:
    ax.text(
        0.01, 0.99, afi_text,
        transform=ax.transAxes, va='top', ha='left', fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.6", alpha=0.9)
    )

    saved_paths: list[str] = []

    # --- Diagnostic plot: #runs per generation for all series ---
    fig2, ax2 = None, None
    if annotate_counts:
        fig2, ax2 = _fixed_figure_and_axes()
        ax2.set_xlim(0 - xpad_left, max_len)
        ax2.set_xlabel("Generation")
        ax2.set_ylabel("# runs still running")
        ax2.set_title("Runs still running per generation")

        for label, s in series_dict.items():
            gen = np.asarray(s["gen"], dtype=float)
            n_at_gen = np.asarray(s["n_at_gen"], dtype=float) if "n_at_gen" in s else None
            if n_at_gen is None:
                continue
            order = np.argsort(gen)
            gen, n_at_gen = gen[order], n_at_gen[order]
            line2, = ax2.plot(gen, n_at_gen, label=label)
            c = colors_by_label.get(label, line2.get_color())
            if label in x0_map:
                x0_val = x0_map[label]
                ax2.axvline(x0_val, **{**vk, "color": c})

        ax2.legend()
        fig2.text((AX_LEFT + AX_W / 2) / FIG_W, 0.3 / FIG_H, description, ha="center", va="center")

    # --- Save or Show ---
    if save:
        outdir_final = outdir or os.getcwd()
        os.makedirs(outdir_final, exist_ok=True)

        # sanitize basename lightly (no path separators)
        safe_base = basename.replace(os.sep, "_").replace("/", "_")

        # main figure
        for ext in formats:
            path = os.path.join(outdir_final, f"{safe_base}.{ext.lstrip('.')}")
            fig.savefig(path, dpi=300)
            saved_paths.append(path)

        # diagnostic figure
        if annotate_counts and fig2 is not None:
            for ext in formats:
                path = os.path.join(outdir_final, f"{safe_base}_counts.{ext.lstrip('.')}")
                fig2.savefig(path, dpi=300)
                saved_paths.append(path)
                try:
                    import csv
                    for label, s in series_dict.items():
                        data_path = os.path.join(outdir_final, f"{safe_base}_{label.replace(' ', '_')}.csv")
                        with open(data_path, "w", newline="") as f:
                            w = csv.writer(f)
                            w.writerow(["gen", "center", "lower", "upper",
                                        "n_at_gen" if "n_at_gen" in s else "n_at_gen (NA)"])
                            ncol_default = np.full_like(s["gen"], 0)
                            ncol = s.get("n_at_gen", ncol_default)
                            for i in range(len(s["gen"])):
                                w.writerow([s["gen"][i], s["center"][i], s["lower"][i], s["upper"][i],
                                            ncol[i] if i < len(ncol) else ""])
                        saved_paths.append(data_path)
                except Exception:
                    pass

        plt.close(fig)
        if fig2 is not None:
            plt.close(fig2)
        return saved_paths

    # default behavior: show (no-op on Agg, but safe)
    if annotate_counts and fig2 is not None:
        plt.show()
    plt.show()
    return []
