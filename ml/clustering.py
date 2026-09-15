"""
clustering.py

Student segmentation using K-Means on engagement + performance features.
Determines K using the Elbow Method and Silhouette Score, then profiles
each cluster's centers to assign a meaningful, DATA-DRIVEN label
(labels are decided AFTER examining the cluster centers, not assumed
beforehand).
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from preprocessing import load_features

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
VIZ_DIR = os.path.join(PROJECT_ROOT, "visualizations")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(VIZ_DIR, exist_ok=True)

CLUSTER_FEATURES = [
    "attendance_percentage", "gpa", "assignment_submission_rate",
    "login_count", "final_marks",
]


def find_optimal_k(X_scaled, k_range=range(2, 8)):
    inertias, silhouettes = [], []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(list(k_range), inertias, marker="o")
    axes[0].set_title("Elbow Method")
    axes[0].set_xlabel("k")
    axes[0].set_ylabel("Inertia")

    axes[1].plot(list(k_range), silhouettes, marker="o", color="orange")
    axes[1].set_title("Silhouette Score")
    axes[1].set_xlabel("k")
    axes[1].set_ylabel("Score")

    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "kmeans_elbow_silhouette.png"), dpi=120)
    plt.close(fig)

    best_k = list(k_range)[int(np.argmax(silhouettes))]
    logger.info("Silhouette scores per k: %s", dict(zip(k_range, [round(s, 3) for s in silhouettes])))
    logger.info("Selected k=%d (best silhouette score)", best_k)
    return best_k, inertias, silhouettes


def label_clusters(df: pd.DataFrame, cluster_col="cluster") -> dict:
    """Examines cluster centers on the ORIGINAL (unscaled) feature values
    and assigns human-readable labels based on what's actually observed."""
    profile = df.groupby(cluster_col)[CLUSTER_FEATURES].mean()
    overall = df[CLUSTER_FEATURES].mean()

    labels = {}
    for cid, row in profile.iterrows():
        # Simple composite score vs. dataset average
        score = ((row - overall) / overall).mean()
        if score > 0.15:
            labels[cid] = "High-performing, highly engaged"
        elif score < -0.15:
            labels[cid] = "Low-performing, low engagement"
        else:
            labels[cid] = "Moderate-performing, moderately engaged"

    logger.info("Cluster profile (mean feature values):\n%s", profile.to_string())
    logger.info("Cluster labels: %s", labels)
    return labels, profile


def run_clustering():
    df = load_features()
    X = df[CLUSTER_FEATURES].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    best_k, inertias, silhouettes = find_optimal_k(X_scaled)

    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    df["cluster"] = km.fit_predict(X_scaled)

    labels, profile = label_clusters(df)
    df["cluster_label"] = df["cluster"].map(labels)

    # 2D visualization via first two features for simplicity (PCA handled separately)
    fig, ax = plt.subplots(figsize=(7, 5))
    scatter = ax.scatter(df["attendance_percentage"], df["gpa"], c=df["cluster"], cmap="viridis", alpha=0.6)
    ax.set_xlabel("Attendance %")
    ax.set_ylabel("GPA")
    ax.set_title(f"Student Segmentation (K-Means, k={best_k})")
    plt.colorbar(scatter, label="Cluster")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "kmeans_clusters.png"), dpi=120)
    plt.close(fig)

    joblib.dump(km, os.path.join(MODELS_DIR, "kmeans.joblib"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "kmeans_scaler.joblib"))
    df.to_csv(os.path.join(PROJECT_ROOT, "data", "processed", "student_clusters.csv"), index=False)

    with open(os.path.join(MODELS_DIR, "clustering_results.json"), "w") as f:
        json.dump({
            "best_k": best_k,
            "silhouette_scores": {str(k): round(s, 4) for k, s in zip(range(2, 8), silhouettes)},
            "cluster_labels": {str(k): v for k, v in labels.items()},
            "cluster_sizes": df["cluster"].value_counts().to_dict(),
        }, f, indent=2, default=str)

    return df, labels, profile


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result_df, cluster_labels, cluster_profile = run_clustering()
    print("\nCluster sizes:\n", result_df["cluster"].value_counts())
    print("\nCluster labels:", cluster_labels)
