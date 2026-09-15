"""
transform.py

Transform phase of the ETL pipeline:
 - data cleaning (missing values, duplicates, invalid values, outliers)
 - type conversion
 - recomputation of derived fields (e.g. attendance_percentage)
 - preparation of clean, warehouse-ready DataFrames

Also exposes `data_quality_report()` to print before/after stats,
satisfying the "data quality validation" requirement.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _quality_snapshot(df: pd.DataFrame, name: str) -> dict:
    return {
        "table": name,
        "rows": len(df),
        "duplicate_rows": int(df.duplicated().sum()),
        "null_cells": int(df.isnull().sum().sum()),
    }


def clean_students(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["student_id"]).copy()
    df["name"] = df["name"].fillna("UNKNOWN")
    df["gender"] = df["gender"].fillna("UNKNOWN")
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
    df["admission_year"] = pd.to_numeric(df["admission_year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["student_id", "department"])
    return df.reset_index(drop=True)


def clean_attendance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates().copy()
    df = df[df["total_classes"] > 0]
    # Fix impossible attended_classes (> total_classes) by capping
    df["attended_classes"] = df[["attended_classes", "total_classes"]].min(axis=1)
    df["attended_classes"] = df["attended_classes"].clip(lower=0)
    # Recompute attendance_percentage instead of trusting the raw (possibly corrupted) value
    df["attendance_percentage"] = (df["attended_classes"] / df["total_classes"] * 100).round(2)
    return df.reset_index(drop=True)


def clean_assessments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates().copy()
    mark_caps = {
        "internal_marks": 50, "assignment_marks": 25, "quiz_marks": 15,
        "lab_marks": 25, "final_marks": 100,
    }
    for col, cap in mark_caps.items():
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].clip(lower=0, upper=cap)
    df = df.dropna(subset=list(mark_caps.keys()))
    return df.reset_index(drop=True)


def clean_lms(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates().copy()
    df["assignment_submission_rate"] = df["assignment_submission_rate"].clip(0, 100)
    df["login_count"] = df["login_count"].clip(lower=0)
    df["content_views"] = df["content_views"].clip(lower=0)
    return df.reset_index(drop=True)


def clean_performance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates().copy()
    df["gpa"] = df["gpa"].clip(0, 10)
    df["cgpa"] = df["cgpa"].clip(0, 10)
    df["backlogs"] = df["backlogs"].clip(lower=0)
    return df.reset_index(drop=True)


def clean_enrollment(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().reset_index(drop=True)


def transform_all(raw: dict) -> dict:
    before = [_quality_snapshot(df, name) for name, df in raw.items()]

    cleaned = {
        "students": clean_students(raw["students"]),
        "course_enrollment": clean_enrollment(raw["course_enrollment"]),
        "attendance": clean_attendance(raw["attendance"]),
        "assessments": clean_assessments(raw["assessments"]),
        "lms_activity": clean_lms(raw["lms_activity"]),
        "academic_performance": clean_performance(raw["academic_performance"]),
    }

    after = [_quality_snapshot(df, name) for name, df in cleaned.items()]

    logger.info("Data quality report:")
    report = pd.DataFrame(before).set_index("table").add_prefix("before_").join(
        pd.DataFrame(after).set_index("table").add_prefix("after_")
    )
    logger.info("\n%s", report.to_string())

    return cleaned, report


if __name__ == "__main__":
    import logging as _logging
    from extract import extract_all
    _logging.basicConfig(level=_logging.INFO)
    raw_data = extract_all()
    cleaned_data, quality_report = transform_all(raw_data)
    print(quality_report)
