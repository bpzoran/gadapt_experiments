# Genetic Algorithm Optimization Experiments

This repository contains a Python project for conducting optimization experiments using genetic algorithms and differential evolution. The experiments focus on comparing different optimization strategies—including adaptive mutation, random mutation, diversity mutation, and SciPy's Differential Evolution—using the PyGAD, GAdapt, and SciPy libraries.

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

## Project Structure

```
GeneticAlgorithmExperiments/
├── run                              # Master bash script (macOS/Linux entry point)
├── run.ps1                          # Master PowerShell script (Windows entry point)
├── research_experiment.py           # Python entry point (called by both scripts)
├── requirements.txt
├── README.md
├── gadapt/                          # GAdapt library
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
│   ├── plugins/                     # PyGAD plugins (e.g. blending crossover)
│   ├── runners/                     # Experiment runners & CLI argument parsing
│   │   ├── experiment.py
│   │   ├── experiment_runner.py
│   │   ├── gadapt_experiment.py
│   │   ├── pygad_experiment.py
│   │   └── scipy_de_experiment.py
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

## Key Features

### Three-Way Optimizer Comparison

The project supports running and comparing three optimization approaches side by side:

- **PyGAD (Random & Adaptive Mutation)**: Standard genetic algorithm with configurable mutation operators.
- **GAdapt (Diversity Mutation)**: Diversity-based mutation that maintains population diversity and avoids premature convergence.
- **SciPy Differential Evolution**: Industry-standard differential evolution optimizer with convergence tracking.

### Benchmark Functions

A comprehensive library of optimization benchmark functions is available in `research_experiments/functions/`, including Rastrigin, Rosenbrock, Sphere, Ackley, Griewank, Beale, Himmelblau, Styblinski-Tang, Booth, and trigonometric variants.

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
| `PERCENTAGE_OF_MUTATION_GENES` | `20` | Percentage of mutation genes |
| `PERCENTAGE_OF_MUTATION_CHROMOSOMES` | `60` | Percentage of mutation chromosomes |
| `NUMBER_OF_GENERATIONS` | `600` | Number of generations |
| `SCIPY_DE_ENABLED` | `true` | Enable SciPy Differential Evolution |
| `PYGAD_ADAPTIVE_MUTATION_ENABLED` | `true` | Enable PyGAD adaptive mutation |
| `PYGAD_RANDOM_MUTATION_ENABLED` | `true` | Enable PyGAD random mutation |
| `GADAPT_RANDOM_MUTATION_ENABLED` | `false` | Enable GAdapt random mutation |

You can override any setting by editing the variables at the top of the script, or by
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

### Integers

| Argument | Default | Description |
|----------|---------|-------------|
| `--population_size` | `64` | Population size |
| `--num_runs` | `1000` | Number of experiment runs |
| `--logging_step` | `50` | Logging step interval |
| `--saturation_criteria` | `15` | Saturation criteria |
| `--number_of_generations` | `600` | Number of generations per run |

### Floats

| Argument | Default | Description |
|----------|---------|-------------|
| `--percentage_of_mutation_chromosomes` | `60` | Percentage of chromosomes to mutate |
| `--percentage_of_mutation_genes` | `20` | Percentage of genes to mutate |
| `--mutation_ratio` | `0.1` | Mutation ratio |
| `--keep_elitism_percentage` | `50.0` | Elitism percentage |
| `--percentage_of_generations_for_performance` | `0.25` | Generations fraction for performance check |

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
| `--log_to_file` | `true` | Write logs to file |

### Strings

| Argument | Default | Description |
|----------|---------|-------------|
| `--plot_stat` | `"mean"` | Statistic to plot |
| `--plot_band` | `"ci"` | Plot band type |
| `--csv_path` | None | Custom CSV output path |
| `--results_path` | None | Custom results output path |
| `--plot_path` | None | Custom plot output path |
| `--base_output_dir` | `"results"` | Base output directory for all output files |

### Lists

| Argument | Default | Description |
|----------|---------|-------------|
| `--variable_numbers` | `2 7 20` | Dimensionalities to test (space-separated) |
| `--saturation_criterias` | `20` | Saturation criteria values (space-separated) |
| `--usecase` | all | Use cases to run (space-separated, e.g. `4 5`) |

### Available Use Cases

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
# Quick demo (10 runs, all use cases)
source run

# Paper replication (1000 runs, ~4 hours)
source run --num_runs 1000

# Run only Sphere and Rosenbrock
source run --usecase 4 5

# Custom population size and mutation ratio
source run --population_size 128 --mutation_ratio 0.2

# Disable SciPy DE, run only GA-based optimizers
source run --scipy_de_enabled false

# Custom output directory
source run --base_output_dir /path/to/output
```

### Windows (PowerShell)

```powershell
# Quick demo (10 runs, all use cases)
.\run.ps1

# Paper replication (1000 runs, ~4 hours)
.\run.ps1 --num_runs 1000

# Run only Sphere and Rosenbrock
.\run.ps1 --usecase 4 5

# Custom population size and mutation ratio
.\run.ps1 --population_size 128 --mutation_ratio 0.2

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
- gadapt==0.4.30
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

