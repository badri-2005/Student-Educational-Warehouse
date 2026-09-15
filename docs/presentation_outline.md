# Presentation Outline (12–15 slides)

**Slide 1 — Title**
Project title, subject (Data Warehousing and Data Mining), your name/roll
number, department, college, guide's name.

**Slide 2 — Problem Statement**
Student data is scattered across attendance registers, mark sheets, and
LMS logs with no unified, historically-accurate view for analysis.

**Slide 3 — Objectives**
Bullet list: build a star-schema warehouse; implement ETL with SCD Type 2;
support OLAP operations; apply classification/clustering/PCA/anomaly
detection; deliver an interactive dashboard.

**Slide 4 — Existing vs Proposed System**
Two columns: Existing (manual, disconnected spreadsheets, no history
tracking, no mining) vs Proposed (centralized warehouse, automated ETL,
OLAP + ML, dashboard).

**Slide 5 — Architecture**
The pipeline diagram: Raw CSVs → Cleaning → ETL → Staging → Warehouse
(star schema) → OLAP → Analytics → ML → Dashboard.

**Slide 6 — Data Warehouse / Star Schema**
Show the dimension/fact table diagram — `dim_student` (highlight SCD Type
2), `dim_course`, `dim_department`, `dim_semester`, `dim_date`, and the
four fact tables.

**Slide 7 — ETL Pipeline**
Extract → Transform (cleaning examples: duplicate removal, invalid
attendance capping, mark range clipping) → Load (staging → dimensions
with SCD2 → facts).

**Slide 8 — OLAP Operations**
One example each of roll-up, drill-down, slice, dice, pivot with a small
sample result table or screenshot.

**Slide 9 — Classification**
Decision Tree + Random Forest for academic risk prediction; show the
model comparison table (accuracy/precision/recall/F1) and mention the
feature-leakage caveat honestly.

**Slide 10 — Clustering + PCA**
Elbow/silhouette chart, chosen k, cluster labels with brief profile, and
the PCA 2D projection plot.

**Slide 11 — Anomaly Detection & Dashboard**
Isolation Forest example (high attendance/low marks case), then a
screenshot of the Streamlit dashboard's Overview page.

**Slide 12 — Results**
Key numbers pulled from `models/full_evaluation_summary.json` after
running the pipeline (don't pre-fill fabricated numbers — regenerate and
paste real ones before presenting).

**Slide 13 — Limitations**
Synthetic data; feature leakage in the risk classifier; indicator-not-
certainty framing for predictions and anomalies.

**Slide 14 — Future Enhancements**
Leakage-free risk target; time-series risk tracking; dashboard
authentication; real anonymized data.

**Slide 15 — Conclusion**
One-paragraph summary tying the warehouse + OLAP + ML + dashboard
together as a coherent, explainable system.
