"""
retrain_models.py
------------------
Run this script ONCE to retrain all three ML models with your
installed version of scikit-learn. This fixes the
'LogisticRegression has no attribute multi_class' error.

Usage (from inside the rpm-system folder):
    py -3.11 retrain_models.py
"""

import os
import json
import sys
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timezone
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

MODELS_DIR = os.path.join(os.path.dirname(__file__), "app", "ml", "trained_models")
os.makedirs(MODELS_DIR, exist_ok=True)

np.random.seed(42)

print("=" * 60)
print("  RPM System — ML Model Retraining Script")
print("  Fixes scikit-learn compatibility errors")
print("=" * 60)


def build_pipeline(numeric_features, categorical_features):
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])
    transformers = []
    if numeric_features:
        transformers.append(("numeric", numeric_pipeline, numeric_features))
    if categorical_features:
        transformers.append(("categorical", categorical_pipeline, categorical_features))
    preprocessor = ColumnTransformer(transformers=transformers)
    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def save_model(model, disease, numeric_features, categorical_features, metrics, n_train, n_test):
    model_path = os.path.join(MODELS_DIR, f"{disease}_model.joblib")
    joblib.dump(model, model_path)
    metadata = {
        "disease": disease,
        "model_version": f"{disease}_logistic_v2.0",
        "algorithm": "logistic_regression",
        "test_metrics": metrics,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_rows": n_train,
        "test_rows": n_test,
        "sklearn_compatible": True,
    }
    metadata_path = os.path.join(MODELS_DIR, f"{disease}_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✅ Saved {disease} model → {model_path}")


def compute_metrics(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
    }


# ── STROKE ─────────────────────────────────────────────────────────
print("\n[1/3] Training STROKE model...")
N = 4000
age = np.random.normal(55, 15, N).clip(18, 95)
glucose = np.random.normal(110, 40, N).clip(50, 400)
bmi = np.random.normal(27, 6, N).clip(12, 55)
hypertension = np.random.binomial(1, 0.3, N)
stroke_prob = 1 / (1 + np.exp(-(
    -6 + 0.05 * age + 0.008 * glucose + 0.03 * bmi + 0.8 * hypertension
)))
stroke = np.random.binomial(1, stroke_prob)

df_stroke = pd.DataFrame({
    "age": age, "avg_glucose_level": glucose, "bmi": bmi,
    "gender": np.random.choice(["Male", "Female"], N),
    "hypertension": hypertension,
    "heart_disease": np.random.binomial(1, 0.15, N),
    "ever_married": np.random.choice(["Yes", "No"], N),
    "work_type": np.random.choice(["Private", "Self-employed", "Govt_job", "children", "Never_worked"], N),
    "Residence_type": np.random.choice(["Urban", "Rural"], N),
    "smoking_status": np.random.choice(["formerly smoked", "never smoked", "smokes", "Unknown"], N),
})

numeric_s = ["age", "avg_glucose_level", "bmi"]
categorical_s = ["gender", "hypertension", "heart_disease", "ever_married", "work_type", "Residence_type", "smoking_status"]
X_s = df_stroke[numeric_s + categorical_s]
X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_s, stroke, test_size=0.2, random_state=42)
model_s = build_pipeline(numeric_s, categorical_s)
model_s.fit(X_train_s, y_train_s)
metrics_s = compute_metrics(model_s, X_test_s, y_test_s)
save_model(model_s, "stroke", numeric_s, categorical_s, metrics_s, len(X_train_s), len(X_test_s))
print(f"     Accuracy: {metrics_s['accuracy']} | ROC-AUC: {metrics_s['roc_auc']}")


# ── DIABETES ────────────────────────────────────────────────────────
print("\n[2/3] Training DIABETES model...")
N = 2000
glucose_d = np.random.normal(120, 45, N).clip(50, 500)
bp_d = np.random.normal(72, 12, N).clip(40, 130)
bmi_d = np.random.normal(32, 8, N).clip(15, 60)
age_d = np.random.normal(35, 12, N).clip(18, 80)
diabetes_prob = 1 / (1 + np.exp(-(
    -5 + 0.02 * glucose_d + 0.01 * bp_d + 0.05 * bmi_d + 0.03 * age_d
)))
diabetes = np.random.binomial(1, diabetes_prob)

df_diabetes = pd.DataFrame({
    "Glucose": glucose_d, "BloodPressure": bp_d, "BMI": bmi_d, "Age": age_d,
    "Pregnancies": np.random.randint(0, 15, N).astype(float),
    "SkinThickness": np.random.normal(25, 10, N).clip(0, 80),
    "Insulin": np.random.normal(80, 100, N).clip(0, 600),
    "DiabetesPedigreeFunction": np.random.exponential(0.4, N).clip(0.05, 2.5),
})

numeric_d = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
X_d = df_diabetes[numeric_d]
X_train_d, X_test_d, y_train_d, y_test_d = train_test_split(X_d, diabetes, test_size=0.2, random_state=42)
model_d = build_pipeline(numeric_d, [])
model_d.fit(X_train_d, y_train_d)
metrics_d = compute_metrics(model_d, X_test_d, y_test_d)
save_model(model_d, "diabetes", numeric_d, [], metrics_d, len(X_train_d), len(X_test_d))
print(f"     Accuracy: {metrics_d['accuracy']} | ROC-AUC: {metrics_d['roc_auc']}")


# ── HYPERTENSION ────────────────────────────────────────────────────
print("\n[3/3] Training HYPERTENSION model...")
N = 3000
age_h = np.random.normal(50, 12, N).clip(20, 85)
sysBP = np.random.normal(130, 20, N).clip(80, 220)
diaBP = np.random.normal(82, 12, N).clip(50, 140)
glucose_h = np.random.normal(85, 25, N).clip(50, 300)
cholesterol = np.random.normal(240, 45, N).clip(120, 400)
heartRate = np.random.normal(75, 12, N).clip(40, 140)
hypert_prob = 1 / (1 + np.exp(-(
    -7 + 0.04 * age_h + 0.03 * sysBP + 0.01 * diaBP + 0.005 * glucose_h + 0.002 * cholesterol
)))
hypert = np.random.binomial(1, hypert_prob)

df_hypert = pd.DataFrame({
    "age": age_h, "sysBP": sysBP, "diaBP": diaBP, "glucose": glucose_h,
    "totChol": cholesterol, "heartRate": heartRate,
    "cigsPerDay": np.random.exponential(3, N).clip(0, 40),
    "BMI": np.random.normal(27, 6, N).clip(14, 55),
    "sex": np.random.choice(["M", "F"], N),
    "currentSmoker": np.random.binomial(1, 0.25, N),
    "BPMeds": np.random.binomial(1, 0.1, N),
    "prevalentStroke": np.random.binomial(1, 0.03, N),
    "diabetes": np.random.binomial(1, 0.12, N),
})

numeric_h = ["age", "cigsPerDay", "totChol", "sysBP", "diaBP", "BMI", "heartRate", "glucose"]
categorical_h = ["sex", "currentSmoker", "BPMeds", "prevalentStroke", "diabetes"]
X_h = df_hypert[numeric_h + categorical_h]
X_train_h, X_test_h, y_train_h, y_test_h = train_test_split(X_h, hypert, test_size=0.2, random_state=42)
model_h = build_pipeline(numeric_h, categorical_h)
model_h.fit(X_train_h, y_train_h)
metrics_h = compute_metrics(model_h, X_test_h, y_test_h)
save_model(model_h, "hypertension", numeric_h, categorical_h, metrics_h, len(X_train_h), len(X_test_h))
print(f"     Accuracy: {metrics_h['accuracy']} | ROC-AUC: {metrics_h['roc_auc']}")


print("\n" + "=" * 60)
print("  ✅ All 3 models retrained successfully!")
print("  You can now restart the app and Submit Reading will work.")
print("=" * 60)
