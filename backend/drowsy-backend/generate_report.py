
"""Generate repository PDF reports using the project report implementation."""

import importlib.util
import os
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parent
REPORT_GENERATOR = REPOSITORY_ROOT / "generate_report.py"


def load_report_generator():
    if not REPORT_GENERATOR.is_file():
        raise RuntimeError(
            f"Report generator not found: {REPORT_GENERATOR}"
        )

    spec = importlib.util.spec_from_file_location(
        "project_generate_report",
        REPORT_GENERATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the project report generator")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    report_type = (
        sys.argv[1].lower()
        if len(sys.argv) > 1
        else os.getenv("REPORT_TYPE", "monthly")
    ).lower()

    os.chdir(REPOSITORY_ROOT)
    generator = load_report_generator()

    try:
        generator.generate_pdf(report_type)
    except (RuntimeError, ValueError) as error:
        print(f"\n[ERROR] {error}")
        print("Choose report type: weekly, monthly, or final")
        sys.exit(1)


if __name__ == "__main__":
    main()
