# AI-Integrated Remote Patient Monitoring System

**Final Year Computer Science Project**
Chronic Disease Management for: **Stroke · Diabetes · Hypertension**

## Overview

A production-quality Remote Patient Monitoring (RPM) system that allows
patients with chronic conditions to submit health data remotely while
doctors monitor them in real time. Machine learning models assess risk,
detect deterioration trends, and trigger alerts when clinical thresholds
are crossed.

## Tech Stack

| Layer            | Technology                                  |
|-------------------|----------------------------------------------|
| Frontend          | Streamlit                                    |
| Backend           | Python (OOP, layered architecture)           |
| Database          | MySQL                                        |
| Machine Learning  | scikit-learn, pandas, NumPy, joblib          |
| Visualization     | Plotly, Streamlit charts                     |
| Authentication    | Streamlit + bcrypt password hashing          |

## System Users

- **Administrator** — manages accounts, oversees system-wide analytics
- **Doctor** — monitors assigned patients, reviews AI alerts, adds clinical notes
- **Patient** — submits vitals remotely, views personal trends and AI feedback

## Project Structure

```
rpm-system/
├── app/
│   ├── main.py                 # Streamlit entry point
│   ├── pages/                  # Streamlit multipage UI (role-based)
│   ├── core/                   # config, security, exceptions
│   ├── database/                # connection + repository pattern
│   ├── services/                 # business logic layer
│   ├── ml/                       # trained models + inference pipeline
│   └── utils/                    # validators, visualization helpers
├── ml_training/                  # model training scripts & datasets
├── database/                     # schema.sql
├── tests/                        # pytest test suite
└── docs/                         # project documentation
```

## Setup Instructions

### 1. Clone and create a virtual environment
```bash
git clone <your-repo-url>
cd rpm-system
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# then edit .env with your real MySQL credentials and secret key
```

### 4. Set up the database
```bash
mysql -u root -p < database/schema.sql

# Optional: load sample dev/demo data
mysql -u root -p rpm_system < database/seed_data.sql
```

### 5. Create the first administrator account
```bash
python scripts/bootstrap_admin.py
```

### 6. Run the application
```bash
streamlit run app/main.py
```

## Machine Learning

Three models (stroke, diabetes, hypertension) are trained via:
```bash
python ml_training/notebooks_or_scripts/generate_synthetic_datasets.py  # dev/test data only
python ml_training/train_models.py
```

**⚠️ Important — read before final submission:** this development environment
has no internet access, so the datasets currently in `ml_training/datasets/`
are **synthetically generated** to match the exact column schemas of real
public datasets (see comments in `generate_synthetic_datasets.py` for exact
source links). For your actual submission, download the real datasets and
replace the CSVs with the same filenames — `train_models.py` works unchanged.

## Limitations

- **Feature coverage mismatch**: the standard stroke/diabetes/hypertension
  datasets use features this system doesn't currently collect (BMI requires
  height; smoking status, cholesterol, marital status are not gathered at
  registration or vitals submission). Missing features are imputed with the
  training set's median/mode at inference time — a standard technique, but
  one that reduces prediction reliability compared to a full clinical
  workup. **Future work**: collect height, smoking status, and family
  history at patient registration to close this gap.
- **Synthetic training data**: see the ML Training section above.
- Not a certified medical device — see Disclaimer below.

## Development Status

- [x] Phase 1 — Environment setup & project skeleton
- [x] Phase 2 — MySQL schema design
- [x] Phase 3 — Database connection & repository layer
- [x] Phase 4 — Authentication system
- [x] Phase 5 — Patient module
- [x] Phase 6 — ML training pipeline & risk engine
- [ ] Phase 7 — Doctor module
- [ ] Phase 8 — Admin module
- [ ] Phase 9 — Alerts & recommendation engine
- [ ] Phase 10 — Visualization dashboards
- [ ] Phase 11 — Testing, polish, documentation

## Disclaimer

This is an academic Final Year Project. It is **not** a certified medical
device and should not be used for real clinical decision-making.
