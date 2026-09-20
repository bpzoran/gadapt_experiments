import math

from research_experiments.settings.experiment_ga_settings import ExperimentGASettings
from research_experiments.utils.exp_logging import log_message_info
from research_experiments.runners.experiment import Experiment
from research_experiments.runners.experiment_runner import run_experiment
from research_experiments.functions.moderately_coupled_trigonometric import moderately_coupled_trigonometric_func
TITLE = "Moderately Coupled Trigonometric Function"
ENABLED = False

def execute():
    log_message_info(TITLE)
    args_bounds = [{"low": 0, "high": math.pi},  # arg1
                   {"low": 0, "high": math.pi},  # arg2
                   {"low": 0, "high": 200},  # arg3
                   {"low": 0, "high": math.pi},  # arg4
                   {"low": 0, "high": math.pi},  # arg5
                   {"low": 0, "high": 200},  # arg6
                   {"low": 0, "high": math.pi},  # arg7
                   {"low": 0, "high": 200}  # arg8
                   ]

    experiment = Experiment(moderately_coupled_trigonometric_func, args_bounds=args_bounds)
    experiment.execute_experiment()

def main():
    if not ENABLED:
        log_message_info(f"{TITLE} - Experiment disabled")
        return
    run_experiment(execute)

if __name__ == "__main__":
    main()
