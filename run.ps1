#Requires -Version 5.1
<#
==============================================================================
 MASTER SCRIPT (Windows / PowerShell)
==============================================================================
 Windows counterpart of the `run` bash script. It executes the same
 reproduction pipeline with the same defaults.

 Default Configuration (quick demo):
 - 10 runs
 - For paper replication use 1000 runs (approx. 4 hours): .\run.ps1 --num_runs 1000
 - Default population/mutation settings defined in research_experiment.py

 Usage:
   .\run.ps1
   .\run.ps1 --num_runs 1000
   .\run.ps1 --usecase 4 5

 If script execution is blocked by policy, run it without changing machine
 settings:
   powershell -ExecutionPolicy Bypass -File .\run.ps1
==============================================================================
#>

$ErrorActionPreference = 'Stop'

# --- Configuration ---
# Modify these variables to change the default behavior of the "Reproducible Run"

$NUM_RUNS = 10        # Default: 10 runs (quick demo). Use 1000 for paper replication: .\run.ps1 --num_runs 1000
$POP_SIZE = 64        # Default population size
$RESULTS_DIR = "results"
$BASE_OUTPUT_DIR = $RESULTS_DIR
$DIMENSIONS = @(2, 7, 20)   # Default dimensions to test
$SATURATION_CRITERIAS = @(20)
$KEEP_ELITISM_PERCENTAGE = 50     # Share of the best candidate solutions kept in the population (and used as mating parents)
$PERCENTAGE_OF_MUTATION_CANDIDATE_SOLUTIONS = 60
$PERCENTAGE_OF_MUTATION_DECISION_VARIABLES = 60
$PERCENTAGE_OF_GENERATIONS_FOR_PERFORMANCE = "0.25"   # Length of the early phase used by the REC metric
$NUMBER_OF_GENERATIONS = 600
$SCIPY_DE_ENABLED = "true"
$PYGAD_ADAPTIVE_MUTATION_ENABLED = "true"
$PYGAD_RANDOM_MUTATION_ENABLED = "true"
$GADAPT_DIVERSITY_MUTATION_ENABLED = "true"
$GADAPT_RANDOM_MUTATION_ENABLED = "false"

# --- Strategy-specific settings ---
$PYGAD_PARENT_SELECTION = "roulette_wheel"       # roulette_wheel (as in GAdapt), or a PyGAD type: sss, rws, sus, rank, random, tournament
$PYGAD_RANDOM_MUTATION_PROBABILITY = "0.1"
$PYGAD_ADAPTIVE_MUTATION_PROBABILITIES = @("0.6", "0.1")   # for low-quality and for high-quality solutions
$SCIPY_DE_STRATEGY = "best1exp"
$NORMAL_DISTRIBUTION_MUTATION_MIN_STD_DEV_DECAY_GENERATIONS = ""   # GAdapt: empty = off (constant lower bound of the Gaussian mutation step). A number of generations enables the decay, e.g. 2.5

Write-Host "Starting Experiment with $NUM_RUNS runs..."

# --- Interpreter selection ---
# Prefer the project virtual environment if present, otherwise fall back to
# whatever `python` resolves to on PATH (e.g. an already-activated venv).
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
}
else {
    throw "Python was not found. Install Python 3.12+ and ensure it is on PATH, or create a virtual environment in .venv"
}

# --- Execution ---
# Run from the repository root so relative paths (research_experiment.py,
# results/) resolve the same way they do for the bash script.
# The trailing @args forwards any extra arguments passed on the command line,
# e.g. .\run.ps1 --num_runs 5 --usecase 4

Push-Location $PSScriptRoot
$optionalArguments = @()
if ($NORMAL_DISTRIBUTION_MUTATION_MIN_STD_DEV_DECAY_GENERATIONS -ne "") {
    $optionalArguments += @("--normal_distribution_mutation_min_std_dev_decay_generations", $NORMAL_DISTRIBUTION_MUTATION_MIN_STD_DEV_DECAY_GENERATIONS)
}
try {
    & $python -u research_experiment.py `
        --num_runs $NUM_RUNS `
        --population_size $POP_SIZE `
        --base_output_dir $BASE_OUTPUT_DIR `
        --variable_numbers $DIMENSIONS `
        --saturation_criterias $SATURATION_CRITERIAS `
        --keep_elitism_percentage $KEEP_ELITISM_PERCENTAGE `
        --percentage_of_mutation_candidate_solutions $PERCENTAGE_OF_MUTATION_CANDIDATE_SOLUTIONS `
        --percentage_of_mutation_decision_variables $PERCENTAGE_OF_MUTATION_DECISION_VARIABLES `
        --percentage_of_generations_for_performance $PERCENTAGE_OF_GENERATIONS_FOR_PERFORMANCE `
        --number_of_generations $NUMBER_OF_GENERATIONS `
        --scipy_de_enabled $SCIPY_DE_ENABLED `
        --pygad_adaptive_mutation_enabled $PYGAD_ADAPTIVE_MUTATION_ENABLED `
        --pygad_random_mutation_enabled $PYGAD_RANDOM_MUTATION_ENABLED `
        --gadapt_diversity_mutation_enabled $GADAPT_DIVERSITY_MUTATION_ENABLED `
        --gadapt_random_mutation_enabled $GADAPT_RANDOM_MUTATION_ENABLED `
        --pygad_parent_selection $PYGAD_PARENT_SELECTION `
        --pygad_random_mutation_probability $PYGAD_RANDOM_MUTATION_PROBABILITY `
        --pygad_adaptive_mutation_probabilities $PYGAD_ADAPTIVE_MUTATION_PROBABILITIES `
        --scipy_de_strategy $SCIPY_DE_STRATEGY `
        @optionalArguments `
        @args

    if ($LASTEXITCODE -ne 0) {
        throw "Experiment failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host "Experiment complete. Results saved to $RESULTS_DIR"

<#
==============================================================================
 ARGUMENT REFERENCE
==============================================================================
 Use the arguments below to customize the run via command line or by editing
 the variables above.

 **Integers:**
   --population_size (default: 64)
   --num_runs (default: 1000)
   --logging_step (default: 50)
   --saturation_criteria (default: 20)

 **Floats:**
   --percentage_of_mutation_candidate_solutions (default: 60)
   --percentage_of_mutation_decision_variables (default: 60)
   --pygad_random_mutation_probability (default: 0.1)
   --normal_distribution_mutation_min_std_dev_decay_generations (default: not set, off)
   --pygad_adaptive_mutation_probabilities (two floats: low-quality, high-quality solutions; default: (0.6 0.1))
   --keep_elitism_percentage (default: 50.0)
   --percentage_of_generations_for_performance (default: 0.25)

 **Booleans (true/false, 1/0):**
   --plot_fitness (default: True)
   --gadapt_random_mutation_enabled (default: False)
   --pygad_random_mutation_enabled (default: True)
   --gadapt_diversity_mutation_enabled (default: True)
   --pygad_adaptive_mutation_enabled (default: True)
   --log_to_file (default: True)

 **Strings:**
   --plot_stat (default: "mean")
   --plot_band (default: "ci")
   --pygad_parent_selection (default: "roulette_wheel"; or a PyGAD type: sss, rws, sus, rank, random, tournament)
   --scipy_de_strategy (default: "best1exp")
   --csv_path (default: None)
   --base_output_dir (default: None, the current directory)

 **Lists:**
   --variable_numbers (space-separated ints, default: (2 7 20))
   --saturation_criterias (space-separated ints, default: (15))
   --usecase (space-separated ints, e.g., "4 5")

 **Available Use Cases:**
   1. Separated Trig Arithmetic    7. Ackley
   2. Highly Coupled Trig          8. Griewank
   3. Moderately Coupled Trig      9. Beale
   4. Sphere                      10. Himmelblau
   5. Rosenbrock                  11. Styblinski Tang
   6. Rastrigin                   12. Booth
==============================================================================
#>
