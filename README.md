# Genetic Algorithm Optimization Experiments

This repository contains the experiments that evaluate **diversity-guided mutation**, implemented in the [GAdapt](https://github.com/bpzoran/gadapt) library, against other optimizers. Each use case (a benchmark function) is optimized by five configurations: GAdapt's diversity-guided mutation, PyGAD with random mutation, PyGAD with adaptive mutation, SciPy's Differential Evolution, and CMA-ES (the `cmaes` library). Every configuration is run many times independently, under the same stopping rule, for functions of several dimensionalities. The aim is not to compare the software efficiency of the libraries, but to compare diversity-based self-adaptive mutation with traditional genetic algorithm configurations and with a robust continuous optimizer, in terms of accuracy, convergence speed and reliability across independent runs.

The experiment is fully parametrized from the command line (or by editing the variables in the `run` / `run.ps1` launcher scripts), so the values of the parameters, such as the population size, the stopping rule, the number of runs or the mutation shares, are chosen by the researcher.

## Quick Start

### macOS / Linux

```bash
# 1. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the experiment (quick demo — 10 runs)
source run

# 3. Run with paper-replication settings (1000 runs, ~4 hours)
source run --num_runs 1000

# 4. Run specific use cases only
source run --usecase 4 5
```

### Windows (PowerShell)

```powershell
# 1. Install dependencies
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Run the experiment (quick demo — 10 runs)
.\run.ps1

# 3. Run with paper-replication settings (1000 runs, ~4 hours)
.\run.ps1 --num_runs 1000

# 4. Run specific use cases only
.\run.ps1 --usecase 4 5
```

If PowerShell blocks the script with an execution-policy error, run it without
changing any machine settings:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

## Experiment Design

### Compared Strategies

The configurations share the same core setup: the population size, the share of kept candidate solutions, the variable bounds, the crossover type and the termination limits are aligned across the libraries, even though their configuration syntax differs. Most of these are command-line parameters, see [Command-Line Arguments](#command-line-arguments). That includes the strategy-specific details: the PyGAD parent selection and mutation probabilities, and the Differential Evolution strategy. Their code is in `research_experiments/runners/experiment.py`. Two custom operators are provided for PyGAD (`research_experiments/plugins/pygad/`): the blend crossover, because PyGAD does not include one, and the roulette wheel selection, which works like the one in GAdapt. PyGAD's built-in roulette wheel (`rws`) takes probabilities proportional to the fitness values, and PyGAD maximizes the negated cost, so for the cost functions of this experiment it would favor the worst solutions instead of the best ones. The custom selection uses the ranks of the solutions, like GAdapt does, so it does not depend on the sign or the scale of the cost.

| | GAdapt (diversity mutation) | PyGAD (random mutation) | PyGAD (adaptive mutation) | SciPy (Differential Evolution) | CMA-ES |
|---|---|---|---|---|---|
| **Mutation** | Diversity-guided | Random | Adaptive | Differential evolution mutation with a dithered scale factor | Sampling from an adapted multivariate normal distribution (no mutation operator) |
| **Mutation rate** | Dynamic, regulated by the population diversity in every generation | Fixed probability | Probability adapted to the quality of the candidate solutions | Dynamic (dithering) | Adapted step size and covariance matrix |
| **Parent selection** | Roulette wheel | Roulette wheel | Roulette wheel | Differential evolution strategy | The best half of the sampled candidate solutions update the distribution |
| **Crossover** | Blend | Blend | Blend | Differential evolution recombination | None (recombination of the weighted best samples into the new mean) |
| **Replacement** | A kept share of the population, the rest is replaced by offspring | same | same | One-to-one greedy replacement | A new population is sampled from the updated distribution in every generation |
| **Stopping** | Stagnation-based, the same rule for all five | same | same | same | same |

**CMA-ES** uses `cmaes.CMA` with the bounds of the variables. The initial mean is the center of the range, and the initial standard deviation is `--cmaes_sigma_fraction` (default 0.3) of the range. The population size is the one of the other strategies, `--population_size`, and the stopping rule is the common one (it also stops if CMA-ES itself reports numerical convergence). There are no restarts.

**Diversity-guided mutation in GAdapt** regulates mutation in five stages: the number and the selection of candidate solutions to mutate, the number and the selection of decision variables to mutate, and the alteration of the decision variable values. It is driven by three diversity measures (cost diversity, parent diversity and variable columnar diversity), which are described in the GAdapt documentation. At the choice points GAdapt picks one of the configured methods at random, and a share of plain random choices is retained on purpose, so the search can still escape local optima when the population has converged. Optionally (`--normal_distribution_mutation_min_std_dev_decay_generations`, off by default), the lower bound of the size of the value changes shrinks while the best cost stagnates, which makes the mutation finer exactly when the progress stalls.

### Benchmark Functions

The functions are standard test functions from the optimization literature. They cover separable and non-separable problems, unimodal and multimodal landscapes, and different dimensionalities. The definitions are in `research_experiments/functions/`, and the search ranges in the use case modules.

| # | Function | Motivation |
|---|----------|------------|
| 4 | Sphere | The simplest convex, unimodal, separable function. Checks baseline convergence and the correctness of the implementation |
| 5 | Rosenbrock | Non-convex, with a narrow curved valley. Unimodal, but the valley slows convergence, so it tests fine-tuning near the optimum |
| 6 | Rastrigin | Highly multimodal, with many regularly distributed local minima. Tests avoiding premature convergence and maintaining diversity |
| 7 | Ackley | A nearly flat outer region and a central basin with many local minima. Evaluates global exploration |
| 8 | Griewank | Many widespread local minima with a regular structure. Challenges the balance between exploration and exploitation over a wide search space |
| 11 | Styblinski-Tang | Strongly multimodal, with many local minima and negative optima. Tests maintaining exploration in higher dimensions |
| 9 | Beale | Continuous, unimodal, with steep peripheral peaks and a broad flat basin around the global minimum (two variables) |
| 10 | Himmelblau | Multimodal with four global minima. Tests whether an algorithm consistently converges to any of them (two variables) |
| 12 | Booth | A simple convex function with a single global minimum. A baseline to verify correct convergence in low dimensions (two variables) |

These nine functions are the use cases 4–12. The other functions can have any number of variables, set with `--variable_numbers`, which tests how the strategies scale with the dimensionality. Use cases 1–3 are three additional trigonometric functions, which are not part of the experiment and are disabled by default (`ENABLED = False` in their modules).

Standardized suites such as CEC and BBOB are not used. Their protocols do not match the question asked here: reliability, i.e. whether an optimizer occasionally fails badly, and not only how well it performs on a typical run. Such failures can be rare, so each configuration should be run many times, and the budget is governed by a stagnation-based stopping rule and not by a fixed number of function evaluations. The classical functions are used because their landscapes are well understood, which makes it possible to trace the behavior of a strategy to specific landscape features. They are unrotated, and several of them have the optimum at the origin.

### Experiment Protocol

- **Independent runs.** Every use case, for every number of variables, is executed in `--num_runs` independent runs of each configuration, to account for the stochastic nature of the algorithms.
- **Stopping rule.** A run stops when the best cost has not improved for `--saturation_criteria` generations, or when `--number_of_generations` generations are reached. The same rule applies to all five configurations. It reflects operational use, where the optimizer runs repeatedly, the number of generations cannot be fixed in advance, and each run must decide by itself when to stop. The comparison is specific to the chosen stagnation window, which is why it is a parameter (`--saturation_criterias` accepts several values) and can be varied. Budgets are expressed in generations and not in function evaluations, and the configurations do not necessarily evaluate the same number of candidate solutions per generation.
- **Same conditions.** The same population size, bounds and termination limits are used for all configurations, so that the effect of the mutation strategy is isolated.

### Metrics

For each use case, the following are recorded and aggregated over the runs (the column names are those in `final_results_*.csv`):

| Metric | Definition | Better |
|--------|------------|--------|
| **Average fitness** (`avg_min_fitness`) | Mean of the final minimum fitness over the runs | Lower |
| **Average generations** (`avg_generations`) | Mean number of generations until the stopping rule is met | Lower |
| **Relative Early Convergence, REC** (`relative_early_convergence`) | The share of the total improvement achieved in the early phase of the search. The early phase is not fixed: it is a fraction (`--percentage_of_generations_for_performance`) of the generations of the fastest-converging configuration | Lower |
| **Area Under the Convergence Curve, AUCC** (`area_under_convergence_curve`) | The integral of the best-so-far fitness over the generations: low-cost regions reached early and kept for longer give a smaller area | Lower |
| **Standard deviation, SD** (`sd_min_fitness`) | Standard deviation of the final minimum fitness across the runs: the stability of the optimization | Lower |

The diversity mutation is also compared with each baseline through relative measures (`output/rel_improvements_*.csv`):

- **AFI %** (Adjusted Fitness Improvement): the improvement in average fitness, scaled by the fitness range between the first generation and the baseline's final result. It is not a plain percentage difference, which becomes unstable when both values are small.
- **Generations Δ%**, **REC Δ%** and **AUCC Δ%**: the relative reduction of the average number of generations, of REC and of AUCC. Positive values mean faster or more efficient convergence than the baseline.
- **SD SPC %** (Standard Deviation Symmetric Percent Change): the relative reduction of the variability of the final fitness. A symmetric formulation avoids instability when a denominator is close to zero. Positive values mean more stable optimization than the baseline.

### Statistical Testing

Per-run minimum fitness values of the diversity mutation are compared with each baseline using a paired Wilcoxon signed-rank test (runs matched by index), separately for every function and number of variables. A non-parametric paired test is used because per-run minima are not normally distributed. An omnibus Friedman test over the whole suite (functions as blocks, strategies as treatments) then checks whether the strategies differ at all, followed by a Holm-corrected pairwise post-hoc. All p-values are Holm-Bonferroni adjusted for multiple comparisons, and the effect size is the matched-pairs rank-biserial correlation. Where the means and the ranks answer different questions, both are reported: the mean-based measures (AFI and the other Δ-metrics) reflect reliability, including rare failures, while the rank-based test reflects accuracy on a typical run. See [Statistical Significance](#statistical-significance) for the generated outputs.

## Project Structure

```
GeneticAlgorithmExperiments/
├── run                              # Master bash script (macOS/Linux entry point)
├── run.ps1                          # Master PowerShell script (Windows entry point)
├── research_experiment.py           # Python entry point (called by both scripts)
├── requirements.txt
├── README.md
├── research_experiments/            # Core experiment package
│   ├── __init__.py
│   ├── use_case_01_separated_trig_arithmetic_function.py
│   ├── use_case_02_highly_coupled_trigonometric_function.py
│   ├── use_case_03_moderately_coupled_trigonometric_function.py
│   ├── use_case_04_sphere_function.py
│   ├── use_case_05_rosenbrock_function.py
│   ├── use_case_06_rastrigin_function.py
│   ├── use_case_07_ackley_function.py
│   ├── use_case_08_griewank_function.py
│   ├── use_case_09_beale_function.py
│   ├── use_case_10_himmelblau_function.py
│   ├── use_case_11_styblinski_tang_function.py
│   ├── use_case_12_booth_function.py
│   ├── functions/                   # Benchmark objective functions
│   ├── plugins/                     # PyGAD plugins (blend crossover, roulette wheel selection)
│   ├── runners/                     # Experiment runners & CLI argument parsing
│   │   ├── experiment.py
│   │   ├── experiment_runner.py
│   │   ├── gadapt_experiment.py
│   │   ├── pygad_experiment.py
│   │   ├── scipy_de_experiment.py
│   │   └── cmaes_experiment.py
│   ├── settings/                    # Singleton experiment settings
│   │   └── experiment_ga_settings.py
│   └── utils/                       # Logging, CSV, plotting utilities
│       ├── exp_logging.py
│       ├── csv_writter.py
│       ├── analyze_ga_results_from_csv.py
│       ├── data_aggregation.py
│       ├── plot_fitness_per_generation.py
│       ├── plot_from_csv.py
│       ├── experiment_utils.py
│       ├── export_run_level_data.py
│       └── significance.py
└── results/                         # Default output directory (logs, csv, plots)
```

## Running the Experiments

### Using the launcher script (Recommended)

The launcher script is the primary entry point. It sets default configuration values
and forwards all arguments to `research_experiment.py`. Use `run` on macOS/Linux
and `run.ps1` on Windows — both scripts carry identical defaults and accept
exactly the same arguments.

```bash
# macOS / Linux
source run
```

```powershell
# Windows
.\run.ps1
```

#### Default Configuration (in `run` / `run.ps1`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NUM_RUNS` | `10` | Number of runs (set to `1000` for paper replication) |
| `POP_SIZE` | `64` | Population size |
| `BASE_OUTPUT_DIR` | `results` | Base output directory for logs, CSVs, and plots |
| `DIMENSIONS` | `(2 7 20)` | Dimensionalities to test |
| `SATURATION_CRITERIAS` | `(20)` | Saturation criteria values |
| `KEEP_ELITISM_PERCENTAGE` | `50` | Percentage of the best candidate solutions kept in the population (also the share used as mating parents) |
| `PERCENTAGE_OF_MUTATION_CANDIDATE_SOLUTIONS` | `60` | Percentage of mutation candidate solutions |
| `PERCENTAGE_OF_MUTATION_DECISION_VARIABLES` | `60` | Percentage of mutation decision variables |
| `PERCENTAGE_OF_GENERATIONS_FOR_PERFORMANCE` | `0.25` | Length of the early phase of the search used by the REC metric (a fraction of the generations) |
| `NUMBER_OF_GENERATIONS` | `600` | Number of generations |
| `SCIPY_DE_ENABLED` | `true` | Enable SciPy Differential Evolution |
| `CMAES_ENABLED` | `true` | Enable CMA-ES |
| `PYGAD_ADAPTIVE_MUTATION_ENABLED` | `true` | Enable PyGAD adaptive mutation |
| `PYGAD_RANDOM_MUTATION_ENABLED` | `true` | Enable PyGAD random mutation |
| `GADAPT_DIVERSITY_MUTATION_ENABLED` | `true` | Enable GAdapt diversity mutation |
| `GADAPT_RANDOM_MUTATION_ENABLED` | `false` | Enable GAdapt random mutation |
| `PYGAD_PARENT_SELECTION` | `"roulette_wheel"` | Parent selection of the PyGAD strategies |
| `PYGAD_RANDOM_MUTATION_PROBABILITY` | `0.1` | Mutation probability of PyGAD random mutation |
| `PYGAD_ADAPTIVE_MUTATION_PROBABILITIES` | `(0.6 0.1)` | Mutation probabilities of PyGAD adaptive mutation: for low-quality and for high-quality solutions |
| `NORMAL_DISTRIBUTION_MUTATION_MIN_STD_DEV_DECAY_GENERATIONS` | `""` | GAdapt: empty means off (`--normal_distribution_mutation_min_std_dev_decay_generations` is not passed). A number of generations, e.g. `2.5`, enables the decay |
| `SCIPY_DE_STRATEGY` | `"best1exp"` | Strategy of SciPy Differential Evolution |
| `CMAES_SIGMA_FRACTION` | `0.3` | CMA-ES: initial standard deviation, as a fraction of the range of the variables |

The defaults of the launcher scripts configure the experiment described in [Experiment Design](#experiment-design), with the number of runs set low for a quick demo. You can override any setting by editing the variables at the top of the script, or by
passing arguments on the command line. Command-line arguments are appended after the
script's own defaults, so they always take precedence:

```bash
# macOS / Linux
source run --num_runs 1000 --population_size 128
```

```powershell
# Windows
.\run.ps1 --num_runs 1000 --population_size 128
```

### Using Python Directly

```bash
python -u research_experiment.py --num_runs 100 --population_size 64
```

## Command-Line Arguments

All arguments below can be passed to `run`, to `run.ps1`, or directly to
`research_experiment.py`.

The defaults listed below are those of `research_experiment.py` (see `ExperimentGASettings`). The launcher scripts pass
their own values for some of them, see [Default Configuration](#default-configuration-in-run--runps1): `--num_runs`,
`--saturation_criterias` and `--base_output_dir`.

### Integers

| Argument | Default | Description |
|----------|---------|-------------|
| `--population_size` | `64` | Population size |
| `--num_runs` | `1000` | Number of experiment runs |
| `--logging_step` | `50` | Logging step interval |
| `--saturation_criteria` | `20` | Saturation criteria |
| `--number_of_generations` | `600` | Number of generations per run |

### Floats

| Argument | Default | Description |
|----------|---------|-------------|
| `--percentage_of_mutation_candidate_solutions` | `60` | Percentage of candidate solutions to mutate |
| `--percentage_of_mutation_decision_variables` | `60` | Percentage of decision variables to mutate |
| `--normal_distribution_mutation_min_std_dev_decay_generations` | None | GAdapt (both strategies): by default the lower bound of the standard deviation of the normal distribution mutation is constant. A number of generations enables the decay: the lower bound is divided by 10 for every such number of consecutive generations without an improvement of the minimal cost, so the mutation makes finer adjustments while the progress stalls |
| `--cmaes_sigma_fraction` | `0.3` | CMA-ES: the initial standard deviation, as a fraction of the range of the variables |
| `--pygad_random_mutation_probability` | `0.1` | Mutation probability of PyGAD random mutation (0-1) |
| `--keep_elitism_percentage` | `50.0` | Elitism percentage |
| `--pygad_adaptive_mutation_probabilities` | `0.6 0.1` | Mutation probabilities of PyGAD adaptive mutation (0-1), two values: for low-quality and for high-quality solutions |
| `--percentage_of_generations_for_performance` | `0.25` | Generations fraction for performance check |

> **Removed option.** `--mutation_ratio` no longer exists: the mutation probabilities of the PyGAD strategies are set directly with `--pygad_random_mutation_probability` and `--pygad_adaptive_mutation_probabilities`. Passing it prints a warning.
>
> **Renamed options.** Since GAdapt 0.5.0 uses the terms *candidate solution* and *decision variable* (formerly *chromosome* and *gene*),
> `--percentage_of_mutation_chromosomes` is now `--percentage_of_mutation_candidate_solutions` and
> `--percentage_of_mutation_genes` is now `--percentage_of_mutation_decision_variables`. The previous names are still accepted,
> so commands from earlier versions keep working. The PyGAD arguments (`num_genes`, `mutation_percent_genes`, ...) keep PyGAD's own terminology.

### Booleans

Accepts `true`/`false`, `yes`/`no`, `1`/`0`.

| Argument | Default | Description |
|----------|---------|-------------|
| `--plot_fitness` | `true` | Plot fitness curves |
| `--gadapt_random_mutation_enabled` | `false` | Enable GAdapt random mutation |
| `--pygad_random_mutation_enabled` | `true` | Enable PyGAD random mutation |
| `--gadapt_diversity_mutation_enabled` | `true` | Enable GAdapt diversity mutation |
| `--pygad_adaptive_mutation_enabled` | `true` | Enable PyGAD adaptive mutation |
| `--scipy_de_enabled` | `true` | Enable SciPy Differential Evolution |
| `--cmaes_enabled` | `true` | Enable CMA-ES |
| `--log_to_file` | `true` | Write logs to file |

### Strings

| Argument | Default | Description |
|----------|---------|-------------|
| `--pygad_parent_selection` | `"roulette_wheel"` | Parent selection of the PyGAD strategies: `roulette_wheel` (the custom selection, as in GAdapt), or a PyGAD type: `sss`, `rws`, `sus`, `rank`, `random`, `tournament` |
| `--scipy_de_strategy` | `"best1exp"` | Strategy of SciPy Differential Evolution, any strategy of `scipy.optimize.differential_evolution` |
| `--plot_stat` | `"mean"` | Statistic to plot |
| `--plot_band` | `"ci"` | Plot band type |
| `--csv_path` | None | Custom CSV output path |
| `--results_path` | None | Custom results output path |
| `--plot_path` | None | Custom plot output path |
| `--base_output_dir` | None | Base output directory for all output files (the current directory if not set) |

### Lists

| Argument | Default | Description |
|----------|---------|-------------|
| `--variable_numbers` | `2 7 20` | Dimensionalities to test (space-separated) |
| `--saturation_criterias` | `15` | Saturation criteria values (space-separated) |
| `--usecase` | all enabled | Use cases to run (space-separated, e.g. `4 5`). Use cases 1–3 are disabled by default |

### Available Use Cases

Use cases 4–12 are the nine benchmark functions of the experiment, see [Benchmark Functions](#benchmark-functions). Use cases 1–3 are disabled by default (`ENABLED = False` in their modules), so they are skipped even if selected with `--usecase`.

| # | Function | # | Function |
|---|----------|---|----------|
| 1 | Separated Trig Arithmetic | 7 | Ackley |
| 2 | Highly Coupled Trigonometric | 8 | Griewank |
| 3 | Moderately Coupled Trigonometric | 9 | Beale |
| 4 | Sphere | 10 | Himmelblau |
| 5 | Rosenbrock | 11 | Styblinski-Tang |
| 6 | Rastrigin | 12 | Booth |

## Examples

### macOS / Linux

```bash
# Quick demo (10 runs, all enabled use cases)
source run

# Paper replication (1000 runs, ~4 hours)
source run --num_runs 1000

# Run only Sphere and Rosenbrock
source run --usecase 4 5

# Custom population size and PyGAD parent selection
source run --population_size 128 --pygad_parent_selection tournament

# Disable SciPy DE, run only GA-based optimizers
source run --scipy_de_enabled false

# Custom output directory
source run --base_output_dir /path/to/output
```

### Windows (PowerShell)

```powershell
# Quick demo (10 runs, all enabled use cases)
.\run.ps1

# Paper replication (1000 runs, ~4 hours)
.\run.ps1 --num_runs 1000

# Run only Sphere and Rosenbrock
.\run.ps1 --usecase 4 5

# Custom population size and PyGAD parent selection
.\run.ps1 --population_size 128 --pygad_parent_selection tournament

# Disable SciPy DE, run only GA-based optimizers
.\run.ps1 --scipy_de_enabled false

# Custom output directory
.\run.ps1 --base_output_dir C:\path\to\output
```

## Output

All output of a single run session is written into one timestamped session folder
under `base_output_dir` (default: `results/`), so each run is fully self-contained:

```
results/
└── <timestamp>/             # One run session
    ├── output/              # Reports and aggregated results
    │   ├── GA_comparison_AFI_REC_AUCC.docx
    │   ├── rel_improvements_*.csv
    │   ├── significance_wilcoxon_per_function_dim.csv
    │   ├── significance_friedman_omnibus.csv
    │   ├── significance_friedman_posthoc.csv
    │   ├── per_run_min_fitness.csv          # tidy per-run minima (archival)
    │   ├── per_run_summary_by_comparison.csv
    │   ├── significance_wilcoxon_export.csv         # reviewer-facing column names
    │   ├── significance_friedman_posthoc_export.csv
    │   ├── charts_standard/
    │   └── charts_custom/
    ├── csv/                 # Per-run CSVs, aggregated data, merged results
    ├── log/                 # Timestamped log file
    └── plot/                # Convergence and fitness plots
```

### Convergence plots

Each experiment gets a convergence plot (`<experiment>.png`, 300 dpi) and a
`_counts.png` diagnostic. All plots share the same image size, axes size and x-axis
range (`0..number_of_generations`), so they can be compared directly; extra text such
as the "Avg gen" labels is placed outside the axes box instead of resizing it.

- **Curves** show the mean best-so-far fitness over **all** runs at each generation.
  A run that stops early keeps its final value for the rest of the range, so the end of
  each curve equals the average minimum fitness in `final_results_*.csv`. (Averaging only
  the runs still running would let early-stopping runs drop out and make a strategy's
  tail look better than it is.) The `_counts.png` plot shows how many runs are still
  running at each generation.
- **Y axis** is the gap to the optimum, `f − f*`, on a log scale, clipped at a floor of
  `1e-16` so runs that reach the optimum exactly can be drawn. `f*` is known for the
  benchmark functions (0, or −39.16616570377142 × *d* for Styblinski–Tang). For functions
  without a known optimum the gap is measured from the best value found in any run and
  the axis is labelled "Gap to best found".
- **Grey shading** marks the window used for the Relative Early Convergence (REC)
  metric; **dashed vertical lines** mark each strategy's average number of generations,
  labelled with the same `avg_generations` value reported in `final_results_*.csv`.
- **AFI box** in the corner gives the Adjusted Fitness Improvement of the diversity
  mutation against each baseline.

To regenerate the plots of a finished session from its CSV files, without re-running
the experiments (needs the `runs_*.csv`, `final_results_*.csv` and `aggregated_data_*.csv`
files in the session's `csv/` folder):

```bash
python -m research_experiments.utils.plot_from_csv --csv-dir results/<timestamp>/csv
```

Plots are written to `results/<timestamp>/plot_regenerated/` (change with `--outdir`;
`--x-max`, `--floor` and `--formats` are also available). In addition to the
per-experiment plots, it writes one combined image per function that was run with
several numbers of variables (e.g. `Ackley Function (2, 7, 20 Variables, Saturation = 20).png`),
with the fewest variables on top and the most at the bottom.

### Statistical Significance

The generated report `output/GA_comparison_AFI_REC_AUCC.docx` includes a
**Statistical Significance Testing** section covering:

- **Wilcoxon signed-rank test per function and dimensionality** — paired per-run
  comparison of Diversity mutation against each baseline, matched by run index, run
  separately for every number of variables the function was tested at. This shows
  whether an advantage holds as the search space grows instead of being averaged
  away across dimensionalities.
- **Friedman test across the suite** — functions as blocks, strategies as treatments,
  with a Holm-Bonferroni-corrected pairwise post-hoc.

All reported p-values are Holm-Bonferroni adjusted for multiple comparisons
(α = 0.05), and effect sizes are given as the matched-pairs rank-biserial
correlation. The same results are also written as standalone CSVs in `output/`.

### Per-run data export

The same analysis step also writes machine-readable per-run data, so every statistic
in the report can be recomputed without re-running the experiment:

- **`per_run_min_fitness.csv`** — one row per (function, dimension, saturation,
  strategy, run) with the run's minimum fitness and stop generation. This is the raw
  material behind every significance statistic, produced by the same loader the tests
  use, so it is traceable by construction rather than by transcription.
- **`per_run_summary_by_comparison.csv`** — per (function × dimension × baseline):
  median and mean minimum fitness for each strategy, the Diversity-vs-baseline win
  rate, tie count, and tail counts above a fixed threshold.
- **`significance_wilcoxon_export.csv`** / **`significance_friedman_posthoc_export.csv`**
  — the significance tables with reviewer-facing column names
  (`function, variables, baseline, N, W, p_raw, p_holm, r, significant`).

When reproducing the statistics from `per_run_min_fitness.csv`, read it with
`pd.read_csv(path, float_precision="round_trip")`. Pandas' default parser is off by
up to one ULP, which is numerically irrelevant but flips exact ties on functions where
two strategies reach the same optimum, and therefore perturbs the Wilcoxon *W*.

These exports run automatically as part of every experiment. To regenerate them for a
session that has already finished — without repeating the run:

```bash
python -m research_experiments.utils.export_run_level_data --session results/<timestamp>
```

## Requirements

- Python 3.12 or higher
- pygad==3.5.0
- python-docx==1.2.0
- pandas==2.3.3
- numpy==1.26.4
- scipy==1.17.1
- cmaes==0.13.1
- gadapt==0.5.2
- matplotlib==3.11.2

Supported platforms: macOS, Linux (via `run`) and Windows (via `run.ps1`).
The Windows launcher requires Windows PowerShell 5.1 or PowerShell 7+, both of which
ship with or are readily available on modern Windows.

Install all dependencies:

```bash
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

