# Viva Preparation — Questions & Answers

## Data Warehousing Fundamentals

**1. What is a data warehouse?**
A subject-oriented, integrated, time-variant, and non-volatile collection
of data used to support management decision-making and analysis.

**2. Why use a data warehouse instead of querying operational databases directly?**
Operational (OLTP) systems are optimized for fast transactional writes,
not large analytical scans; querying them directly for reporting would
slow down day-to-day operations and often requires joining across
multiple disconnected systems.

**3. OLTP vs OLAP?**
OLTP handles many short read/write transactions (e.g. inserting an
attendance record); OLAP handles complex read-heavy aggregations across
large historical datasets (e.g. average GPA trend over 6 semesters).

**4. What is a star schema?**
A schema with a central fact table connected to denormalized dimension
tables, shaped like a star, optimized for fast aggregation queries.

**5. Fact table vs dimension table?**
Fact tables hold measures (numeric, aggregatable values like marks or
attendance %) and foreign keys; dimension tables hold descriptive
attributes (student name, course name) used to filter/group facts.

**6. What is the "grain" of a fact table?**
The level of detail one row represents — e.g. `fact_attendance`'s grain
is one row per student-course-semester.

**7. What is a surrogate key, and why use one instead of the natural key?**
A warehouse-generated integer key (e.g. `student_key`) independent of the
source system's business key (`student_id`). It allows multiple historical
versions of the same business entity to coexist (needed for SCD Type 2)
and insulates the warehouse from changes to the source key format.

**8. What is SCD (Slowly Changing Dimension) Type 2?**
A technique for preserving dimension history: when a tracked attribute
changes, the old row is expired and a new row is inserted with a new
surrogate key, rather than overwriting the old value.

**9. Why not just overwrite (SCD Type 1) for student department changes?**
Overwriting would corrupt historical reports — e.g. a report on
"average GPA per department last year" would incorrectly attribute a
student's old-department performance to their new department.

**10. What is ETL?**
Extract (read from source), Transform (clean/reshape), Load (write into
the warehouse) — the standard pipeline for populating a data warehouse.

**11. ETL vs ELT?**
ETL transforms data before loading it into the target; ELT loads raw data
first and transforms it inside the target system (common with modern
cloud warehouses that have abundant compute).

**12. What is a staging table and why use one?**
An intermediate landing table holding near-raw data before cleaning, so
the load process can be re-run/debugged without re-reading the original
source files, and so transformation logic doesn't have to happen in-flight.

**13. What data quality issues did you handle, and how?**
Duplicate rows (dropped), missing names (filled with "UNKNOWN"), invalid
attendance (`attended_classes` capped at `total_classes`, percentage
recomputed instead of trusted), and out-of-range marks (clipped to valid
bounds). See `etl/transform.py`.

## OLAP Operations

**14. What is roll-up?** Aggregating data from a lower level of
granularity to a higher one, e.g. student → department → college.

**15. What is drill-down?** The reverse of roll-up — moving from
summarized data to more detailed data, e.g. department → course → student.

**16. What is slice?** Fixing one dimension's value and analyzing across
the remaining dimensions (e.g. only semester = 3).

**17. What is dice?** Filtering on multiple dimension values
simultaneously (department = CSE AND semester = 5 AND attendance < 75%).

**18. What is pivot (rotate)?** Rotating data axes to present a
cross-tabulated view, e.g. courses as rows and semesters as columns showing
average marks.

**19. Why does MySQL not have a native PIVOT keyword, and what did you use instead?**
Conditional aggregation — `AVG(CASE WHEN semester = 1 THEN marks END)` for
each semester, achieving the same cross-tab effect.

## Data Mining / Machine Learning

**20. Why Decision Tree for this task?**
It's simple, interpretable (you can trace exactly why a student was
classified as high-risk), and needs little preprocessing.

**21. Why Random Forest in addition to Decision Tree?**
It averages many de-correlated trees trained on bootstrapped samples,
which typically reduces overfitting/variance compared to a single tree.

**22. What is overfitting, and how did you guard against it?**
A model that fits training data (including its noise) too closely and
generalizes poorly to new data. We used a held-out test split, limited
tree depth/leaf size, and macro-averaged metrics.

**23. Why did both models score so highly (>97%) on this dataset?**
Because `student_risk` is derived directly from GPA thresholds, and GPA
is itself computed from the same marks features used to predict risk —
this is feature leakage. It validates the pipeline mechanics but isn't a
result a professor should treat as "the model learned something subtle";
see Limitations in README.md.

**24. Why K-Means for clustering?**
It's simple, fast, and well suited to continuous numeric features like
attendance/marks/engagement, producing clear, interpretable segments.

**25. How did you select K?**
By running K-Means for k = 2–7, plotting inertia (elbow method) and
computing the silhouette score for each k, then picking the k with the
best silhouette score.

**26. What is the elbow method?**
Plotting within-cluster sum of squares (inertia) against k and looking
for the point where adding more clusters stops meaningfully reducing
inertia — the "elbow" of the curve.

**27. What is a silhouette score?**
A measure (-1 to 1) of how well-separated clusters are — how close each
point is to its own cluster vs. the nearest other cluster. Higher is better.

**28. Why did you label clusters only after looking at the data?**
To avoid confirmation bias — assuming labels beforehand risks fitting the
narrative to preconceptions rather than what the data actually shows.

**29. What is PCA and why did you use it?**
Principal Component Analysis is a dimensionality-reduction technique that
projects correlated features onto a smaller number of uncorrelated
components capturing maximum variance — used here to visualize ~10
features on a single 2D scatter plot.

**30. Why standardize features before PCA/K-Means/classification?**
These algorithms are distance- or variance-based; features on different
scales (e.g. `login_count` in tens vs `gpa` in single digits) would
otherwise dominate the result purely due to scale, not actual importance.

**31. What is anomaly detection and why Isolation Forest?**
Identifying data points that don't fit typical patterns. Isolation Forest
is efficient on tabular data, doesn't require a distance metric, and
isolates anomalies by how few random splits it takes to separate them
from the rest of the data.

**32. Why can't an anomaly be treated as automatically "bad"?**
It only means "statistically unusual combination of features" — e.g. a
student with high engagement but low marks might be struggling with test
anxiety, not lack of effort. It's a prompt for human review, not a verdict.

**33. What is precision?**
Of everything predicted positive (e.g. predicted HIGH_RISK), the fraction
that was actually positive.

**34. What is recall?**
Of everything that was actually positive, the fraction the model
correctly identified.

**35. What is F1-score?**
The harmonic mean of precision and recall — a single number balancing
both, useful when class sizes are imbalanced.

**36. Why is accuracy sometimes misleading?**
With imbalanced classes (e.g. few HIGH_RISK students), a model that
always predicts the majority class can still show high accuracy while
being useless for the minority class — precision/recall/F1 per class
expose this.

**37. How does your system identify at-risk students end-to-end?**
Cleaned attendance/marks/LMS features feed a Decision Tree/Random Forest
trained on `student_risk` (derived from academic status), and the
dashboard surfaces predicted HIGH_RISK students with supporting feature
values for review.

**38. What are the limitations of your ML approach?**
Synthetic data, feature leakage in the classification target (see Q23),
indicator-not-certainty framing, and only a narrow k range explored for
clustering. Documented explicitly in README.md and docs/documentation.md.

**39. What's the difference between classification and clustering here?**
Classification is supervised — it learns from a known `student_risk`
label. Clustering is unsupervised — it groups students by similarity
without being told any "correct" grouping in advance.

**40. Why use joblib to save models?**
It's Python's standard, efficient way to serialize scikit-learn model
objects (including large NumPy arrays inside trees/forests) to disk for
reuse without retraining.

## Architecture / Engineering

**41. Why keep credentials in a `.env` file instead of hardcoding them?**
Security and portability — the same code runs against different
databases/environments without code changes, and credentials never end
up in version control.

**42. Why generate synthetic data instead of scraping/using real student data?**
Real student records are sensitive personal data; using synthetic data
avoids privacy/ethics issues while still demonstrating every technique
realistically.

**43. What would you change to make this production-ready?**
Add authentication, incremental (not full-truncate) fact loads, proper
data validation contracts, CI tests for the ETL, and replace the
leakage-prone risk target with an independently defined one.

**44. Why Streamlit for the dashboard instead of a custom web app?**
It lets a data-focused project build an interactive, filterable dashboard
quickly in pure Python, without needing separate frontend/backend
development for an academic deliverable.

**45. How does the dashboard connect to your data?**
It reads the processed CSVs/JSON artifacts produced by the ML pipeline
(`data/processed/`, `models/`) — decoupling the dashboard from needing a
live DB connection at render time.

**46. Why truncate-and-reload fact tables instead of incremental upserts?**
Simplicity appropriate for a capstone project's scale; a production
system would use incremental/merge loads to avoid reprocessing the whole
warehouse on every run.

**47. What indexes did you add, and why?**
Indexes on foreign key columns in fact tables (`student_key`,
`course_key`) and on `dim_student.student_id`/`is_current`, to keep OLAP
joins and the SCD Type 2 "find current row" lookup fast.

**48. How do you verify the ETL actually worked?**
Row counts logged at each stage, the printed data-quality before/after
report, and spot-checking OLAP queries in `sql/olap_queries.sql` against
expected aggregates.

**49. What was the hardest part of this project?**
(Answer in your own words — e.g. correctly implementing SCD Type 2 so
historical facts stay attributed to the right dimension version, or
avoiding target leakage when defining `student_risk`.)

**50. What did you learn from this project?**
(Answer in your own words — e.g. how warehouse design decisions like
surrogate keys and grain directly shape what OLAP queries are efficient
and correct, and how easy it is to accidentally leak the target into ML
features unless you think carefully about time-ordering.)
