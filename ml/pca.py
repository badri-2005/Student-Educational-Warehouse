"""
pca.py

Applies Principal Component Analysis to standardized student
performance/engagement features to reduce dimensionality and
visualize student clusters in 2D.

Why PCA here: we have ~10 correlated numeric features (marks,
attendance, LMS activity). PCA compresses them into a small number
of uncorrelated components that capture most of the variance, which
makes it possible to visualize the whole student population on a
single 2D plot and sanity-check that the K-Means clusters are
actually separated in feature space (not just on 2 raw features).
"""

import os
import json
import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from preprocessing import load_features, NUMERIC_FEATURES

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIZ_DIR = os.path.join(PROJECT_ROOT, "visualizations")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(VIZ_DIR, exist_ok=True)


def run_pca():
    df = load_features()
    X = df[NUMERIC_FEATURES].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2, random_state=42)
    components = pca.fit_transform(X_scaled)
    df["pc1"] = components[:, 0]
    df["pc2"] = components[:, 1]

    explained_variance = pca.explained_variance_ratio_
    logger.info("Explained variance ratio: PC1=%.3f, PC2=%.3f, total=%.3f",
                explained_variance[0], explained_variance[1], explained_variance.sum())

    # Try to reuse cluster labels if clustering has already been run
    cluster_path = os.path.join(PROJECT_ROOT, "data", "processed", "student_clusters.csv")
    color_by = None
    if os.path.exists(cluster_path):
        clusters = pd.read_csv(cluster_path)[["student_id", "cluster"]]
        df = df.merge(clusters, on="student_id", how="left")
        color_by = "cluster"
    else:
        color_by = "student_risk"

    fig, ax = plt.subplots(figsize=(7, 5))
    categories = df[color_by].astype("category")
    scatter = ax.scatter(df["pc1"], df["pc2"], c=categories.cat.codes, cmap="viridis", alpha=0.6)
    ax.set_xlabel(f"PC1 ({explained_variance[0]*100:.1f}% variance)")
    ax.set_ylabel(f"PC2 ({explained_variance[1]*100:.1f}% variance)")
    ax.set_title(f"PCA Projection of Students (colored by {color_by})")
    plt.tight_layout()
    plt.savefig(os.path.join(VIZ_DIR, "pca_projection.png"), dpi=120)
    plt.close(fig)

    df.to_csv(os.path.join(PROJECT_ROOT, "data", "processed", "student_pca.csv"), index=False)

    with open(os.path.join(MODELS_DIR, "pca_results.json"), "w") as f:
        json.dump({
            "explained_variance_ratio": explained_variance.tolist(),
            "total_variance_captured": float(explained_variance.sum()),
        }, f, indent=2)

    return df, explained_variance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result_df, var = run_pca()
    print(f"PC1 explains {var[0]*100:.1f}% of variance")
    print(f"PC2 explains {var[1]*100:.1f}% of variance")
    print(f"Total variance captured by 2 components: {var.sum()*100:.1f}%")
