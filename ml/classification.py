"""
classification.py

Academic Risk Prediction (NOT a certainty-claiming dropout predictor —
see the limitations note at the bottom of this file and in README.md).

Trains a Decision Tree and a Random Forest to classify each student
into LOW_RISK / MEDIUM_RISK / HIGH_RISK based on engagement and
performance features, evaluates both, and saves the trained models.
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
)

from preprocessing import load_features, NUMERIC_FEATURES

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def prepare_xy(df: pd.DataFrame):
    X = df[NUMERIC_FEATURES].copy()
    y = df["student_risk"].copy()

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns, index=X.index)

    return X_scaled, y_encoded, label_encoder, scaler


def train_and_evaluate():
    df = load_features()
    X, y, label_encoder, scaler = prepare_xy(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    results = {}

    # ---- Decision Tree ----
    dt = DecisionTreeClassifier(max_depth=6, min_samples_leaf=5, random_state=42)
    dt.fit(X_train, y_train)
    dt_pred = dt.predict(X_test)
    results["DecisionTree"] = _metrics(y_test, dt_pred, "DecisionTree")

    # ---- Random Forest ----
    rf = RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=3, random_state=42)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    results["RandomForest"] = _metrics(y_test, rf_pred, "RandomForest")

    # ---- Feature importance (Random Forest) ----
    importance = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    logger.info("Random Forest feature importance:\n%s", importance.to_string())

    # ---- Save models + artifacts ----
    joblib.dump(dt, os.path.join(MODELS_DIR, "decision_tree.joblib"))
    joblib.dump(rf, os.path.join(MODELS_DIR, "random_forest.joblib"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.joblib"))
    joblib.dump(label_encoder, os.path.join(MODELS_DIR, "label_encoder.joblib"))
    importance.to_csv(os.path.join(MODELS_DIR, "feature_importance.csv"))

    with open(os.path.join(MODELS_DIR, "classification_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("\n=== Classification Report: Decision Tree ===")
    print(classification_report(y_test, dt_pred, target_names=label_encoder.classes_))
    print("\n=== Classification Report: Random Forest ===")
    print(classification_report(y_test, rf_pred, target_names=label_encoder.classes_))

    return results, importance


def _metrics(y_test, y_pred, name):
    cm = confusion_matrix(y_test, y_pred)
    return {
        "model": name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_test, y_pred, average="macro")), 4),
        "recall_macro": round(float(recall_score(y_test, y_pred, average="macro")), 4),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro")), 4),
        "confusion_matrix": cm.tolist(),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res, importance = train_and_evaluate()
    print("\n=== Model comparison ===")
    for name, m in res.items():
        print(f"{name}: accuracy={m['accuracy']}, f1_macro={m['f1_macro']}")
    print(
        "\nNOTE: 'student_risk' is an academic-risk indicator derived from current "
        "engagement/performance patterns in synthetic data — it is not a certain "
        "prediction of a real student's future outcome."
    )
