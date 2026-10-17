import numpy as np

ROULETTE_WHEEL = "roulette_wheel"


def roulette_wheel_selection_pygad(fitness, num_parents, ga_instance):
    """
    Roulette wheel parent selection for PyGAD, equivalent to the "roulette_wheel" sampling of GAdapt.

    PyGAD's built-in roulette wheel (`parent_selection_type="rws"`) takes probabilities proportional to
    the fitness values. That only works for positive fitness values: with the fitness used in these
    experiments (the negated cost), the worst solutions would get the highest probability, or the
    probabilities would be invalid. Therefore, as in GAdapt, the probabilities depend on the rank of
    the solution and not on the fitness value, which also makes them independent of the scale and
    the sign of the cost function.

    In each draw, the not yet selected solutions are ranked from the worst (1) to the best, and the
    probability of a solution is proportional to its rank. A selected solution is not drawn again.

    Args:
        fitness: fitness values of the population (PyGAD maximizes the fitness)
        num_parents: number of parents to select
        ga_instance: the PyGAD instance
    Returns:
        the selected parents, and their indices in the population
    """
    fitness = np.asarray(fitness, dtype=float)
    if fitness.ndim > 1:
        fitness = fitness.sum(axis=1)
    remaining = list(np.argsort(fitness, kind="stable"))  # from the worst to the best fitness
    num_parents = min(int(num_parents), len(remaining))
    selected = []
    for _ in range(num_parents):
        ranks = np.arange(1, len(remaining) + 1, dtype=float)
        position = np.random.choice(len(remaining), p=ranks / ranks.sum())
        selected.append(remaining.pop(position))
    parents_indices = np.array(selected, dtype=int)
    parents = ga_instance.population[parents_indices, :].copy()
    return parents, parents_indices


def get_pygad_parent_selection(name: str):
    """
    Returns the value for the `parent_selection_type` parameter of PyGAD: the roulette wheel
    selection defined above for "roulette_wheel", or the name of a PyGAD built-in selection type
    ("sss", "rws", "sus", "rank", "random", "tournament") as it is.
    """
    if name == ROULETTE_WHEEL:
        return roulette_wheel_selection_pygad
    return name
