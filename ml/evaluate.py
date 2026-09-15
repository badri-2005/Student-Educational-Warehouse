"""
evaluate.py

Runs classification, clustering, PCA and anomaly detection in sequence
and prints/saves a consolidated model comparison table, exactly as
computed from the generated dataset (no fabricated numbers).
"""

import os
import json
import logging
import pandas as pd

import classification
import clustering
import pca as pca_module
import anomaly_detection

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")


def run_all():
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("1) CLASSIFICATION (Decision Tree vs Random Forest)")
    print("=" * 60)
    class_results, importance = classification.train_and_evaluate()

    print("\n" + "=" * 60)
    print("2) K-MEANS CLUSTERING")
    print("=" * 60)
    cluster_df, cluster_labels, cluster_profile = clustering.run_clustering()

    print("\n" + "=" * 60)
    print("3) PCA")
    print("=" * 60)
    pca_df, variance = pca_module.run_pca()

    print("\n" + "=" * 60)
    print("4) ANOMALY DETECTION")
    print("=" * 60)
    anomaly_df = anomaly_detection.run_anomaly_detection()

    # ---- Consolidated comparison table ----
    comparison = pd.DataFrame([
        {
            "Model": name,
            "Accuracy": m["accuracy"],
            "Precision (macro)": m["precision_macro"],
            "Recall (macro)": m["recall_macro"],
            "F1 Score (macro)": m["f1_macro"],
        }
        for name, m in class_results.items()
    ])

    print("\n" + "=" * 60)
    print("MODEL COMPARISON TABLE")
    print("=" * 60)
    print(comparison.to_string(index=False))

    better = comparison.loc[comparison["F1 Score (macro)"].idxmax(), "Model"]
    print(f"\nBetter performing model on this dataset: {better}")
    print(
        "Random Forest is generally expected to generalize better than a single "
        "Decision Tree because it averages many de-correlated trees, reducing "
        "variance/overfitting — though on a clean synthetic dataset a single "
        "tree can sometimes match it."
    )

    comparison.to_csv(os.path.join(MODELS_DIR, "model_comparison.csv"), index=False)

    summary = {
        "classification": class_results,
        "clustering": {"k": int(cluster_df["cluster"].nunique()), "labels": cluster_labels},
        "pca_variance_explained": variance.tolist(),
        "anomalies_detected": int(anomaly_df["is_anomaly"].sum()),
    }
    with open(os.path.join(MODELS_DIR, "full_evaluation_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nAll artifacts saved to: {MODELS_DIR}")
    return summary


if __name__ == "__main__":
    run_all()
