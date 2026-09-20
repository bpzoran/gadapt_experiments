from research_experiments.settings.experiment_ga_settings import ExperimentGASettings
from research_experiments.utils.exp_logging import log_message_info
from research_experiments.runners.experiment import Experiment
from research_experiments.runners.experiment_runner import run_experiment
from research_experiments.functions.separated_trig_arithmetic import separated_trig_arithmetic_func
TITLE = "Separated Trig Arithmetic Function"
ENABLED = False
def execute():
    log_message_info(TITLE)
    args_bounds = [{"low": 1.0, "high": 4.0},  # arg1
                   {"low": 37.0, "high": 40.0},  # arg2
                   {"low": 78, "high": 88.0},  # arg3
                   {"low": -5.0, "high": 4.0},  # arg4
                   {"low": 0, "high": 100},  # arg5
                   ]

    experiment = Experiment(separated_trig_arithmetic_func, args_bounds=args_bounds)
    experiment.execute_experiment()

def main():
    if not ENABLED:
        log_message_info(f"{TITLE} - Experiment disabled")
        return
    run_experiment(execute)

if __name__ == "__main__":
    main()
