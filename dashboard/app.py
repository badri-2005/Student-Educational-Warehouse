"""
app.py

Streamlit dashboard for the Educational Data Warehouse and Student
Success Analytics project.

Run from the project root:
    streamlit run dashboard/app.py

Reads the processed feature/cluster/PCA/anomaly CSVs produced by the
ml/ scripts (run ml/evaluate.py first if these don't exist yet).
"""

import os
import sys
import json
import subprocess

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
VIZ_DIR = os.path.join(PROJECT_ROOT, "visualizations")
FEATURES_PATH = os.path.join(PROCESSED_DIR, "student_features.csv")

st.set_page_config(page_title="Educational Data Warehouse & Student Success Analytics",
                    layout="wide", page_icon="🎓")


# ----------------------------------------------------------------
# Data loading (cached)
# ----------------------------------------------------------------
def ensure_processed_data():
    """Create dashboard artifacts when running on a fresh deployment."""
    if os.path.exists(FEATURES_PATH):
        return None

    try:
        subprocess.run(
            [sys.executable, "generate_dataset.py"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [sys.executable, os.path.join("ml", "evaluate.py")],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        output = error.stderr.strip() or error.stdout.strip()
        return f"The ML pipeline could not create the dashboard data: {output}"
    except OSError as error:
        return f"The ML pipeline could not start: {error}"

    return None


pipeline_error = ensure_processed_data()
if pipeline_error:
    st.error(pipeline_error)
    st.stop()


@st.cache_data
def load_data():
    def read_csv(name):
        path = os.path.join(PROCESSED_DIR, name)
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

    def read_json(name):
        path = os.path.join(MODELS_DIR, name)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    return {
        "features": read_csv("student_features.csv"),
        "clusters": read_csv("student_clusters.csv"),
        "pca": read_csv("student_pca.csv"),
        "anomalies": read_csv("student_anomalies.csv"),
        "classification_results": read_json("classification_results.json"),
        "clustering_results": read_json("clustering_results.json"),
        "model_comparison": read_csv("model_comparison.csv"),
        "feature_importance": read_csv("feature_importance.csv"),
    }


data = load_data()
features_df = data["features"]

if features_df.empty:
    st.error(
        "No processed data was created. Check that the repository contains "
        "generate_dataset.py and the ml directory, then redeploy."
    )
    st.stop()

st.sidebar.title("🎓 Navigation")
page = st.sidebar.radio("Go to", [
    "Overview",
    "Student Performance",
    "Attendance Analytics",
    "Course Analytics",
    "OLAP Analytics",
    "Student Segmentation",
    "Academic Risk Prediction",
    "Anomaly Detection",
    "ML Model Evaluation",
    "Student Search",
])

st.sidebar.markdown("---")
st.sidebar.caption(
    "Dataset is synthetically generated for academic demonstration and does "
    "not represent real student records."
)

# ----------------------------------------------------------------
# Shared filters
# ----------------------------------------------------------------
with st.sidebar:
    st.markdown("### Filters")
    departments = ["All"] + sorted(features_df["department"].dropna().unique().tolist())
    dept_filter = st.selectbox("Department", departments)

filtered = features_df.copy()
if dept_filter != "All":
    filtered = filtered[filtered["department"] == dept_filter]


# ==================================================================
# PAGE: Overview
# ==================================================================
if page == "Overview":
    st.title("Educational Data Warehouse & Student Success Analytics")
    st.caption("Synthetic dataset — academic demonstration only, not real student records.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", len(filtered))
    c2.metric("Avg GPA", f"{filtered['gpa'].mean():.2f}")
    c3.metric("Avg Attendance %", f"{filtered['attendance_percentage'].mean():.1f}%")
    c4.metric("At-Risk Students", int((filtered["student_risk"] == "HIGH_RISK").sum()))

    col1, col2 = st.columns(2)
    with col1:
        dept_gpa = filtered.groupby("department")["gpa"].mean().reset_index()
        fig = px.bar(dept_gpa, x="department", y="gpa", title="Average GPA by Department", color="department")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        risk_counts = filtered["student_risk"].value_counts().reset_index()
        risk_counts.columns = ["student_risk", "count"]
        fig = px.pie(risk_counts, names="student_risk", values="count", title="Risk Distribution",
                     color="student_risk",
                     color_discrete_map={"LOW_RISK": "#2ecc71", "MEDIUM_RISK": "#f1c40f", "HIGH_RISK": "#e74c3c"})
        st.plotly_chart(fig, use_container_width=True)

# ==================================================================
# PAGE: Student Performance
# ==================================================================
elif page == "Student Performance":
    st.title("Student Performance")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(filtered, x="gpa", nbins=30, title="GPA Distribution")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.box(filtered, x="department", y="final_marks", title="Final Marks by Department", color="department")
        st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(filtered, x="internal_marks", y="final_marks", color="student_risk",
                      title="Internal vs Final Marks", hover_data=["student_id"],
                      color_discrete_map={"LOW_RISK": "#2ecc71", "MEDIUM_RISK": "#f1c40f", "HIGH_RISK": "#e74c3c"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Performance table")
    st.dataframe(filtered[["student_id", "department", "gpa", "cgpa", "backlogs", "academic_status"]])

# ==================================================================
# PAGE: Attendance Analytics
# ==================================================================
elif page == "Attendance Analytics":
    st.title("Attendance Analytics")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(filtered, x="attendance_percentage", nbins=30, title="Attendance Distribution")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.scatter(filtered, x="attendance_percentage", y="gpa", color="department",
                          title="Attendance vs GPA")
        st.plotly_chart(fig, use_container_width=True)

    low_attendance = filtered[filtered["attendance_percentage"] < 75]
    st.subheader(f"Students below 75% attendance ({len(low_attendance)})")
    st.dataframe(low_attendance[["student_id", "department", "attendance_percentage", "gpa"]])

# ==================================================================
# PAGE: Course Analytics
# ==================================================================
elif page == "Course Analytics":
    st.title("Course / Department Analytics")

    dept_summary = filtered.groupby("department").agg(
        avg_gpa=("gpa", "mean"),
        avg_attendance=("attendance_percentage", "mean"),
        avg_final_marks=("final_marks", "mean"),
        students=("student_id", "count"),
    ).reset_index().round(2)
    st.dataframe(dept_summary)

    fig = px.bar(dept_summary, x="department", y="avg_final_marks", title="Average Final Marks by Department",
                 color="department")
    st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(filtered, x="assignment_submission_rate", y="final_marks", color="department",
                      title="LMS Submission Rate vs Final Marks")
    st.plotly_chart(fig, use_container_width=True)

# ==================================================================
# PAGE: OLAP Analytics
# ==================================================================
elif page == "OLAP Analytics":
    st.title("OLAP-style Analytics")
    st.caption("Emulating roll-up / slice / dice / pivot operations on the processed feature table "
               "(equivalent SQL versions against the warehouse are in sql/olap_queries.sql).")

    st.subheader("Roll-up: Avg GPA by Department (+ grand total)")
    rollup = filtered.groupby("department")["gpa"].mean().reset_index()
    rollup.loc[len(rollup)] = ["TOTAL (college-wide)", filtered["gpa"].mean()]
    st.dataframe(rollup.round(2))

    st.subheader("Dice: Department + entrance band + attendance < 75%")
    band = st.selectbox("Entrance score band", ["All"] + sorted(filtered["entrance_score_band"].dropna().unique().tolist()))
    diced = filtered[filtered["attendance_percentage"] < 75]
    if band != "All":
        diced = diced[diced["entrance_score_band"] == band]
    st.dataframe(diced[["student_id", "department", "entrance_score_band", "attendance_percentage", "gpa"]])

    st.subheader("Pivot: Avg Final Marks by Department x Risk Category")
    pivot = filtered.pivot_table(index="department", columns="student_risk", values="final_marks", aggfunc="mean").round(2)
    st.dataframe(pivot)

# ==================================================================
# PAGE: Student Segmentation
# ==================================================================
elif page == "Student Segmentation":
    st.title("Student Segmentation (K-Means)")

    clusters_df = data["clusters"]
    if clusters_df.empty:
        st.warning("Run `python ml/clustering.py` (or ml/evaluate.py) first.")
    else:
        if dept_filter != "All":
            clusters_df = clusters_df[clusters_df["department"] == dept_filter]

        c1, c2 = st.columns(2)
        c1.metric("Clusters (k)", data["clustering_results"].get("best_k", "-"))
        c2.metric("Students segmented", len(clusters_df))

        fig = px.scatter(clusters_df, x="attendance_percentage", y="gpa", color="cluster_label",
                          title="Clusters: Attendance vs GPA", hover_data=["student_id"])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Cluster sizes")
        st.bar_chart(clusters_df["cluster_label"].value_counts())

        st.subheader("Elbow method / silhouette score")
        elbow_path = os.path.join(VIZ_DIR, "kmeans_elbow_silhouette.png")
        if os.path.exists(elbow_path):
            st.image(elbow_path)

# ==================================================================
# PAGE: Academic Risk Prediction
# ==================================================================
elif page == "Academic Risk Prediction":
    st.title("Academic Risk Prediction")
    st.info(
        "This is an academic-risk INDICATOR based on current engagement/performance "
        "patterns in synthetic data — not a certain prediction of a real student's future."
    )

    risk_counts = filtered["student_risk"].value_counts().reset_index()
    risk_counts.columns = ["student_risk", "count"]
    fig = px.bar(risk_counts, x="student_risk", y="count", color="student_risk",
                 color_discrete_map={"LOW_RISK": "#2ecc71", "MEDIUM_RISK": "#f1c40f", "HIGH_RISK": "#e74c3c"},
                 title="Risk Category Distribution")
    st.plotly_chart(fig, use_container_width=True)

    fi = data["feature_importance"]
    if not fi.empty:
        fi.columns = ["feature", "importance"]
        fig = px.bar(fi.sort_values("importance"), x="importance", y="feature", orientation="h",
                     title="Feature Importance (Random Forest)")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("At-risk students")
    st.dataframe(filtered[filtered["student_risk"] == "HIGH_RISK"][
        ["student_id", "department", "gpa", "attendance_percentage", "backlogs"]
    ])

# ==================================================================
# PAGE: Anomaly Detection
# ==================================================================
elif page == "Anomaly Detection":
    st.title("Anomaly Detection")
    st.info("An anomaly flag means an unusual COMBINATION of features — it is not automatically "
             "a bad student. Use it as a prompt to look closer, not a verdict.")

    anomalies_df = data["anomalies"]
    if anomalies_df.empty:
        st.warning("Run `python ml/anomaly_detection.py` (or ml/evaluate.py) first.")
    else:
        if dept_filter != "All":
            anomalies_df = anomalies_df[anomalies_df["department"] == dept_filter]

        st.metric("Anomalies flagged", int(anomalies_df["is_anomaly"].sum()))

        fig = px.scatter(anomalies_df, x="attendance_percentage", y="final_marks",
                          color="is_anomaly", title="Anomaly Detection: Attendance vs Final Marks",
                          hover_data=["student_id", "anomaly_reason"])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Flagged students")
        st.dataframe(anomalies_df[anomalies_df["is_anomaly"]][
            ["student_id", "department", "attendance_percentage", "final_marks", "anomaly_reason"]
        ])

# ==================================================================
# PAGE: ML Model Evaluation
# ==================================================================
elif page == "ML Model Evaluation":
    st.title("ML Model Evaluation")

    comp = data["model_comparison"]
    if comp.empty:
        st.warning("Run `python ml/classification.py` (or ml/evaluate.py) first.")
    else:
        st.subheader("Model comparison")
        st.dataframe(comp)

        for model_name, metrics in data["classification_results"].items():
            st.subheader(f"Confusion Matrix — {model_name}")
            cm = metrics["confusion_matrix"]
            fig = go.Figure(data=go.Heatmap(z=cm, colorscale="Blues", showscale=True,
                                             x=["LOW_RISK", "MEDIUM_RISK", "HIGH_RISK"],
                                             y=["LOW_RISK", "MEDIUM_RISK", "HIGH_RISK"]))
            fig.update_layout(xaxis_title="Predicted", yaxis_title="Actual")
            st.plotly_chart(fig, use_container_width=True)

        pca_path = os.path.join(VIZ_DIR, "pca_projection.png")
        if os.path.exists(pca_path):
            st.subheader("PCA Cluster Visualization")
            st.image(pca_path)

# ==================================================================
# PAGE: Student Search
# ==================================================================
elif page == "Student Search":
    st.title("Student Search")

    student_id = st.text_input("Enter Student ID (e.g. STU00001)")
    if student_id:
        row = features_df[features_df["student_id"].str.upper() == student_id.strip().upper()]
        if row.empty:
            st.error("Student not found.")
        else:
            r = row.iloc[0]
            st.subheader(f"{r['student_id']} — {r['department']}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("GPA", f"{r['gpa']:.2f}")
            c2.metric("CGPA", f"{r['cgpa']:.2f}")
            c3.metric("Attendance %", f"{r['attendance_percentage']:.1f}%")
            c4.metric("Risk", r["student_risk"])

            st.write("**LMS Activity**")
            st.write(f"Logins (avg): {r['login_count']:.1f} | Content views (avg): {r['content_views']:.1f} | "
                     f"Submission rate: {r['assignment_submission_rate']:.1f}%")

            clusters_df = data["clusters"]
            if not clusters_df.empty:
                crow = clusters_df[clusters_df["student_id"] == r["student_id"]]
                if not crow.empty:
                    st.write(f"**Cluster:** {crow.iloc[0]['cluster_label']}")

            anomalies_df = data["anomalies"]
            if not anomalies_df.empty:
                arow = anomalies_df[anomalies_df["student_id"] == r["student_id"]]
                if not arow.empty:
                    is_anom = bool(arow.iloc[0]["is_anomaly"])
                    st.write(f"**Anomaly status:** {'⚠️ Flagged — ' + arow.iloc[0]['anomaly_reason'] if is_anom else '✅ Normal'}")
