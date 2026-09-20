from research_experiments.utils.exp_logging import log_message_info
from research_experiments.runners.experiment import Experiment
from research_experiments.runners.experiment_runner import run_experiment
from research_experiments.functions.beale import beale_func
from research_experiments.settings.experiment_ga_settings import ExperimentGASettings
TITLE = "Beale function"
ENABLED = True
def execute():
    log_message_info(TITLE)
    experiment = Experiment(beale_func)
    experiment.fill_args_with_same_values(-4.5, 4.5, 2)
    experiment.execute_experiment()

def main():
    if not ENABLED:
        log_message_info(f"{TITLE} - Experiment disabled")
        return
    run_experiment(execute)

if __name__ == "__main__":
    main()
