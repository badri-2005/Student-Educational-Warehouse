"""
pipeline.py

Orchestrates the full ETL pipeline: extract -> transform -> load.

Run from the project root:
    python etl/pipeline.py

Requires:
    - data/raw/*.csv already generated (python generate_dataset.py)
    - MySQL warehouse schema already created (database/schema.sql,
      database/staging.sql), and a valid .env with DB credentials.
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extract import extract_all
from transform import transform_all
from load import load_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")


def run():
    try:
        logger.info("STEP 1/3: Extract")
        raw = extract_all()

        logger.info("STEP 2/3: Transform")
        cleaned, quality_report = transform_all(raw)
        print("\nData Quality Report (before -> after cleaning):")
        print(quality_report.to_string())

        logger.info("STEP 3/3: Load")
        load_all(cleaned)

        logger.info("ETL pipeline finished successfully.")
    except FileNotFoundError as e:
        logger.error("Missing input file: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.exception("ETL pipeline failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    run()
