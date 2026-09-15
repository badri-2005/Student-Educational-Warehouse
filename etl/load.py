"""
load.py

Load phase of the ETL pipeline:
 1. Load cleaned data into staging tables (stg_*).
 2. Load/merge dimension tables (dim_student uses SCD Type 2).
 3. Resolve surrogate keys and load fact tables.

Requires a running MySQL 8 instance with the warehouse schema already
created (run database/schema.sql and database/staging.sql first).
"""

import logging
from datetime import date

import pandas as pd
from sqlalchemy import text

from db import get_engine

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------
# Staging load
# ----------------------------------------------------------------
def load_staging(cleaned: dict, engine):
    mapping = {
        "students": "stg_students",
        "course_enrollment": "stg_course_enrollment",
        "attendance": "stg_attendance",
        "assessments": "stg_assessments",
        "lms_activity": "stg_lms_activity",
        "academic_performance": "stg_academic_performance",
    }
    with engine.begin() as conn:
        for key, table in mapping.items():
            conn.execute(text(f"TRUNCATE TABLE {table}"))
            cleaned[key].to_sql(table, conn, if_exists="append", index=False)
            logger.info("Loaded %d rows into %s", len(cleaned[key]), table)


# ----------------------------------------------------------------
# Dimension loads
# ----------------------------------------------------------------
def load_dim_department(cleaned: dict, engine):
    depts = cleaned["students"]["department"].dropna().unique()
    with engine.begin() as conn:
        for d in depts:
            conn.execute(text("""
                INSERT INTO dim_department (department_id, department_name)
                SELECT :d, :d
                WHERE NOT EXISTS (
                    SELECT 1 FROM dim_department WHERE department_id = :d
                )
            """), {"d": d})


def load_dim_semester(cleaned: dict, engine):
    semesters = sorted(cleaned["course_enrollment"]["semester"].dropna().unique().tolist())
    with engine.begin() as conn:
        for s in semesters:
            conn.execute(text("""
                INSERT INTO dim_semester (semester_number, academic_year)
                SELECT :s, NULL
                WHERE NOT EXISTS (
                    SELECT 1 FROM dim_semester WHERE semester_number = :s
                )
            """), {"s": int(s)})


def load_dim_course(cleaned: dict, engine):
    courses = cleaned["course_enrollment"][["course_id", "course_name", "department"]].drop_duplicates()
    with engine.begin() as conn:
        for _, row in courses.iterrows():
            conn.execute(text("""
                INSERT INTO dim_course (course_id, course_name, department)
                SELECT :cid, :cname, :dept
                WHERE NOT EXISTS (
                    SELECT 1 FROM dim_course WHERE course_id = :cid
                )
            """), {"cid": row["course_id"], "cname": row["course_name"], "dept": row["department"]})


def load_dim_student_scd2(cleaned: dict, engine):
    """
    Implements SCD Type 2 for dim_student:
    - New student_id -> insert a fresh current row.
    - Existing student_id whose tracked attributes changed
      (here: department) -> expire old row, insert new row.
    - Existing student_id with no change -> no-op.
    """
    students = cleaned["students"]
    today = date.today().isoformat()

    with engine.begin() as conn:
        for _, row in students.iterrows():
            existing = conn.execute(text("""
                SELECT student_key, department FROM dim_student
                WHERE student_id = :sid AND is_current = TRUE
            """), {"sid": row["student_id"]}).fetchone()

            if existing is None:
                conn.execute(text("""
                    INSERT INTO dim_student
                        (student_id, student_name, gender, date_of_birth, department,
                         admission_year, entrance_score_band, effective_date, expiry_date, is_current)
                    VALUES
                        (:sid, :name, :gender, :dob, :dept, :ayear, :band, :eff, NULL, TRUE)
                """), {
                    "sid": row["student_id"], "name": row["name"], "gender": row["gender"],
                    "dob": None if pd.isna(row["date_of_birth"]) else str(row["date_of_birth"].date()),
                    "dept": row["department"],
                    "ayear": None if pd.isna(row["admission_year"]) else int(row["admission_year"]),
                    "band": row.get("entrance_score_band"), "eff": today,
                })
            elif existing.department != row["department"]:
                # SCD Type 2: expire old, insert new version
                conn.execute(text("""
                    UPDATE dim_student SET is_current = FALSE, expiry_date = :today
                    WHERE student_key = :key
                """), {"today": today, "key": existing.student_key})
                conn.execute(text("""
                    INSERT INTO dim_student
                        (student_id, student_name, gender, date_of_birth, department,
                         admission_year, entrance_score_band, effective_date, expiry_date, is_current)
                    VALUES
                        (:sid, :name, :gender, :dob, :dept, :ayear, :band, :eff, NULL, TRUE)
                """), {
                    "sid": row["student_id"], "name": row["name"], "gender": row["gender"],
                    "dob": None if pd.isna(row["date_of_birth"]) else str(row["date_of_birth"].date()),
                    "dept": row["department"],
                    "ayear": None if pd.isna(row["admission_year"]) else int(row["admission_year"]),
                    "band": row.get("entrance_score_band"), "eff": today,
                })
            # else: no change, leave the current row as-is
    logger.info("dim_student SCD Type 2 load complete (%d source rows evaluated)", len(students))


# ----------------------------------------------------------------
# Fact loads (resolve surrogate keys, then bulk insert)
# ----------------------------------------------------------------
def _key_maps(engine):
    with engine.connect() as conn:
        student_map = pd.read_sql(
            "SELECT student_key, student_id FROM dim_student WHERE is_current = TRUE", conn
        ).set_index("student_id")["student_key"].to_dict()
        course_map = pd.read_sql(
            "SELECT course_key, course_id FROM dim_course", conn
        ).set_index("course_id")["course_key"].to_dict()
        semester_map = pd.read_sql(
            "SELECT semester_key, semester_number FROM dim_semester", conn
        ).set_index("semester_number")["semester_key"].to_dict()
    return student_map, course_map, semester_map


def load_fact_attendance(cleaned, engine, student_map, course_map, semester_map):
    df = cleaned["attendance"].copy()
    df["student_key"] = df["student_id"].map(student_map)
    df["course_key"] = df["course_id"].map(course_map)
    df["semester_key"] = df["semester"].map(semester_map)
    df = df.dropna(subset=["student_key", "course_key", "semester_key"])
    out = df[["student_key", "course_key", "semester_key",
              "total_classes", "attended_classes", "attendance_percentage"]]
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE fact_attendance"))
        out.to_sql("fact_attendance", conn, if_exists="append", index=False)
    logger.info("Loaded %d rows into fact_attendance", len(out))


def load_fact_assessment(cleaned, engine, student_map, course_map, semester_map):
    df = cleaned["assessments"].copy()
    df["student_key"] = df["student_id"].map(student_map)
    df["course_key"] = df["course_id"].map(course_map)
    df["semester_key"] = df["semester"].map(semester_map)
    df = df.dropna(subset=["student_key", "course_key", "semester_key"])
    out = df[["student_key", "course_key", "semester_key",
              "internal_marks", "assignment_marks", "quiz_marks", "lab_marks", "final_marks"]]
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE fact_assessment"))
        out.to_sql("fact_assessment", conn, if_exists="append", index=False)
    logger.info("Loaded %d rows into fact_assessment", len(out))


def load_fact_lms(cleaned, engine, student_map, course_map, semester_map):
    df = cleaned["lms_activity"].copy()
    df["student_key"] = df["student_id"].map(student_map)
    df["course_key"] = df["course_id"].map(course_map)
    df["semester_key"] = df["semester"].map(semester_map)
    df = df.dropna(subset=["student_key", "course_key", "semester_key"])
    out = df[["student_key", "course_key", "semester_key",
              "login_count", "content_views", "assignment_submission_rate", "average_session_minutes"]]
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE fact_lms_activity"))
        out.to_sql("fact_lms_activity", conn, if_exists="append", index=False)
    logger.info("Loaded %d rows into fact_lms_activity", len(out))


def load_fact_performance(cleaned, engine, student_map, semester_map):
    df = cleaned["academic_performance"].copy()
    df["student_key"] = df["student_id"].map(student_map)
    df["semester_key"] = df["semester"].map(semester_map)
    df = df.dropna(subset=["student_key", "semester_key"])
    out = df[["student_key", "semester_key", "gpa", "cgpa", "backlogs", "pass_fail", "academic_status"]]
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE fact_academic_performance"))
        out.to_sql("fact_academic_performance", conn, if_exists="append", index=False)
    logger.info("Loaded %d rows into fact_academic_performance", len(out))


def load_all(cleaned: dict):
    engine = get_engine()
    load_staging(cleaned, engine)
    load_dim_department(cleaned, engine)
    load_dim_semester(cleaned, engine)
    load_dim_course(cleaned, engine)
    load_dim_student_scd2(cleaned, engine)

    student_map, course_map, semester_map = _key_maps(engine)
    load_fact_attendance(cleaned, engine, student_map, course_map, semester_map)
    load_fact_assessment(cleaned, engine, student_map, course_map, semester_map)
    load_fact_lms(cleaned, engine, student_map, course_map, semester_map)
    load_fact_performance(cleaned, engine, student_map, semester_map)
    logger.info("Warehouse load complete.")
