# Educational Data Warehouse and Student Success Analytics

A college capstone project (Data Warehousing and Data Mining subject) that
builds a centralized educational data warehouse and applies OLAP and
machine learning techniques to analyze student performance, segment
students, and flag academic risk.

> **Note on data:** The dataset used in this project is **synthetically
> generated** for academic demonstration only. It does not represent real
> student records from any institution.

## Problem Statement

Colleges collect student data across disconnected systems — attendance
registers, assessment sheets, and LMS logs — making it hard to get a
unified, analysis-ready view of student performance. This project
integrates that data into a single warehouse and layers OLAP + data
mining on top of it to surface actionable insights (at-risk students,
performance trends, engagement patterns).

## Objectives

- Build a star-schema data warehouse integrating student demographics,
  attendance, assessments, LMS activity, and academic performance.
- Implement a repeatable ETL pipeline with data cleaning and SCD Type 2.
- Demonstrate OLAP operations (roll-up, drill-down, slice, dice, pivot).
- Apply classification, clustering, PCA, and anomaly detection to identify
  at-risk students, segment the population, and spot unusual patterns.
- Present all of the above through an interactive dashboard.

## Features

- Synthetic dataset generator (1,200 students, ~4,600 course-semester records)
- Full ETL pipeline (extract → clean/transform → load) with logging
- Star schema warehouse in MySQL 8 with SCD Type 2 on `dim_student`
- OLAP SQL query library (roll-up, drill-down, slice, dice, pivot, aggregates)
- Decision Tree + Random Forest academic risk classification
- K-Means student segmentation (elbow method + silhouette score)
- PCA-based 2D visualization
- Isolation Forest anomaly detection
- 9-page interactive Streamlit dashboard with student search

## Architecture

```
Raw CSV Data → Data Cleaning → ETL Pipeline → Staging Tables →
Data Warehouse (Star Schema) → OLAP Queries → Analytics Layer →
Machine Learning → Streamlit Dashboard
```

## Technologies

| Layer | Tech |
|---|---|
| Language | Python 3 |
| Data processing | Pandas, NumPy |
| ML | Scikit-learn |
| Database | MySQL 8 |
| DB connectivity | SQLAlchemy, PyMySQL |
| Dashboard | Streamlit, Plotly |
| Model persistence | joblib |

## Database Design — Star Schema

**Dimensions:** `dim_student` (SCD Type 2), `dim_course`, `dim_department`,
`dim_semester`, `dim_date`.

**Facts:** `fact_attendance`, `fact_assessment`, `fact_academic_performance`,
`fact_lms_activity` — each at student-course-semester (or student-semester)
grain, linked to dimensions via surrogate keys.

**SCD Type 2:** when a tracked student attribute (e.g. department) changes,
the old `dim_student` row is expired (`is_current = FALSE`, `expiry_date`
set) and a new row is inserted with a new surrogate key — so historical
facts still point at the version of the student that was true at the time.

Full DDL: `database/schema.sql` and `database/staging.sql`.

## ETL Process

1. **Extract** (`etl/extract.py`) — reads the six raw CSVs.
2. **Transform** (`etl/transform.py`) — deduplicates, fills/drops nulls,
   clips out-of-range marks/attendance, recomputes attendance %, and
   prints a before/after data-quality report.
3. **Load** (`etl/load.py`) — loads staging tables, upserts dimensions
   (with SCD Type 2 for `dim_student`), resolves surrogate keys, and
   loads fact tables.

Run the whole pipeline: `python etl/pipeline.py`

## OLAP Operations

See `sql/olap_queries.sql` for roll-up, drill-down, slice, dice, pivot,
and aggregate queries (avg GPA by department, attendance by semester, pass
% by course, at-risk students by department, etc.), each commented with
what it demonstrates. The dashboard's "OLAP Analytics" page also shows
equivalent operations directly on the processed feature table.

## Machine Learning

- **Classification** (`ml/classification.py`) — Decision Tree and Random
  Forest predict `student_risk` (LOW/MEDIUM/HIGH_RISK), evaluated with
  accuracy, precision, recall, F1, and a confusion matrix.
- **Clustering** (`ml/clustering.py`) — K-Means segments students; K is
  chosen via the elbow method and silhouette score, and cluster labels are
  assigned only after inspecting the resulting cluster centers.
- **PCA** (`ml/pca.py`) — reduces the feature set to 2 components for
  visualization.
- **Anomaly Detection** (`ml/anomaly_detection.py`) — Isolation Forest
  flags unusual attendance/marks/LMS-activity combinations.
- **Evaluation** (`ml/evaluate.py`) — runs everything above and prints a
  consolidated model comparison table.

Run everything: `python ml/evaluate.py`

## Installation & Setup

```bash
git clone <your-repo-url>
cd educational-data-warehouse
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1. Database setup

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/staging.sql
```

Copy `.env.example` to `.env` and fill in your MySQL credentials:

```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=edu_dw
DB_USER=root
DB_PASSWORD=your_password_here
```

### 2. Generate the synthetic dataset

```bash
python generate_dataset.py
```

### 3. Run the ETL pipeline (loads MySQL warehouse)

```bash
python etl/pipeline.py
```

### 4. Run the ML pipeline (classification, clustering, PCA, anomaly detection)

```bash
python ml/evaluate.py
```

This also builds `data/processed/student_features.csv` directly from the
cleaned CSVs, so **the ML pipeline and dashboard can run even before MySQL
is set up** — useful for iterating quickly. The ETL step (`pipeline.py`)
is what actually populates the MySQL warehouse for the OLAP SQL queries.

### 5. Run the dashboard

```bash
streamlit run dashboard/app.py
```

## Results (from this generated dataset)

Exact numbers regenerate slightly with reseeding, but on the shipped
dataset (1,200 students):

- Random Forest and Decision Tree both scored highly (>97% accuracy) on
  the risk classification task — see **Limitations** below for why.
- K-Means selected **k = 2** as optimal by silhouette score, separating a
  higher-engagement/higher-GPA group from a lower one.
- PCA's first 2 components captured **~77%** of feature variance.
- Isolation Forest flagged **~5%** of students as anomalous by design
  (contamination parameter).

Run `python ml/evaluate.py` to reproduce/regenerate all of the above.

## Limitations

- **Synthetic data**: results reflect patterns in generated data, not real
  student behavior — treat this as a working demonstration of the pipeline,
  not a validated real-world model.
- **Feature leakage in classification**: `student_risk` is derived directly
  from GPA thresholds, and GPA is itself computed from the same marks used
  as model features (`internal_marks`, `final_marks`, etc.). This is why
  accuracy is very high — the model is largely re-deriving a deterministic
  rule rather than predicting an independent future outcome. In a
  real-world risk model you would use only *prior-period* data (e.g. last
  semester's marks) to predict *this* semester's risk, avoiding this kind
  of leakage.
- **Academic risk indicator, not certainty**: `student_risk` and anomaly
  flags are indicators for further human review, not definitive
  predictions about a student's future.
- **Small K-Means silhouette test range**: only k = 2–7 was tested for
  simplicity; a production system might explore more values or
  alternative clustering algorithms.

## Future Enhancements

- Replace GPA-threshold-derived labels with an independently defined risk
  target to remove feature leakage.
- Add time-series tracking of a student's risk trajectory across
  semesters (using `dim_date` more fully).
- Add authentication/role-based access to the dashboard for faculty use.
- Incorporate real (anonymized) institutional data once available.

## Project Structure

```
educational-data-warehouse/
├── data/{raw,processed}/
├── database/{schema.sql,staging.sql}
├── etl/{extract.py,transform.py,load.py,pipeline.py,db.py}
├── ml/{preprocessing.py,classification.py,clustering.py,pca.py,anomaly_detection.py,evaluate.py}
├── sql/olap_queries.sql
├── dashboard/app.py
├── models/            (trained models + result artifacts, generated)
├── visualizations/    (elbow/silhouette/PCA/anomaly plots, generated)
├── docs/              (abstract, full documentation, viva Q&A, PPT outline)
├── requirements.txt
├── .env.example
├── .gitignore
└── generate_dataset.py
```

## Screenshots

_Add dashboard screenshots here after running `streamlit run dashboard/app.py` locally._

## Team Members

_Add your name/roll number/team members here for submission._
