from research_experiments.functions.styblinski_tang import styblinski_tang_func
from research_experiments.runners.experiment import Experiment
from research_experiments.runners.experiment_runner import run_experiment
from research_experiments.utils.exp_logging import log_message_info

TITLE = "Styblinski-Tang Function"
ENABLED = True

def execute():
    log_message_info(TITLE)
    experiment = Experiment(styblinski_tang_func)
    experiment.fill_args_with_same_values(-5, 5, 0)
    experiment.execute_experiment()

def main():
    if not ENABLED:
        log_message_info(f"{TITLE} - Experiment disabled")
        return
    run_experiment(execute)

if __name__ == "__main__":
    main()
