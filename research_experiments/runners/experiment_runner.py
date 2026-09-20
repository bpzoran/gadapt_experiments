import argparse
from typing import Callable

from research_experiments.utils.exp_logging import init_logging
from research_experiments.settings.experiment_ga_settings import ExperimentGASettings

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def run_experiment(experiment: Callable) -> None:
    parser = argparse.ArgumentParser(description="Run Genetic Algorithm Experiment")

    # Ints
    parser.add_argument("--population_size", type=int, help="Population size")
    parser.add_argument("--num_runs", type=int, help="Number of runs")
    parser.add_argument("--logging_step", type=int, help="Logging step")
    parser.add_argument("--saturation_criteria", type=int, help="Saturation criteria")
    parser.add_argument("--number_of_generations", type=int, help="Number of generations")

    # Floats
    parser.add_argument("--percentage_of_mutation_chromosomes", type=float, help="Percentage of mutation chromosomes")
    parser.add_argument("--percentage_of_mutation_genes", type=float, help="Percentage of mutation genes")
    parser.add_argument("--mutation_ratio", type=float, help="Mutation ratio")
    parser.add_argument("--keep_elitism_percentage", type=float, help="Keep elitism percentage")
    parser.add_argument("--percentage_of_generations_for_performance", type=float, help="Percentage of generations for performance")

    # Bools
    parser.add_argument("--plot_fitness", type=str2bool, help="Plot fitness")
    parser.add_argument("--gadapt_random_mutation_enabled", type=str2bool, help="Gadapt random mutation enabled")
    parser.add_argument("--pygad_random_mutation_enabled", type=str2bool, help="Pygad random mutation enabled")
    parser.add_argument("--gadapt_diversity_mutation_enabled", type=str2bool, help="Gadapt diversity mutation enabled")
    parser.add_argument("--pygad_adaptive_mutation_enabled", type=str2bool, help="Pygad adaptive mutation enabled")
    parser.add_argument("--log_to_file", type=str2bool, help="Log to file")
    parser.add_argument("--scipy_de_enabled", type=str2bool, help="SciPy differential evolution enabled")

    # Strings
    parser.add_argument("--plot_stat", type=str, help="Plot stat")
    parser.add_argument("--plot_band", type=str, help="Plot band")
    parser.add_argument("--csv_path", type=str, help="CSV path")
    parser.add_argument("--results_path", type=str, help="Results path")
    parser.add_argument("--plot_path", type=str, help="Plot path")
    parser.add_argument("--base_output_dir", type=str, help="Base output directory for all output files")

    # Lists
    parser.add_argument("--variable_numbers", type=int, nargs='+', help="Variable numbers")
    parser.add_argument("--saturation_criterias", type=int, nargs='+', help="Saturation criterias")
    parser.add_argument("--usecase", type=str, nargs='+', help="Use cases")

    args, unknown = parser.parse_known_args()

    app_settings = ExperimentGASettings()

    if args.population_size is not None: app_settings.population_size = args.population_size
    if args.num_runs is not None: app_settings.num_runs = args.num_runs
    if args.logging_step is not None: app_settings.logging_step = args.logging_step
    if args.saturation_criteria is not None: app_settings.saturation_criteria = args.saturation_criteria
    if args.number_of_generations is not None: app_settings.number_of_generations = args.number_of_generations
    
    if args.percentage_of_mutation_chromosomes is not None: app_settings.percentage_of_mutation_chromosomes = args.percentage_of_mutation_chromosomes
    if args.percentage_of_mutation_genes is not None: app_settings.percentage_of_mutation_genes = args.percentage_of_mutation_genes
    if args.mutation_ratio is not None: app_settings.mutation_ratio = args.mutation_ratio
    if args.keep_elitism_percentage is not None: app_settings.keep_elitism_percentage = args.keep_elitism_percentage
    if args.percentage_of_generations_for_performance is not None: app_settings.percentage_of_generations_for_performance = args.percentage_of_generations_for_performance

    if args.plot_fitness is not None: app_settings.plot_fitness = args.plot_fitness
    if args.gadapt_random_mutation_enabled is not None: app_settings.gadapt_random_mutation_enabled = args.gadapt_random_mutation_enabled
    if args.pygad_random_mutation_enabled is not None: app_settings.pygad_random_mutation_enabled = args.pygad_random_mutation_enabled
    if args.gadapt_diversity_mutation_enabled is not None: app_settings.gadapt_diversity_mutation_enabled = args.gadapt_diversity_mutation_enabled
    if args.pygad_adaptive_mutation_enabled is not None: app_settings.pygad_adaptive_mutation_enabled = args.pygad_adaptive_mutation_enabled
    if args.log_to_file is not None: app_settings.log_to_file = args.log_to_file
    if args.scipy_de_enabled is not None: app_settings.scipy_de_enabled = args.scipy_de_enabled

    if args.plot_stat is not None: app_settings.plot_stat = args.plot_stat
    if args.plot_band is not None: app_settings.plot_band = args.plot_band
    if args.csv_path is not None: app_settings.csv_path = args.csv_path
    if args.results_path is not None: app_settings.results_path = args.results_path
    if args.plot_path is not None: app_settings.plot_path = args.plot_path
    if args.base_output_dir is not None: app_settings.base_output_dir = args.base_output_dir

    if args.variable_numbers is not None: app_settings.variable_numbers = args.variable_numbers
    if args.saturation_criterias is not None: app_settings.saturation_criterias = args.saturation_criterias
    if args.usecase is not None:
        use_cases = []
        for item in args.usecase:
            parts = item.replace('_', ' ').replace(',', ' ').split()
            use_cases.extend([int(p) for p in parts])
        app_settings.use_cases = use_cases

    app_settings.backup_settings()

    if app_settings.csv_path is None:
        init_logging(log_to_file=app_settings.log_to_file, logging_dir=app_settings.base_output_dir or "")

    experiment()
