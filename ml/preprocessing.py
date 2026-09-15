"""
preprocessing.py

Builds a single student-level feature table used by every ML module
(classification, clustering, PCA, anomaly detection).

By default this reads the CLEANED data produced by the ETL transform
step directly from data/raw (re-running the same cleaning logic), so
the ML phases are runnable and gradeable even before MySQL is set up.
If you already have the warehouse loaded, you can instead point this
at the database (see `load_from_warehouse()` below).

Output: data/processed/student_features.csv
"""

import os
import sys
import logging
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "etl"))

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

RISK_MAP = {
    "EXCELLENT": "LOW_RISK",
    "GOOD": "LOW_RISK",
    "AVERAGE": "MEDIUM_RISK",
    "AT_RISK": "HIGH_RISK",
}


def build_student_features() -> pd.DataFrame:
    from extract import extract_all
    from transform import transform_all

    raw = extract_all()
    cleaned, _ = transform_all(raw)

    students = cleaned["students"]
    attendance = cleaned["attendance"]
    assessments = cleaned["assessments"]
    lms = cleaned["lms_activity"]
    performance = cleaned["academic_performance"]

    # Aggregate each per-course/per-semester fact to one row per student
    att_agg = attendance.groupby("student_id")["attendance_percentage"].mean().rename("attendance_percentage")

    assess_agg = assessments.groupby("student_id").agg(
        internal_marks=("internal_marks", "mean"),
        assignment_marks=("assignment_marks", "mean"),
        quiz_marks=("quiz_marks", "mean"),
        lab_marks=("lab_marks", "mean"),
        final_marks=("final_marks", "mean"),
    )

    lms_agg = lms.groupby("student_id").agg(
        login_count=("login_count", "mean"),
        content_views=("content_views", "mean"),
        assignment_submission_rate=("assignment_submission_rate", "mean"),
        average_session_minutes=("average_session_minutes", "mean"),
    )

    # Use each student's latest semester performance record as the "current" snapshot
    perf_sorted = performance.sort_values(["student_id", "semester"])
    perf_latest = perf_sorted.groupby("student_id").tail(1).set_index("student_id")
    perf_latest = perf_latest[["gpa", "cgpa", "backlogs", "academic_status"]]

    features = (
        students.set_index("student_id")[["department", "gender", "admission_year", "entrance_score_band"]]
        .join(att_agg, how="inner")
        .join(assess_agg, how="inner")
        .join(lms_agg, how="inner")
        .join(perf_latest, how="inner")
    )

    features = features.dropna()
    features["student_risk"] = features["academic_status"].map(RISK_MAP)
    features = features.reset_index()

    out_path = os.path.join(PROCESSED_DIR, "student_features.csv")
    features.to_csv(out_path, index=False)
    logger.info("Wrote student feature table: %s (%d students)", out_path, len(features))
    return features


def load_features() -> pd.DataFrame:
    """Loads the processed feature table, building it first if missing."""
    path = os.path.join(PROCESSED_DIR, "student_features.csv")
    if not os.path.exists(path):
        return build_student_features()
    return pd.read_csv(path)


NUMERIC_FEATURES = [
    "attendance_percentage", "internal_marks", "assignment_marks", "quiz_marks",
    "lab_marks", "final_marks", "login_count", "content_views",
    "assignment_submission_rate", "average_session_minutes", "gpa", "cgpa", "backlogs",
]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = build_student_features()
    print(df.head())
    print("\nRisk distribution:\n", df["student_risk"].value_counts())
