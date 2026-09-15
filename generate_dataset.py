"""
generate_dataset.py

Generates a realistic SYNTHETIC educational dataset for the
"Educational Data Warehouse and Student Success Analytics" project.

IMPORTANT (Academic Integrity Note):
The dataset produced by this script is entirely synthetic and does NOT
represent real student records from any institution. It exists purely
to demonstrate data warehousing, OLAP and data mining techniques.

Run:
    python generate_dataset.py

Output (in data/raw/):
    students.csv
    attendance.csv
    assessments.csv
    course_enrollment.csv
    lms_activity.csv
    academic_performance.csv
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import date, timedelta

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_STUDENTS = 1200
DEPARTMENTS = ["CSE", "ECE", "MECH", "CIVIL", "IT", "EEE"]
SEMESTERS = [1, 2, 3, 4, 5, 6]
ADMISSION_YEARS = [2021, 2022, 2023, 2024]

FIRST_NAMES = [
    "Aarav", "Vihaan", "Aditya", "Arjun", "Sai", "Krishna", "Ishaan", "Rohan",
    "Ananya", "Diya", "Kavya", "Priya", "Sneha", "Meera", "Riya", "Pooja",
    "Karthik", "Vignesh", "Naveen", "Suresh", "Divya", "Lakshmi", "Aishwarya",
    "Gokul", "Harini", "Dinesh", "Mohan", "Sathya", "Bhavya", "Nithya",
]
LAST_NAMES = [
    "Kumar", "Sharma", "Raj", "Nair", "Iyer", "Reddy", "Pillai", "Menon",
    "Gupta", "Rao", "Krishnan", "Subramaniam", "Murthy", "Varma", "Das",
]

COURSES = {
    "CSE": [("CS301", "Data Structures"), ("CS302", "DBMS"), ("CS303", "Operating Systems"),
            ("CS304", "Computer Networks"), ("CS305", "Data Warehousing and Mining")],
    "ECE": [("EC301", "Signals and Systems"), ("EC302", "Digital Electronics"),
            ("EC303", "Communication Systems"), ("EC304", "VLSI Design"), ("EC305", "Microprocessors")],
    "MECH": [("ME301", "Thermodynamics"), ("ME302", "Fluid Mechanics"),
             ("ME303", "Machine Design"), ("ME304", "Manufacturing Tech"), ("ME305", "Heat Transfer")],
    "CIVIL": [("CE301", "Structural Analysis"), ("CE302", "Geotechnical Eng"),
              ("CE303", "Surveying"), ("CE304", "Concrete Tech"), ("CE305", "Transportation Eng")],
    "IT": [("IT301", "Web Technologies"), ("IT302", "Cloud Computing"),
           ("IT303", "Software Engineering"), ("IT304", "Information Security"), ("IT305", "Mobile Computing")],
    "EEE": [("EE301", "Power Systems"), ("EE302", "Control Systems"),
            ("EE303", "Electrical Machines"), ("EE304", "Power Electronics"), ("EE305", "Circuit Theory")],
}


def random_dob(admission_year):
    # Students are ~18 at admission
    birth_year = admission_year - 18
    start = date(birth_year, 1, 1)
    end = date(birth_year, 12, 28)
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def make_students():
    rows = []
    for i in range(1, NUM_STUDENTS + 1):
        student_id = f"STU{i:05d}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        gender = random.choice(["M", "F"])
        dept = random.choice(DEPARTMENTS)
        admission_year = random.choice(ADMISSION_YEARS)
        dob = random_dob(admission_year)
        # A non-sensitive academic-context attribute: prior academic score band
        # (used only to introduce realistic correlation with performance, not
        # a protected attribute)
        entrance_score_band = random.choice(["HIGH", "MEDIUM", "LOW"])
        rows.append({
            "student_id": student_id,
            "name": name,
            "gender": gender,
            "date_of_birth": dob.isoformat(),
            "department": dept,
            "admission_year": admission_year,
            "entrance_score_band": entrance_score_band,
        })
    return pd.DataFrame(rows)


def band_bias(band):
    """Returns a performance bias multiplier based on entrance score band.
    This creates realistic, learnable correlations for the ML phases."""
    return {"HIGH": 1.15, "MEDIUM": 1.0, "LOW": 0.85}[band]


def make_enrollment_attendance_assessment_lms(students_df):
    enrollment_rows = []
    attendance_rows = []
    assessment_rows = []
    lms_rows = []

    for _, s in students_df.iterrows():
        dept_courses = COURSES[s["department"]]
        bias = band_bias(s["entrance_score_band"])
        # each student takes a random subset of semesters relevant to their admission year
        n_semesters_completed = random.choice([2, 3, 4, 5, 6])
        student_semesters = SEMESTERS[:n_semesters_completed]

        # Assign a latent "engagement" trait per student (drives attendance + LMS + marks together)
        # Calibrated for a realistic, learnable spread across risk categories (not everyone excels).
        engagement = np.clip(np.random.normal(0.5 * bias, 0.22), 0.05, 1.0)

        for sem in student_semesters:
            course_id, course_name = random.choice(dept_courses)
            enrollment_rows.append({
                "student_id": s["student_id"],
                "course_id": course_id,
                "course_name": course_name,
                "department": s["department"],
                "semester": sem,
            })

            # ---- Attendance ----
            total_classes = random.randint(55, 70)
            attendance_pct_target = np.clip(np.random.normal(60 + engagement * 35, 8), 30, 100)
            attended_classes = int(round(total_classes * attendance_pct_target / 100))
            attendance_pct = round(attended_classes / total_classes * 100, 2)
            attendance_rows.append({
                "student_id": s["student_id"],
                "course_id": course_id,
                "semester": sem,
                "total_classes": total_classes,
                "attended_classes": attended_classes,
                "attendance_percentage": attendance_pct,
            })

            # ---- Assessments ---- (correlated with engagement + bias, plus noise)
            base = 30 + engagement * 55
            internal_marks = float(np.clip(np.random.normal(base * 0.9, 9), 0, 50))
            assignment_marks = float(np.clip(np.random.normal(base * 0.45, 7), 0, 25))
            quiz_marks = float(np.clip(np.random.normal(base * 0.27, 5), 0, 15))
            lab_marks = float(np.clip(np.random.normal(base * 0.45, 6), 0, 25))
            final_marks = float(np.clip(np.random.normal(base, 12), 0, 100))
            assessment_rows.append({
                "student_id": s["student_id"],
                "course_id": course_id,
                "semester": sem,
                "internal_marks": round(internal_marks, 2),
                "assignment_marks": round(assignment_marks, 2),
                "quiz_marks": round(quiz_marks, 2),
                "lab_marks": round(lab_marks, 2),
                "final_marks": round(final_marks, 2),
            })

            # ---- LMS activity ----
            login_count = int(np.clip(np.random.normal(engagement * 60, 12), 0, 120))
            content_views = int(np.clip(np.random.normal(engagement * 150, 30), 0, 400))
            submission_rate = float(np.clip(np.random.normal(engagement * 100, 12), 0, 100))
            avg_session_minutes = float(np.clip(np.random.normal(engagement * 40, 10), 2, 90))
            lms_rows.append({
                "student_id": s["student_id"],
                "course_id": course_id,
                "semester": sem,
                "login_count": login_count,
                "content_views": content_views,
                "assignment_submission_rate": round(submission_rate, 2),
                "average_session_minutes": round(avg_session_minutes, 2),
            })

    return (pd.DataFrame(enrollment_rows), pd.DataFrame(attendance_rows),
            pd.DataFrame(assessment_rows), pd.DataFrame(lms_rows))


def make_academic_performance(students_df, assessment_df):
    # Aggregate a semester GPA per student from their assessment records
    perf_rows = []
    grouped = assessment_df.groupby(["student_id", "semester"])
    for (student_id, semester), grp in grouped:
        avg_pct = (grp["internal_marks"].mean() / 50 * 100 * 0.4 +
                   grp["final_marks"].mean() * 0.6)
        # Map percentage to a 10-point GPA scale with noise
        gpa = float(np.clip(avg_pct / 10 + np.random.normal(0, 0.4), 0, 10))
        backlogs = 0
        pass_fail = "PASS"
        if avg_pct < 40:
            pass_fail = "FAIL"
            backlogs = random.randint(1, 3)
        elif avg_pct < 50 and random.random() < 0.3:
            backlogs = 1

        if gpa >= 8.5:
            status = "EXCELLENT"
        elif gpa >= 7:
            status = "GOOD"
        elif gpa >= 5:
            status = "AVERAGE"
        else:
            status = "AT_RISK"

        perf_rows.append({
            "student_id": student_id,
            "semester": semester,
            "gpa": round(gpa, 2),
            "backlogs": backlogs,
            "pass_fail": pass_fail,
            "academic_status": status,
        })

    perf_df = pd.DataFrame(perf_rows)

    # Compute a running CGPA (cumulative average of GPA up to that semester) per student
    perf_df = perf_df.sort_values(["student_id", "semester"])
    perf_df["cgpa"] = (perf_df.groupby("student_id")["gpa"]
                        .expanding().mean().round(2).reset_index(level=0, drop=True))
    return perf_df


def inject_data_quality_issues(students_df, attendance_df, assessment_df):
    """Deliberately injects realistic messiness so the cleaning phase (Phase 6)
    has genuine problems to solve — required for the 'data cleaning' concept."""
    students_df = students_df.copy()
    attendance_df = attendance_df.copy()
    assessment_df = assessment_df.copy()

    # 1) Duplicate a few student rows
    dup_sample = students_df.sample(n=15, random_state=1)
    students_df = pd.concat([students_df, dup_sample], ignore_index=True)

    # 2) Null out a few names / departments
    idx = students_df.sample(n=10, random_state=2).index
    students_df.loc[idx, "name"] = None

    # 3) Invalid attendance values (attended > total, negative values)
    idx = attendance_df.sample(n=20, random_state=3).index
    attendance_df.loc[idx, "attended_classes"] = attendance_df.loc[idx, "total_classes"] + 5

    idx2 = attendance_df.sample(n=10, random_state=4).index
    attendance_df.loc[idx2, "attendance_percentage"] = -1

    # 4) Invalid / out-of-range marks
    idx3 = assessment_df.sample(n=15, random_state=5).index
    assessment_df.loc[idx3, "final_marks"] = 150  # impossible mark

    idx4 = assessment_df.sample(n=15, random_state=6).index
    assessment_df.loc[idx4, "internal_marks"] = -5  # impossible mark

    # 5) Duplicate assessment rows
    dup_assess = assessment_df.sample(n=10, random_state=7)
    assessment_df = pd.concat([assessment_df, dup_assess], ignore_index=True)

    return students_df, attendance_df, assessment_df


def main():
    print("Generating students...")
    students_df = make_students()

    print("Generating enrollment, attendance, assessments, LMS activity...")
    enrollment_df, attendance_df, assessment_df, lms_df = make_enrollment_attendance_assessment_lms(students_df)

    print("Generating academic performance (GPA/CGPA)...")
    performance_df = make_academic_performance(students_df, assessment_df)

    print("Injecting realistic data quality issues (for the cleaning phase)...")
    students_df, attendance_df, assessment_df = inject_data_quality_issues(
        students_df, attendance_df, assessment_df
    )

    students_df.to_csv(os.path.join(OUTPUT_DIR, "students.csv"), index=False)
    enrollment_df.to_csv(os.path.join(OUTPUT_DIR, "course_enrollment.csv"), index=False)
    attendance_df.to_csv(os.path.join(OUTPUT_DIR, "attendance.csv"), index=False)
    assessment_df.to_csv(os.path.join(OUTPUT_DIR, "assessments.csv"), index=False)
    lms_df.to_csv(os.path.join(OUTPUT_DIR, "lms_activity.csv"), index=False)
    performance_df.to_csv(os.path.join(OUTPUT_DIR, "academic_performance.csv"), index=False)

    print("\nDataset generation complete. Files written to:", OUTPUT_DIR)
    print(f"  students.csv             : {len(students_df)} rows")
    print(f"  course_enrollment.csv    : {len(enrollment_df)} rows")
    print(f"  attendance.csv           : {len(attendance_df)} rows")
    print(f"  assessments.csv          : {len(assessment_df)} rows")
    print(f"  lms_activity.csv         : {len(lms_df)} rows")
    print(f"  academic_performance.csv : {len(performance_df)} rows")
    print("\nNOTE: This dataset is synthetically generated for academic demonstration")
    print("and does not represent real student records.")


if __name__ == "__main__":
    main()
