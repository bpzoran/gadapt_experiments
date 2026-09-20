# research_experiment.py
import os
from importlib import import_module
from pathlib import Path
from typing import Callable, List, Optional

from research_experiments.runners.experiment_runner import run_experiment
from research_experiments.settings.experiment_ga_settings import ExperimentGASettings
from research_experiments.utils.analyze_ga_results_from_csv import generate_results
from research_experiments.utils.csv_writter import merge_csvs


def _discover_use_case_modules() -> List[str]:
    """
    Find all Python modules in the same directory as this file whose names
    start with 'use_case', excluding this file and __init__.py. Returns a
    list of module *stems* sorted alphabetically.
    """
    here = Path(__file__).resolve().parent / "research_experiments"

    this_stem = Path(__file__).resolve().stem

    candidates = []
    for p in here.iterdir():
        if (
            p.is_file()
            and p.suffix == ".py"
            and p.stem.startswith("use_case")
            and p.stem not in {this_stem, "__init__"}
        ):
            candidates.append(p.stem)

    candidates.sort()  # sort by module name
    return candidates


def _import_use_case(stem: str):
    """
    Import a module by stem from the current package (relative import if packaged),
    otherwise as a top-level module.
    """
    if __package__:
        return import_module(f".{stem}", package=__package__)
    return import_module(stem)


def _get_main(mod) -> Optional[Callable[[], None]]:
    """
    Return mod.main if present and callable, else None.
    """
    fn = getattr(mod, "main", None)
    return fn if callable(fn) else None


def run_all_use_cases() -> None:
    # must start exactly like this:
    app_settings = ExperimentGASettings()
    app_settings.backup_settings()

    use_cases_to_run = app_settings.use_cases

    for stem in _discover_use_case_modules():
        if use_cases_to_run is not None:
            # Extract the number from the stem (e.g., "use_case_04_sphere_function" -> 4)
            try:
                # Assuming the format is use_case_XX_...
                parts = stem.split('_')
                if len(parts) >= 3 and parts[0] == 'use' and parts[1] == 'case':
                    use_case_num = int(parts[2])
                    if use_case_num not in use_cases_to_run:
                        continue
            except ValueError:
                # If we can't parse the number, skip or include based on logic.
                # Here we skip if we can't match the number.
                continue

        mod = _import_use_case(f"research_experiments.{stem}")
        main_fn = _get_main(mod)
        if main_fn is None:
            # Skip modules without a main()
            continue

        # restore settings before each module's main()
        app_settings.restore_settings()
        main_fn()
    final_results_merged_file_name = f"{os.path.join(app_settings.csv_path, '_final_results_merged.csv')}"
    merged_files, merged_rows = merge_csvs(
        input_dir=app_settings.csv_path,
        filename_prefix="final_results_",
        output_file=final_results_merged_file_name,
        recursive=False,  # set True to include subfolders
        strict=False
    )
    print(f"Merged {merged_files} files, wrote {merged_rows} rows.")
    generate_results(final_results_merged_file_name, app_settings.results_path)


def main() -> None:
    run_experiment(run_all_use_cases)


if __name__ == "__main__":
    main()
