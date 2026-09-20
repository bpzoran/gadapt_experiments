#Requires -Version 5.1
<#
==============================================================================
 MASTER SCRIPT (Windows / PowerShell)
==============================================================================
 Windows counterpart of the `run` bash script. It executes the same
 reproduction pipeline with the same defaults.

 Default Configuration (Paper Replication):
 - 1000 runs (approx. 4 hours)
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

$NUM_RUNS = 10        # Set to 10 for a quick demo, 1000 for paper replication
$POP_SIZE = 64        # Default population size
$RESULTS_DIR = "results"
$BASE_OUTPUT_DIR = $RESULTS_DIR
$DIMENSIONS = @(2, 7, 20)   # Default dimensions to test
$SATURATION_CRITERIAS = @(20)
$PERCENTAGE_OF_MUTATION_GENES = 20
$PERCENTAGE_OF_MUTATION_CHROMOSOMES = 60
$NUMBER_OF_GENERATIONS = 600
$SCIPY_DE_ENABLED = "true"
$PYGAD_ADAPTIVE_MUTATION_ENABLED = "true"
$PYGAD_RANDOM_MUTATION_ENABLED = "true"
$GADAPT_RANDOM_MUTATION_ENABLED = "false"

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
try {
    & $python -u research_experiment.py `
        --num_runs $NUM_RUNS `
        --population_size $POP_SIZE `
        --base_output_dir $BASE_OUTPUT_DIR `
        --variable_numbers $DIMENSIONS `
        --saturation_criterias $SATURATION_CRITERIAS `
        --percentage_of_mutation_genes $PERCENTAGE_OF_MUTATION_GENES `
        --percentage_of_mutation_chromosomes $PERCENTAGE_OF_MUTATION_CHROMOSOMES `
        --number_of_generations $NUMBER_OF_GENERATIONS `
        --scipy_de_enabled $SCIPY_DE_ENABLED `
        --pygad_adaptive_mutation_enabled $PYGAD_ADAPTIVE_MUTATION_ENABLED `
        --pygad_random_mutation_enabled $PYGAD_RANDOM_MUTATION_ENABLED `
        --gadapt_random_mutation_enabled $GADAPT_RANDOM_MUTATION_ENABLED `
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
   --num_runs (default: 100)
   --logging_step (default: 50)
   --saturation_criteria (default: 15)

 **Floats:**
   --percentage_of_mutation_chromosomes (default: 60)
   --percentage_of_mutation_genes (default: 60)
   --mutation_ratio (default: 0.1)
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
   --csv_path (default: None)
   --base_output_dir (default: "results")

 **Lists:**
   --variable_numbers (space-separated ints, default: (2 7 20))
   --saturation_criterias (space-separated ints, default: (20))
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
