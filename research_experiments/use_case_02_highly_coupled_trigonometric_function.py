from research_experiments.settings.experiment_ga_settings import ExperimentGASettings
from research_experiments.utils.exp_logging import log_message_info
from research_experiments.runners.experiment import Experiment
from research_experiments.runners.experiment_runner import run_experiment
from research_experiments.functions.highly_coupled_trigonometric import highly_coupled_trigonometric_func
TITLE = "Highly Coupled Trigonometric Function"
ENABLED = False
def execute():
    log_message_info(TITLE)
    args_bounds = [{"low": 1.0, "high": 4.0},  # arg1
                   {"low": 37.0, "high": 40.0},  # arg2
                   {"low": 78.0, "high": 88.0},  # arg3
                   {"low": -5.0, "high": 4.0},  # arg4
                   {"low": 1.0, "high": 100.0},  # arg5
                   {"low": 1.0, "high": 4.0},  # arg6
                   {"low": -1, "high": 0.01},  # arg7
                   ]
    experiment = Experiment(highly_coupled_trigonometric_func, args_bounds=args_bounds)
    experiment.execute_experiment()

def main():
    if not ENABLED:
        log_message_info(f"{TITLE} - Experiment disabled")
        return
    run_experiment(execute)

if __name__ == "__main__":
    main()
