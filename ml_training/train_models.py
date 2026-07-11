"""
train_models.py
------------------
Trains, evaluates, and saves the three disease risk models: stroke,
diabetes, hypertension.

For each disease:
  1. Load the dataset (real Kaggle CSV if present, else the synthetic
     stand-in from generate_synthetic_datasets.py — same schema either way)
  2. Build a preprocessing + classifier Pipeline
  3. Compare Logistic Regression vs Random Forest via 5-fold
     cross-validated RECALL (not accuracy — see rationale below)
  4. Fit the better model on the full training split
  5. Evaluate on a held-out test set (accuracy, precision, recall,
     F1, ROC-AUC)
  6. Save the fitted Pipeline (preprocessing + model bundled together)
     via joblib, plus a metadata.json with the feature schema and metrics

Why recall over accuracy for model selection: in remote patient
monitoring, a false negative (telling a high-risk patient they're fine)
is far more costly than a false positive (an unnecessary doctor review).
Optimizing for accuracy alone would let the model minimize error by
mostly predicting "low risk" on an imbalanced dataset — recall
explicitly penalizes missed positive cases.

Run with:
    python ml_training/train_models.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.ml.preprocessing import build_preprocessing_pipeline  # noqa: E402

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")
MODELS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "app", "ml", "trained_models")
)
RANDOM_SEED = 42


# ======================================================================
# Per-disease configuration — this is the ONLY place that needs editing
# if a dataset's column names change (e.g., when you swap in real
# Kaggle CSVs, which use these exact column names already).
# ======================================================================
DISEASE_CONFIGS = {
    "stroke": {
        "csv": "stroke_data.csv",
        "target": "stroke",
        "numeric_features": ["age", "avg_glucose_level", "bmi"],
        "categorical_features": [
            "gender", "hypertension", "heart_disease", "ever_married",
            "work_type", "Residence_type", "smoking_status",
        ],
    },
    "diabetes": {
        "csv": "diabetes_data.csv",
        "target": "Outcome",
        "numeric_features": [
            "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
            "Insulin", "BMI", "DiabetesPedigreeFunction", "Age",
        ],
        "categorical_features": [],
    },
    "hypertension": {
        "csv": "hypertension_data.csv",
        "target": "Risk",
        "numeric_features": [
            "age", "cigsPerDay", "totChol", "sysBP", "diaBP",
            "BMI", "heartRate", "glucose",
        ],
        "categorical_features": [
            "sex", "currentSmoker", "BPMeds", "prevalentStroke", "diabetes",
        ],
    },
}


def train_and_evaluate_one(disease: str, config: dict) -> dict:
    print(f"\n{'=' * 60}\n Training model: {disease.upper()}\n{'=' * 60}")

    csv_path = os.path.join(DATASETS_DIR, config["csv"])
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {config['csv']}")

    feature_cols = config["numeric_features"] + config["categorical_features"]
    X = df[feature_cols]
    y = df[config["target"]]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    preprocessor = build_preprocessing_pipeline(
        config["numeric_features"], config["categorical_features"]
    )

    candidates = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=8, class_weight="balanced",
            random_state=RANDOM_SEED,
        ),
    }

    # --- Step 1: 5-fold CV comparison on recall, using the TRAIN split only
    #     (test set stays untouched until final evaluation) ---
    cv_scores = {}
    for name, clf in candidates.items():
        pipe = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", clf)])
        scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="recall")
        cv_scores[name] = scores.mean()
        print(f"  {name:22s} 5-fold CV recall: {scores.mean():.3f} (+/- {scores.std():.3f})")

    best_name = max(cv_scores, key=cv_scores.get)
    print(f"  -> Selected: {best_name} (highest CV recall)")

    # --- Step 2: fit the chosen model on the full training split ---
    final_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", candidates[best_name]),
    ])
    final_pipeline.fit(X_train, y_train)

    # --- Step 3: evaluate on the held-out test set ---
    y_pred = final_pipeline.predict(X_test)
    y_proba = final_pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
    }
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    metrics["confusion_matrix"] = {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}

    print(f"  Test set metrics: {metrics}")

    # --- Step 4: save model + metadata ---
    os.makedirs(MODELS_DIR, exist_ok=True)
    version = f"{disease}_{best_name.split('_')[0]}_v1.0"

    model_path = os.path.join(MODELS_DIR, f"{disease}_model.joblib")
    joblib.dump(final_pipeline, model_path)

    metadata = {
        "disease": disease,
        "model_version": version,
        "algorithm": best_name,
        "cv_recall_scores": {k: round(v, 4) for k, v in cv_scores.items()},
        "test_metrics": metrics,
        "numeric_features": config["numeric_features"],
        "categorical_features": config["categorical_features"],
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_rows": len(X_train),
        "test_rows": len(X_test),
    }
    metadata_path = os.path.join(MODELS_DIR, f"{disease}_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  Saved model  -> {model_path}")
    print(f"  Saved metadata -> {metadata_path}")

    return metadata


def main() -> None:
    all_metadata = {}
    for disease, config in DISEASE_CONFIGS.items():
        all_metadata[disease] = train_and_evaluate_one(disease, config)

    print(f"\n{'=' * 60}\n Training Summary\n{'=' * 60}")
    for disease, meta in all_metadata.items():
        m = meta["test_metrics"]
        print(f"{disease:15s} | algo={meta['algorithm']:20s} | "
              f"recall={m['recall']:.3f} | precision={m['precision']:.3f} | "
              f"roc_auc={m['roc_auc']:.3f}")


if __name__ == "__main__":
    main()
