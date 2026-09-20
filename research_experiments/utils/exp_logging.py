import datetime
import logging
import os
from pathlib import Path
from gadapt.utils.TimeStampFormatter import TimestampFormatter

from research_experiments.settings.experiment_ga_settings import ExperimentGASettings

# Maximum log file size in bytes (default: 5 MB)
MAX_LOG_FILE_SIZE = 5 * 1024 * 1024
# Number of backup log files to keep
BACKUP_COUNT = 5


def init_logging(log_to_file: bool, logging_dir: str = ""):
    """
    Initializes logging for genetic algorithm experiments.

    All output of a single run session is written into one timestamped session
    folder under logging_dir, structured as:

        <logging_dir>/<timestamp>/output   reports, charts   -> results_path
        <logging_dir>/<timestamp>/csv      per-run & merged CSVs -> csv_path
        <logging_dir>/<timestamp>/log      log file
        <logging_dir>/<timestamp>/plot     convergence plots -> plot_path

    If logging_dir is empty, defaults to a 'results' folder in the current working directory.
    """

    if not logging_dir:
        logging_dir = os.path.join(os.getcwd(), "results")

    app_settings = ExperimentGASettings()

    now = datetime.datetime.now()
    formatted_date_time = now.strftime('%Y_%m_%d_%H_%M_%S_') + f'{now.microsecond // 1000:03d}'

    session_path = Path(logging_dir) / formatted_date_time
    results_path = session_path / "output"
    csv_path = session_path / "csv"
    log_dir = session_path / "log"
    plot_path = session_path / "plot"

    for directory in (results_path, csv_path, log_dir, plot_path):
        os.makedirs(directory, exist_ok=True)

    app_settings.results_path = str(results_path)
    app_settings.csv_path = str(csv_path)
    app_settings.plot_path = str(plot_path)

    log_path = os.path.join(log_dir, f"ga_exp_log_{formatted_date_time}.log")

    logger = logging.getLogger("ga_exp_logger")
    for h in logger.handlers:
        logger.removeHandler(h)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        TimestampFormatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    logger.addHandler(console_handler)
    if log_to_file:
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(
            TimestampFormatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)


def log_message_info(message: str):
    ga_exp_logger = logging.getLogger("ga_exp_logger")
    ga_exp_logger.log(level=logging.INFO, msg=message)
