# AI-Integrated Remote Patient Monitoring System

**Final Year Project — Computer Science Department**
**University of Energy and Natural Resources (UENR), Sunyani, Ghana**

---

## Overview

This system enables patients with chronic conditions — stroke, diabetes, and hypertension — to submit health readings remotely while doctors and administrators monitor patient status in real time using AI-driven risk assessment.

The system is built with **Python**, **Streamlit**, **MySQL**, and **scikit-learn**. It is designed as an academic demonstration and is NOT a certified medical device.

---

## Features

### For Patients (10 pages)
- Submit vitals remotely (blood pressure, heart rate, glucose, SpO2, temperature, weight)
- Receive instant AI severity assessment after every submission
- View vitals history with interactive Plotly trend charts
- Download personal health reports as PDF
- Send messages to assigned doctor and view full chat history
- View and confirm booked appointments
- AI-powered Symptom Checker — describe symptoms and get disease risk predictions
- Rate and review assigned doctor
- Receive and manage medication reminders with daily checklist
- View all notifications (alerts, messages, appointments) in one center
- Join teleconsultation (video call) sessions with doctor
- Toggle dark mode and switch between 4 languages (English, Spanish, French, German)

### For Doctors (6 pages)
- View all assigned patients and their latest vitals
- Receive automatic alerts when patient vitals are severe or critical
- Get instant message notifications when patients report symptoms
- Add clinical notes per patient
- Compare risk scores across all assigned patients
- Prescribe medications to patients with PDF export
- Manage weekly availability schedule for appointment booking
- View full conversation threads with patients
- Start and manage teleconsultation (video call) sessions
- View patient ratings and feedback
- Access all notifications in one center

### For Administrators (5 pages)
- Register and manage doctors and patients
- Bulk import patients from CSV files
- Assign patients to doctors
- View system-wide analytics (user counts, alert severity distribution)
- Doctor activity monitoring — per-doctor stats for patients, appointments, notes, alerts
- View full audit log of all system actions
- Deactivate or reactivate user accounts
- View active user sessions and force logout
- Generate comprehensive admin reports (exportable as CSV/PDF)
- Configure system settings (clinic info, vitals thresholds, SMTP, security)

---

## AI & Machine Learning

### Three Disease Prediction Models
| Disease | Algorithm | Features Used |
|---|---|---|
| Stroke | Logistic Regression | Age, glucose, BMI, gender, hypertension, smoking status |
| Diabetes | Logistic Regression | Glucose, blood pressure, BMI, age, insulin, pregnancies |
| Hypertension | Logistic Regression | Systolic/diastolic BP, age, cholesterol, heart rate, BMI |

### AI Symptom Checker
A rule-based symptom-to-disease mapping engine covering 30+ symptoms mapped to stroke, diabetes, and hypertension. When symptoms match, ML models boost the prediction accuracy with personalized risk scores.

### AI Severity Engine (Rule-Based NLP)
A real-time severity detection system that analyses:
- **Vitals thresholds** — clinical rules for BP, glucose, SpO2, heart rate, temperature
- **Symptom text** — 25+ keyword patterns (chest pain, difficulty breathing, palpitations, etc.)
- **Trend analysis** — compares current readings to recent history to detect deterioration

**Severity levels:** Normal → Mild → Moderate → Severe → Critical

When severity is Moderate or higher, the doctor automatically receives a message alert.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| Backend | Python 3.11 |
| Database | MySQL (via XAMPP) |
| ML Models | scikit-learn (LogisticRegression + Pipeline) |
| Data Processing | pandas, NumPy |
| Visualizations | Plotly |
| PDF Generation | fpdf2 |
| Authentication | bcrypt (password hashing) |

---

## Project Structure

```
rpm-system/
├── app/
│   ├── core/               # Config, security, exceptions
│   ├── database/           # Models, repositories, connection
│   │   └── repositories/   # 14 repositories (users, patients, doctors, vitals, etc.)
│   ├── ml/                 # Risk engine, severity engine, trained models
│   ├── pages/              # 22 Streamlit pages (see table below)
│   ├── services/           # Business logic (auth, monitoring, alerts, symptom checker)
│   └── utils/              # PDF generator, prescription generator, translations, CSS theme
├── database/               # SQL schema, seed data, migrations
├── ml_training/            # Model training scripts
├── tests/                  # Unit tests (pytest) — 67 tests
├── scripts/                # Bootstrap admin script
├── retrain_models.py       # Re-trains all 3 ML models
├── run_migrations.py       # Creates new database tables
├── requirements.txt        # Python dependencies
└── .env                    # Environment configuration (not committed to Git)
```

---

## All 22 Pages

| # | Page | Description | Role |
|---|------|-------------|------|
| 1 | Login | Authentication + patient self-registration | All |
| 2 | Admin Dashboard | User/doctor/patient management, bulk import, audit, sessions | Admin |
| 3 | Doctor Dashboard | Patient overview, alerts, vitals, clinical notes | Doctor |
| 4 | Patient Dashboard | Vitals submission, AI predictions, risk trends | Patient |
| 5 | Messages | Send/receive messages between doctor and patient | All |
| 6 | Appointments | Book, confirm, cancel appointments with PDF | All |
| 7 | Reset Password | Password reset via security question | All |
| 8 | Medications | Prescribe, manage, download medications as PDF | All |
| 9 | Patient Profile | View and update personal profile | Patient |
| 10 | Admin Reports | System analytics, export CSV/PDF reports | Admin |
| 11 | Profile Completion | Complete profile after first login | Patient |
| 12 | AI Symptom Checker | Describe symptoms, get disease risk predictions | Patient |
| 13 | Doctor Schedule | Set weekly availability for booking | Doctor |
| 14 | Patient Progress Report | Generate PDF with vitals, meds, appointments | Patient |
| 15 | Medication Reminders | Set reminders, daily checklist, doctor notification | Patient |
| 16 | Vitals Charts | Interactive Plotly charts for all vital signs | Patient |
| 17 | Chat History | Full conversation thread between doctor/patient | All |
| 18 | Notifications | Unified alerts, messages, appointments center | All |
| 19 | Doctor Rating | Patients rate doctors, doctors view feedback | All |
| 20 | Teleconsultation | Video call room management, session notes | Doctor/Patient |
| 21 | System Settings | Clinic info, thresholds, SMTP, security config | Admin |
| 22 | Preferences | Dark mode toggle, language selector (EN/ES/FR/DE) | All |

---

## Database Tables (21 tables)

| Table | Purpose |
|-------|---------|
| users | All user accounts (admin, doctor, patient) |
| doctors | Doctor profiles (specialization, license) |
| patients | Patient profiles (DOB, conditions, assigned doctor) |
| vitals_records | Patient vital sign submissions |
| predictions | ML model prediction results |
| alerts | Auto-generated alerts for severe/critical readings |
| clinical_notes | Doctor notes per patient |
| messages | In-app messaging between users |
| appointments | Appointment bookings |
| medications | Prescribed medications with schedule |
| medication_logs | Medication adherence tracking |
| lifestyle_records | Patient lifestyle data |
| audit_logs | System audit trail |
| active_sessions | User session tracking |
| emergency_notifications | Emergency contact alerts |
| patient_consents | Patient consent records |
| doctor_schedules | Weekly availability for booking |
| password_reset_tokens | Password reset tokens |
| doctor_ratings | Patient ratings and feedback |
| teleconsultations | Video call sessions |
| system_settings | Admin-configurable system settings |

---

## Setup Instructions

### Prerequisites
- Python 3.11
- XAMPP (MySQL)
- VS Code

### STEP 1 — Clone / extract the project
Extract the project to your Desktop.

### STEP 2 — Create the database
1. Open XAMPP and start MySQL
2. Go to `http://localhost/phpmyadmin`
3. Create a new database called `rpm_system`
4. Import `database/schema.sql`
5. Import `database/seed_data.sql`

### STEP 3 — Create new tables (ratings, teleconsultation, settings)
```bash
py -3.11 run_migrations.py
```

### STEP 4 — Configure environment
Create a `.env` file in the `rpm-system` folder:
```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=rpm_system
DB_USER=root
DB_PASSWORD=
APP_ENV=development
APP_SECRET_KEY=mysecretkey123456789abcdef
BCRYPT_ROUNDS=12
SESSION_EXPIRY_MINUTES=60
RISK_THRESHOLD_MEDIUM=0.4
RISK_THRESHOLD_HIGH=0.7
RISK_THRESHOLD_CRITICAL=0.9
```

### STEP 5 — Install dependencies
```bash
cd rpm-system
py -3.11 -m pip install -r requirements.txt --prefer-binary
```

### STEP 6 — Train ML models
```bash
py -3.11 retrain_models.py
```

### STEP 7 — Create admin account
```bash
py -3.11 scripts/bootstrap_admin.py
```

### STEP 8 — Run the app
```bash
py -3.11 -m streamlit run app/main.py
```

### STEP 9 — Open in browser
```
http://localhost:8501
```

---

## Running Tests

```bash
cd rpm-system
py -3.11 -m pytest tests/ -v
```

### Test Coverage
| Test File | What It Tests |
|---|---|
| `test_auth_service.py` | Login, registration, password validation |
| `test_severity_engine.py` | AI severity detection for vitals and symptoms |
| `test_models.py` | Database model parsing (especially chronic_conditions bug fix) |
| `test_project_structure.py` | All required files and folders exist |

**Total: 67 tests — all passing**

---

## User Roles & Default Accounts

| Role | How to Create |
|---|---|
| Admin | Run `scripts/bootstrap_admin.py` |
| Doctor | Log in as Admin → Admin Dashboard → Add Doctor tab |
| Patient | Log in page → Patient Registration tab, OR Admin → Add Patient tab |

---

## Localization

The system supports 4 languages via the Preferences page:
- 🇬🇧 English (default)
- 🇪🇸 Español (Spanish)
- 🇫🇷 Français (French)
- 🇩🇪 Deutsch (German)

---

## Known Limitations

1. This is an academic demonstration — not a certified medical device
2. ML models are trained on synthetic data, not real clinical datasets
3. No real payment processing or SMS notifications
4. Email alerts are configured but not connected to a live SMTP server
5. Teleconsultation uses embedded Jitsi Meet rooms (meet.jit.si) for real video calls — requires an internet connection and for both participants to be on the same network as the app

---

## Author

**Yussif Hamza**
BSc Computer Science — Final Year
University of Energy and Natural Resources (UENR)
Sunyani, Bono Region, Ghana

---

*This project is submitted as a Final Year Project for academic evaluation only.*
