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
```
*(schema.sql will be added in Phase 2)*

### 5. Run the application
```bash
streamlit run app/main.py
```

## Development Status

- [x] Phase 1 — Environment setup & project skeleton
- [ ] Phase 2 — MySQL schema design
- [ ] Phase 3 — Database connection & repository layer
- [ ] Phase 4 — Authentication system
- [ ] Phase 5 — Patient module
- [ ] Phase 6 — ML training pipeline & risk engine
- [ ] Phase 7 — Doctor module
- [ ] Phase 8 — Admin module
- [ ] Phase 9 — Alerts & recommendation engine
- [ ] Phase 10 — Visualization dashboards
- [ ] Phase 11 — Testing, polish, documentation

## Disclaimer

This is an academic Final Year Project. It is **not** a certified medical
device and should not be used for real clinical decision-making.
