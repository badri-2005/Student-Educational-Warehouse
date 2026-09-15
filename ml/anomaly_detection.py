"""
anomaly_detection.py

Detects unusual academic patterns using Isolation Forest — e.g. a
student with very high attendance but very low marks, or very high
LMS activity but poor performance.

IMPORTANT: an anomaly flag means "statistically unusual combination
of features", NOT "this is a bad student" or a disciplinary signal.
Anomalies deserve a closer human look, not automatic judgement — for
example, they might reflect a student who understands material without
needing much LMS interaction, or data-entry inconsistency.
"""

import os
import json
import logging
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from preprocessing import load_features

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIZ_DIR = os.path.join(PROJECT_ROOT, "visualizations")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(VIZ_DIR, exist_ok=True)

ANOMALY_FEATURES = [
    "attendance_percentage", "final_marks", "login_count",
    "content_views", "assignment_submission_rate",
]


def run_anomaly_detection(contamination: float = 0.05):
    df = load_features()
    X = df[ANOMALY_FEATURES].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso = IsolationForest(contamination=contamination, random_state=42, n_estimators=200)
    df["anomaly_flag"] = iso.fit_predict(X_scaled)          # -1 = anomaly, 1 = normal
    df["anomaly_score"] = iso.decision_function(X_scaled)    # lower = more anomalous
    df["is_anomaly"] = df["anomaly_flag"] == -1

    # Describe *why* flagged rows look unusual, for the dashboard/viva
    def describe(row):
        notes = []
        if row["attendance_percentage"] > 80 and row["final_marks"] < 45:
            notes.append("High attendance but low marks")
        if row["login_count"] > df["login_count"].quantile(0.75) and row["final_marks"] < 45:
            notes.append("High LMS activity but poor performance")
        if row["assignment_submission_rate"] < 30 and row["final_marks"] > 70:
            notes.append("Low submission rate but high marks")
        return "; ".join(notes) if notes else "Unusual combination of features"

    df["anomaly_reason"] = df.apply(lambda r: describe(r) if r["is_anomaly"] else "", axis=1)

    fig, ax = plt.subplots(figsize=(7, 5))
    normal = df[~df["is_anomaly"]]
    anomalous = df[df["is_anomaly"]]
    ax.scatter(normal["attendance_percentage"], normal["final_marks"], alpha=0.4, label="Normal", c="steelblue")
    ax.scatter(anomalous["attendance_percentage"], anomalous["final_marks"], alpha=0.9, label="Anomaly", c="red", marker="x")
    ax.set_xlabel("Attendance %")
    ax.set_ylabel("Final marks")
    ax.set_title("Anomaly Detection: Attendance vs Final Marks")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "anomaly_detection.png"), dpi=120)
    plt.close(fig)

    df.to_csv(os.path.join(PROJECT_ROOT, "data", "processed", "student_anomalies.csv"), index=False)

    with open(os.path.join(MODELS_DIR, "anomaly_results.json"), "w") as f:
        json.dump({
            "contamination": contamination,
            "n_anomalies": int(df["is_anomaly"].sum()),
            "n_total": len(df),
        }, f, indent=2)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result_df = run_anomaly_detection()
    print(f"\nFlagged {result_df['is_anomaly'].sum()} anomalies out of {len(result_df)} students")
    print(result_df[result_df["is_anomaly"]][["student_id", "attendance_percentage", "final_marks", "anomaly_reason"]].head(10))
