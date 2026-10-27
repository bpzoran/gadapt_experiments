import logging
import math
from typing import Callable, Tuple

import numpy as np
from cmaes import CMA

from research_experiments.settings.experiment_ga_settings import ExperimentGASettings
from research_experiments.utils.exp_logging import log_message_info
from research_experiments.utils.experiment_utils import number_of_generations_for_performance_check

logger = logging.getLogger(__name__)

# An improvement of the best cost smaller than this does not count (the same as in SciPy Differential Evolution)
MIN_DELTA = 1e-12


def execute_cmaes_experiment(
    cost_function: Callable,
    bounds: list[tuple[float, float]],
    optimization_name: str = "",
    result_list=None,
) -> Tuple[list[list[float]], float, float, float]:
    """
    Execute a CMA-ES optimization experiment on continuous variables.

    It uses CMA-ES (cmaes.CMA) with the lower and upper bounds of the variables. The population size is the one
    of the other strategies. A run stops
    when the best cost has not improved for `saturation_criteria` generations, or after `number_of_generations`
    generations, which is the same stopping rule as for the other strategies.

    Args:
        cost_function: The objective function to minimize
        bounds: List of (min, max) tuples for each dimension
        optimization_name: Name of the optimization for logging
        result_list: List to append result messages to

    Returns:
        Tuple of (min_cost_per_generations_per_run, final_min_cost, mean_fitness_per_generation, final_average_generations_completed)
    """
    if result_list is None:
        result_list = []

    log_message_info(f"Start optimization with CMA-ES, {optimization_name}:")
    app_settings = ExperimentGASettings()

    lows = np.array([b[0] for b in bounds], dtype=float)
    highs = np.array([b[1] for b in bounds], dtype=float)
    cma_bounds = np.stack([lows, highs], axis=1)
    mean = (lows + highs) / 2.0
    sigma = app_settings.cmaes_sigma_fraction * float(np.mean(highs - lows))

    best_fitness_list = []
    fitness_per_generation = []
    generations_completed = []
    min_cost_per_generations_per_run = []
    final_min_cost = math.nan
    for i in range(app_settings.num_runs):
        optimizer = CMA(mean=mean.copy(), sigma=sigma, bounds=cma_bounds,
                        population_size=app_settings.population_size)
        best = math.inf
        generations_without_improvement = 0
        best_per_generation: list[float] = []  # the best cost found so far, after each generation
        for _ in range(app_settings.number_of_generations):
            solutions = []
            generation_best = math.inf
            for _ in range(optimizer.population_size):
                x = optimizer.ask()
                value = float(cost_function(x))
                solutions.append((x, value))
                generation_best = min(generation_best, value)
            optimizer.tell(solutions)
            if generation_best < best - MIN_DELTA:
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            best = min(best, generation_best)
            best_per_generation.append(best)
            if generations_without_improvement >= app_settings.saturation_criteria or optimizer.should_stop():
                break

        best_fitness_list.append(best)
        generations_completed.append(len(best_per_generation))

        # Get fitness value at the performance checkpoint
        num_of_generations = number_of_generations_for_performance_check(
            len(best_per_generation), app_settings.percentage_of_generations_for_performance
        )
        if num_of_generations > len(best_per_generation):
            logger.warning(
                f"num_of_generations ({num_of_generations}) was > len(best_per_generation) ({len(best_per_generation)})! - {optimization_name}, i = {i}"
            )
            num_of_generations = len(best_per_generation)
        fitness_per_generation.append(best_per_generation[num_of_generations - 1])

        if (i != 0) and (i % app_settings.logging_step == 0):
            log_message_info(f"CMA-ES - {optimization_name} - Optimization number {i}.")
            log_message_info(f"CMA-ES - {optimization_name} - Average best fitness: {round(np.mean(best_fitness_list), 10):.10f}")
            log_message_info(f"CMA-ES - {optimization_name} - Average generations completed: {round(np.mean(generations_completed), 10):.10f}")

        min_cost_per_generations_per_run.append(best_per_generation)
        final_min_cost = round(np.mean(best_fitness_list), 10)

    # Prepare final results
    cmaes_avg_fitness = f"CMA-ES - {optimization_name} - Final average best fitness: {final_min_cost:.10f}"
    final_average_generations = round(np.mean(generations_completed), 10)
    cmaes_avg_generations = f"CMA-ES - {optimization_name} - Final average generations completed: {final_average_generations:.10f}"
    mean_fitness_per_generation = round(np.mean(fitness_per_generation), 10)
    cmaes_avg_fitness_after_n_generations = f"CMA-ES - {optimization_name} - Final average fitness after {app_settings.percentage_of_generations_for_performance} generations: {mean_fitness_per_generation:.10f}"

    log_message_info(cmaes_avg_fitness)
    log_message_info(cmaes_avg_generations)
    result_list.append(f"***********CMA-ES - {optimization_name.upper()}***********")
    result_list.append(cmaes_avg_fitness)
    result_list.append(cmaes_avg_generations)
    result_list.append(cmaes_avg_fitness_after_n_generations)

    return (
        min_cost_per_generations_per_run,
        final_min_cost,
        mean_fitness_per_generation,
        final_average_generations,
    )
