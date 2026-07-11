"""
preprocessing.py
-------------------
Builds a reusable scikit-learn preprocessing pipeline shared by all
three disease models.

Design decision: rather than writing separate ad-hoc preprocessing
code per disease, this single function builds a ColumnTransformer
given a list of numeric and categorical feature names. This pipeline
is then chained with a classifier into ONE sklearn Pipeline object
that gets saved via joblib — meaning inference-time code never has to
remember "scale this, one-hot-encode that" manually. It's baked into
the saved model artifact.

Critically: the SimpleImputer here is what makes the risk_engine
resilient to missing features at inference time (see Phase 6 design
notes) — any feature our app doesn't collect is passed as NaN and
gets filled with the TRAINING set's median (numeric) or most frequent
value (categorical), rather than crashing or requiring every feature
to be present.
"""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder


def build_preprocessing_pipeline(numeric_features: list[str],
                                  categorical_features: list[str]) -> ColumnTransformer:
    """
    Returns a ColumnTransformer that:
      - Numeric columns: median-imputes missing values, then standardizes
      - Categorical columns: most-frequent-imputes missing values, then one-hot encodes

    handle_unknown="ignore" on the encoder means a category never seen
    during training (e.g., a new work_type value) won't crash inference —
    it's encoded as all-zeros instead.
    """
    numeric_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    return ColumnTransformer(transformers=[
        ("numeric", numeric_pipeline, numeric_features),
        ("categorical", categorical_pipeline, categorical_features),
    ])
