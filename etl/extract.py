"""
extract.py

Extract phase of the ETL pipeline: reads the raw CSV files produced
by generate_dataset.py into pandas DataFrames.
"""

import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

FILES = {
    "students": "students.csv",
    "course_enrollment": "course_enrollment.csv",
    "attendance": "attendance.csv",
    "assessments": "assessments.csv",
    "lms_activity": "lms_activity.csv",
    "academic_performance": "academic_performance.csv",
}


def extract_all() -> dict:
    """Reads every raw CSV file and returns a dict of DataFrames keyed by name."""
    data = {}
    for key, filename in FILES.items():
        path = os.path.join(RAW_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Expected raw file not found: {path}. "
                f"Run 'python generate_dataset.py' first."
            )
        df = pd.read_csv(path)
        logger.info("Extracted %s: %d rows, %d columns", filename, len(df), len(df.columns))
        data[key] = df
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dfs = extract_all()
    for name, df in dfs.items():
        print(f"{name}: {df.shape}")
