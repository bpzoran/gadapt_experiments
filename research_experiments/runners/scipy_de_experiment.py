import logging
import math
from typing import Callable, Tuple

import numpy as np
from scipy.optimize import differential_evolution

from research_experiments.utils.exp_logging import log_message_info
from research_experiments.settings.experiment_ga_settings import ExperimentGASettings
from research_experiments.utils.experiment_utils import number_of_generations_for_performance_check

logger = logging.getLogger(__name__)


class FitnessTracker:
    """Wraps a cost function to record every evaluation's fitness value."""

    def __init__(self, cost_function: Callable):
        self.cost_function = cost_function
        self.all_values: list[float] = []

    def __call__(self, x):
        value = float(self.cost_function(x))
        self.all_values.append(value)
        return value


class NoImprovementStopper:
    """Stop DE after `patience` iterations without improvement in best cost."""

    def __init__(self, cost_function: Callable, patience: int, min_delta: float = 1e-12, number_of_generations: int = -1):
        self.cost_function = cost_function
        self.patience = patience
        self.min_delta = min_delta
        self.best_fitness = math.inf
        self.wait = 0
        self.gen = 0
        self.fitness_values: list[float] = []
        self.num_of_generations = number_of_generations

    def __call__(self, xk, convergence=None) -> bool:
        current_fitness = float(self.cost_function(xk))
        self.fitness_values.append(current_fitness)

        if current_fitness < (self.best_fitness - self.min_delta):
            self.best_fitness = current_fitness
            self.wait = 0
        else:
            self.wait += 1
        self.gen += 1

        return self.wait >= self.patience or self.gen >= self.num_of_generations


def execute_scipy_de_experiment(
    cost_function: Callable,
    bounds: list[tuple[float, float]],
    optimization_name: str = "",
    result_list=None,
) -> Tuple[list[list[float]], float, float, int]:
    """
    Execute a SciPy Differential Evolution optimization experiment.

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

    log_message_info(f"Start optimization with SciPy DE, {optimization_name}:")
    app_settings = ExperimentGASettings()

    best_fitness_list = []
    fitness_per_generation = []
    iterations_completed = []
    min_cost_per_generations_per_run = []
    final_min_cost = math.nan
    popsize_multiplier = max(1, app_settings.population_size // len(bounds))
    actual_pop_size = popsize_multiplier * len(bounds)
    for i in range(app_settings.num_runs):
        tracker = FitnessTracker(cost_function)
        stopper = NoImprovementStopper(
            cost_function=tracker,
            patience=app_settings.saturation_criteria,
            number_of_generations=app_settings.number_of_generations,
        )

        # Run differential evolution
        result = differential_evolution(
            tracker,
            bounds,
            strategy="best1exp",
            popsize=popsize_multiplier,
            maxiter=10000,
            mutation=(0.5, 1),
            recombination=0.7,
            tol=1e-7,
            polish=False,
            disp=False,
            callback=stopper,
        )



        # The callback is only invoked after each generation (not for the
        # initial population), so stopper.fitness_values misses generation 0.
        # Recover it from the tracker: the best value among the first
        # actual_pop_size evaluations is the initial population's best.
        initial_best = min(tracker.all_values[:actual_pop_size]) if len(tracker.all_values) >= actual_pop_size else result.fun
        fitness_values = [initial_best] + stopper.fitness_values

        # Record results from this run
        best_fitness = result.fun
        best_fitness_list.append(best_fitness)
        iterations_completed.append(result.nit)

        # Get fitness value at the performance checkpoint
        num_of_generations = number_of_generations_for_performance_check(
            result.nit, app_settings.percentage_of_generations_for_performance
        )

        if len(fitness_values) == 0:
            logger.warning(
                f"No fitness values recorded! SciPy DE - {optimization_name}, i = {i}"
            )
            fitness_per_generation.append(best_fitness)
        else:
            if num_of_generations > len(fitness_values):
                num_of_generations_old = num_of_generations
                num_of_generations = len(fitness_values)
                logger.warning(
                    f"num_of_generations ({num_of_generations_old}) was > len(fitness_values) ({len(fitness_values)})! - {optimization_name}, i = {i}"
                )
            fitness_per_generation.append(float(fitness_values[num_of_generations - 1]))

        if (i != 0) and (i % app_settings.logging_step == 0):
            log_message_info(
                f"SciPy DE - {optimization_name} - Optimization number {i}."
            )
            log_message_info(
                f"SciPy DE - {optimization_name} - Average best fitness: {round(np.mean(best_fitness_list), 10):.10f}"
            )
            log_message_info(
                f"SciPy DE - {optimization_name} - Average iterations completed: {round(np.mean(iterations_completed), 10):.10f}"
            )

        min_cost_per_generations_per_run.append(fitness_values)
        final_min_cost = round(np.mean(best_fitness_list), 10)

    # Prepare final results
    scipy_de_avg_fitness = f"SciPy DE - {optimization_name} - Final average best fitness: {final_min_cost:.10f}"
    final_average_iterations = round(np.mean(iterations_completed), 10)
    scipy_de_avg_iterations = f"SciPy DE - {optimization_name} - Final average iterations completed: {final_average_iterations:.10f}"
    mean_fitness_per_generation = round(np.mean(fitness_per_generation), 10)
    scipy_de_avg_fitness_after_n_generations = f"SciPy DE - {optimization_name} - Final average fitness after {app_settings.percentage_of_generations_for_performance} iterations: {mean_fitness_per_generation:.10f}"

    log_message_info(scipy_de_avg_fitness)
    log_message_info(scipy_de_avg_iterations)
    result_list.append(f"***********SCIPY_DE - {optimization_name.upper()}***********")
    result_list.append(scipy_de_avg_fitness)
    result_list.append(scipy_de_avg_iterations)
    result_list.append(scipy_de_avg_fitness_after_n_generations)

    return (
        min_cost_per_generations_per_run,
        final_min_cost,
        mean_fitness_per_generation,
        final_average_iterations,
    )

