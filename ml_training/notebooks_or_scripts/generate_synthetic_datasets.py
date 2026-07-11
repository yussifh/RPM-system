"""
generate_synthetic_datasets.py
---------------------------------
Generates synthetic training data matching the EXACT column schemas of
three well-known public datasets, since this development environment
has no internet access to download the real ones from Kaggle.

IMPORTANT — READ BEFORE YOUR FINAL SUBMISSION:
This synthetic data is a development/testing stand-in ONLY. For your
actual project submission, download the real datasets and place them
in ml_training/datasets/ with the exact filenames below — train_models.py
will work UNCHANGED on the real data since the column schemas match:

  1. stroke_data.csv
     Source: "Stroke Prediction Dataset" by fedesoriano on Kaggle
     https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset

  2. diabetes_data.csv
     Source: "Pima Indians Diabetes Database"
     https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database

  3. hypertension_data.csv
     Source: Framingham-study-style hypertension risk dataset
     (commonly distributed on Kaggle as "Hypertension Risk Prediction")

The synthetic generator below encodes REALISTIC clinical correlations
(older age + higher BMI/glucose + smoking -> higher risk probability)
so that the training pipeline, evaluation metrics, and model comparison
logic can be properly exercised and demonstrated end-to-end even
without real data.
"""

import os

import numpy as np
import pandas as pd

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")
RANDOM_SEED = 42


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def generate_stroke_dataset(n: int = 4000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Matches fedesoriano's Stroke Prediction Dataset schema exactly."""
    rng = np.random.default_rng(seed)

    age = rng.gamma(shape=6, scale=8, size=n).clip(1, 95)
    hypertension = rng.binomial(1, p=_sigmoid((age - 55) / 12)).astype(int)
    heart_disease = rng.binomial(1, p=_sigmoid((age - 60) / 15)).astype(int)
    avg_glucose_level = rng.normal(100, 35, n).clip(55, 280) + hypertension * 15
    bmi = rng.normal(28, 6, n).clip(14, 55)
    gender = rng.choice(["Male", "Female", "Other"], n, p=[0.42, 0.57, 0.01])
    ever_married = rng.choice(["Yes", "No"], n, p=[0.65, 0.35])
    work_type = rng.choice(
        ["Private", "Self-employed", "Govt_job", "children", "Never_worked"],
        n, p=[0.57, 0.16, 0.13, 0.13, 0.01],
    )
    residence_type = rng.choice(["Urban", "Rural"], n)
    smoking_status = rng.choice(
        ["never smoked", "formerly smoked", "smokes", "Unknown"],
        n, p=[0.37, 0.17, 0.15, 0.31],
    )
    smoking_risk = np.where(smoking_status == "smokes", 1,
                    np.where(smoking_status == "formerly smoked", 0.5, 0))

    # Composite risk score -> probability -> binary outcome (realistic ~5% prevalence)
    risk_logit = (
        0.05 * (age - 45)
        + 1.1 * hypertension
        + 1.3 * heart_disease
        + 0.015 * (avg_glucose_level - 100)
        + 0.03 * (bmi - 25)
        + 0.6 * smoking_risk
        - 6.0
    )
    stroke_prob = _sigmoid(risk_logit)
    stroke = rng.binomial(1, stroke_prob)

    return pd.DataFrame({
        "gender": gender,
        "age": age.round(1),
        "hypertension": hypertension,
        "heart_disease": heart_disease,
        "ever_married": ever_married,
        "work_type": work_type,
        "Residence_type": residence_type,
        "avg_glucose_level": avg_glucose_level.round(2),
        "bmi": bmi.round(1),
        "smoking_status": smoking_status,
        "stroke": stroke,
    })


def generate_diabetes_dataset(n: int = 2000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Matches the Pima Indians Diabetes Database schema exactly."""
    rng = np.random.default_rng(seed + 1)

    age = rng.gamma(shape=5, scale=6, size=n).clip(21, 85)
    pregnancies = rng.poisson(2.2, n).clip(0, 15)
    bmi = rng.normal(31, 7, n).clip(15, 60)
    glucose = rng.normal(115, 30, n).clip(50, 250)
    blood_pressure = rng.normal(72, 12, n).clip(30, 130)
    skin_thickness = rng.normal(21, 10, n).clip(0, 60)
    insulin = rng.normal(85, 90, n).clip(0, 600)
    dpf = rng.gamma(shape=1.5, scale=0.33, size=n).clip(0.05, 2.5)

    risk_logit = (
        0.02 * (age - 33)
        + 0.05 * (bmi - 30)
        + 0.025 * (glucose - 120)
        + 0.5 * dpf
        + 0.08 * pregnancies
        - 1.0
    )
    outcome_prob = _sigmoid(risk_logit)
    outcome = rng.binomial(1, outcome_prob)

    return pd.DataFrame({
        "Pregnancies": pregnancies,
        "Glucose": glucose.round(1),
        "BloodPressure": blood_pressure.round(1),
        "SkinThickness": skin_thickness.round(1),
        "Insulin": insulin.round(1),
        "BMI": bmi.round(1),
        "DiabetesPedigreeFunction": dpf.round(3),
        "Age": age.round(0).astype(int),
        "Outcome": outcome,
    })


def generate_hypertension_dataset(n: int = 3000, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Matches the Framingham-study-style hypertension risk dataset schema."""
    rng = np.random.default_rng(seed + 2)

    age = rng.gamma(shape=6, scale=7.5, size=n).clip(20, 90)
    sex = rng.choice(["M", "F"], n)
    current_smoker = rng.binomial(1, 0.3, n)
    cigs_per_day = np.where(current_smoker == 1, rng.poisson(12, n), 0)
    bp_meds = rng.binomial(1, 0.08, n)
    prevalent_stroke = rng.binomial(1, 0.02, n)
    diabetes = rng.binomial(1, 0.09, n)
    tot_chol = rng.normal(230, 40, n).clip(120, 400)
    sys_bp = rng.normal(128, 20, n).clip(85, 220) + age * 0.15
    dia_bp = rng.normal(82, 12, n).clip(50, 140)
    bmi = rng.normal(27, 5, n).clip(15, 50)
    heart_rate = rng.normal(76, 12, n).clip(45, 140)
    glucose = rng.normal(82, 25, n).clip(40, 300) + diabetes * 40

    risk_logit = (
        0.03 * (age - 50)
        + 0.02 * (sys_bp - 120)
        + 0.02 * (dia_bp - 80)
        + 0.4 * current_smoker
        + 0.03 * (bmi - 25)
        + 0.6 * bp_meds
        - 2.4
    )
    risk_prob = _sigmoid(risk_logit)
    risk = rng.binomial(1, risk_prob)

    return pd.DataFrame({
        "age": age.round(0).astype(int),
        "sex": sex,
        "currentSmoker": current_smoker,
        "cigsPerDay": cigs_per_day,
        "BPMeds": bp_meds,
        "prevalentStroke": prevalent_stroke,
        "diabetes": diabetes,
        "totChol": tot_chol.round(1),
        "sysBP": sys_bp.round(1),
        "diaBP": dia_bp.round(1),
        "BMI": bmi.round(1),
        "heartRate": heart_rate.round(0).astype(int),
        "glucose": glucose.round(1),
        "Risk": risk,
    })


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stroke_df = generate_stroke_dataset()
    diabetes_df = generate_diabetes_dataset()
    hypertension_df = generate_hypertension_dataset()

    stroke_df.to_csv(os.path.join(OUTPUT_DIR, "stroke_data.csv"), index=False)
    diabetes_df.to_csv(os.path.join(OUTPUT_DIR, "diabetes_data.csv"), index=False)
    hypertension_df.to_csv(os.path.join(OUTPUT_DIR, "hypertension_data.csv"), index=False)

    print(f"stroke_data.csv        -> {len(stroke_df)} rows, "
          f"{stroke_df['stroke'].mean():.1%} positive rate")
    print(f"diabetes_data.csv      -> {len(diabetes_df)} rows, "
          f"{diabetes_df['Outcome'].mean():.1%} positive rate")
    print(f"hypertension_data.csv  -> {len(hypertension_df)} rows, "
          f"{hypertension_df['Risk'].mean():.1%} positive rate")


if __name__ == "__main__":
    main()
