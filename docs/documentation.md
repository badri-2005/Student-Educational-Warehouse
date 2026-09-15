# Project Documentation
## Educational Data Warehouse and Student Success Analytics

---

## ABSTRACT

Educational institutions generate large volumes of data across disconnected
systems — attendance registers, assessment records, and learning
management system (LMS) logs — which makes it difficult to obtain a
unified view of student performance. This project designs and implements
a centralized **educational data warehouse** using a star schema in MySQL,
integrating student demographics, attendance, assessments, LMS activity,
and academic performance. An ETL pipeline extracts, cleans, and loads data
into the warehouse, implementing **Slowly Changing Dimension (SCD) Type 2**
to preserve student history. OLAP operations (roll-up, drill-down, slice,
dice, pivot) support multi-dimensional analysis at the student, course,
and semester level. Data mining techniques — Decision Tree and Random
Forest classification, K-Means clustering, Principal Component Analysis
(PCA), and Isolation Forest anomaly detection — are applied to identify
academic risk patterns, segment students by engagement/performance, and
flag unusual academic behavior. Results are presented through an
interactive Streamlit dashboard. The dataset used is synthetically
generated for academic demonstration and does not represent real student
records.

---

## INTRODUCTION

Modern colleges accumulate data about students from multiple independent
sources. Without integration, this data is hard to analyze holistically —
a professor might see attendance in one register and marks in another
spreadsheet, with no single place to spot a student quietly falling behind
across several signals at once. Data warehousing addresses this by
consolidating data into a subject-oriented, integrated, time-variant
store optimized for analysis (OLAP) rather than transaction processing
(OLTP). Data mining then extracts patterns from that consolidated data
that would not be visible from any single source alone.

---

## PROBLEM STATEMENT

There is no single, queryable, historically-consistent view of a
student's demographic, attendance, assessment, and engagement data that
supports both multi-dimensional reporting and predictive analysis of
academic risk.

---

## OBJECTIVES

1. Design a star-schema data warehouse for educational data.
2. Build an ETL pipeline with cleaning, validation, and SCD Type 2.
3. Implement OLAP operations for multi-level analysis.
4. Apply classification, clustering, PCA, and anomaly detection to
   support academic risk identification and student segmentation.
5. Deliver results through an interactive dashboard.

---

## EXISTING SYSTEM

Most college systems store attendance, marks, and LMS data in separate
modules or spreadsheets with little integration. Reporting is typically
manual (exporting spreadsheets and combining them by hand), there is no
historical tracking of changing student attributes, and there is no
systematic use of data mining to flag at-risk students proactively.

## PROPOSED SYSTEM

A centralized data warehouse consolidates all data sources into a star
schema with proper history tracking (SCD Type 2). An automated ETL
pipeline keeps the warehouse current and clean. OLAP queries give
faculty/administrators fast multi-dimensional views, and machine learning
models surface risk and engagement patterns that would be tedious to spot
manually.

---

## SYSTEM REQUIREMENTS

**Hardware:** Any standard laptop/desktop (4GB+ RAM recommended).
**Software:** Python 3.9+, MySQL 8, pip, a modern web browser (for the
Streamlit dashboard).

## FUNCTIONAL REQUIREMENTS

- Generate/import student, attendance, assessment, LMS, and performance data
- Clean and validate data before loading
- Load data into a star-schema warehouse with history tracking
- Support OLAP queries (roll-up, drill-down, slice, dice, pivot)
- Classify students into risk categories
- Segment students via clustering
- Detect anomalous academic patterns
- Provide an interactive dashboard with student search

## NON-FUNCTIONAL REQUIREMENTS

- Runnable on a normal laptop (no enterprise infrastructure required)
- Reasonable performance for a dataset of ~1,000+ students
- No hardcoded credentials (environment-variable based configuration)
- Understandable, well-commented code suitable for a viva walkthrough

---

## SYSTEM ARCHITECTURE

```
Raw CSV Data → Data Cleaning → ETL Pipeline → Staging Tables →
Data Warehouse (Star Schema) → OLAP Queries → Analytics Layer →
Machine Learning → Streamlit Dashboard
```

Each layer has a single responsibility: raw data is never queried
directly by analytics or ML; it is always cleaned and staged first, then
loaded into a warehouse that acts as the single source of truth for both
OLAP reporting and mining.

---

## DATA WAREHOUSE DESIGN

See `database/schema.sql` for full DDL. Dimensions: `dim_student` (SCD
Type 2), `dim_course`, `dim_department`, `dim_semester`, `dim_date`. Facts:
`fact_attendance`, `fact_assessment`, `fact_academic_performance`,
`fact_lms_activity`.

## STAR SCHEMA DESCRIPTION

The star schema places each fact table at the center, linked to
denormalized dimension tables via surrogate keys. This denormalization
trades some redundancy for much faster, simpler joins during OLAP
aggregation — exactly what's needed for reporting workloads (as opposed
to a normalized OLTP schema optimized for transactional writes).

## ETL PROCESS

**Extract:** read all six raw CSVs into DataFrames.
**Transform:** deduplicate, handle nulls, clip/repair invalid values
(e.g. attended_classes > total_classes, marks outside valid ranges),
recompute derived fields, and produce a before/after data-quality report.
**Load:** load staging tables, then upsert dimensions (SCD Type 2 for
`dim_student`), resolve surrogate keys via lookups, and bulk-load fact
tables.

## SCD TYPE 2 IMPLEMENTATION

When a student's department changes, the existing `dim_student` row is
expired (`is_current = FALSE`, `expiry_date` = today) and a new row is
inserted with a new surrogate key and `is_current = TRUE`. Fact rows
loaded before the change keep referencing the old surrogate key, so
historical reports (e.g. "average GPA by department last semester")
remain accurate even after a student transfers departments.

## OLAP OPERATIONS

- **Roll-up:** aggregate from student → department → college level.
- **Drill-down:** expand department-level figures into course- and
  student-level detail.
- **Slice:** fix one dimension (e.g. semester = 3) and analyze across others.
- **Dice:** filter on multiple dimensions simultaneously (department +
  semester + attendance threshold).
- **Pivot:** cross-tabulate a measure (e.g. average marks) by course and
  semester using conditional aggregation (MySQL has no native PIVOT
  keyword).

## DATA MINING METHODS

### CLASSIFICATION

Decision Tree and Random Forest classifiers predict `student_risk`
(LOW/MEDIUM/HIGH_RISK) from attendance, marks, and LMS engagement
features. Evaluated with accuracy, precision, recall, F1-score, and a
confusion matrix (see Limitations regarding feature leakage in this
particular formulation).

### CLUSTERING

K-Means groups students by engagement and performance similarity. The
number of clusters (k) is chosen using the elbow method (inertia vs. k)
and confirmed with the silhouette score, rather than assumed in advance.
Cluster labels ("High-performing/highly engaged", etc.) are assigned only
after examining the actual feature averages within each cluster.

### PCA

Principal Component Analysis reduces the ~10 correlated numeric features
down to 2 principal components for visualization, retaining a majority of
the original variance while making the whole student population plottable
on a single 2D scatter chart.

### ANOMALY DETECTION

Isolation Forest flags students whose feature combination is statistically
unusual (e.g. high attendance but low marks). An anomaly flag indicates a
pattern worth a closer human look — it is explicitly not a judgment about
student quality.

---

## RESULTS

See `models/full_evaluation_summary.json` and `models/model_comparison.csv`
after running `python ml/evaluate.py` for the exact metrics computed on
the generated dataset (accuracy, precision, recall, F1 for both classifiers;
optimal k and cluster labels; PCA explained variance; anomaly count).
Numbers are not hardcoded here because they are meant to be reproduced by
running the pipeline, per the project's academic-integrity requirement.

## CONCLUSION

This project demonstrates an end-to-end educational analytics pipeline —
from raw data through a properly modeled warehouse with history tracking,
through OLAP analysis, to machine-learning-driven risk identification and
segmentation — all presented through an accessible dashboard. It shows
how data warehousing and data mining concepts combine in a realistic,
explainable system sized appropriately for a college capstone.

## FUTURE ENHANCEMENTS

- Remove feature leakage in the risk classifier by using only prior-period data.
- Track student risk trajectories over time using `dim_date`.
- Add authentication and role-based dashboard access for faculty.
- Replace synthetic data with real, anonymized institutional data.
- Explore additional clustering algorithms (DBSCAN, hierarchical) for comparison.

## REFERENCES

- Kimball, R., & Ross, M. *The Data Warehouse Toolkit* (star schema design, SCD).
- Han, J., Kamber, M., & Pei, J. *Data Mining: Concepts and Techniques*.
- Scikit-learn documentation: https://scikit-learn.org/stable/
- Streamlit documentation: https://docs.streamlit.io/
- MySQL 8 Reference Manual: https://dev.mysql.com/doc/refman/8.0/en/
