-- ==============================================================
-- AI-Integrated Remote Patient Monitoring System
-- MySQL Database Schema
-- ==============================================================
-- Run with:  mysql -u root -p < database/schema.sql
--
-- Design notes (see chat for full rationale):
--   * users/doctors/patients uses table inheritance (shared PK)
--   * vitals_records is append-only (immutable clinical history)
--   * predictions is decoupled from vitals_records (derived AI output)
--   * alerts trace back to the prediction that triggered them
--   * audit_logs is independent of business tables
-- ==============================================================

CREATE DATABASE IF NOT EXISTS rpm_system
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE rpm_system;

-- Ensure clean re-runs during development (order matters: children first)
DROP TABLE IF EXISTS active_sessions;
DROP TABLE IF EXISTS doctor_schedules;
DROP TABLE IF EXISTS patient_consents;
DROP TABLE IF EXISTS emergency_notifications;
DROP TABLE IF EXISTS password_reset_tokens;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS medication_logs;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS lifestyle_records;
DROP TABLE IF EXISTS clinical_notes;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS predictions;
DROP TABLE IF EXISTS vitals_records;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS users;


-- ==============================================================
-- 1. USERS  (shared base table for all roles)
-- ==============================================================
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    full_name       VARCHAR(120)        NOT NULL,
    email           VARCHAR(150)        NOT NULL,
    password_hash   VARCHAR(255)        NOT NULL,   -- bcrypt hash, never plaintext
    role            ENUM('admin', 'doctor', 'patient') NOT NULL,
    phone_number    VARCHAR(20)         NULL,
    is_active       BOOLEAN             NOT NULL DEFAULT TRUE,
    created_at      DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP
                                             ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT uq_users_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE INDEX idx_users_role ON users (role);


-- ==============================================================
-- 2. DOCTORS  (extends users where role = 'doctor')
-- ==============================================================
CREATE TABLE doctors (
    user_id         INT PRIMARY KEY,
    specialization  VARCHAR(100)    NULL,
    license_number  VARCHAR(50)     NOT NULL,

    CONSTRAINT fk_doctors_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_doctors_license UNIQUE (license_number)
) ENGINE=InnoDB;


-- ==============================================================
-- 3. PATIENTS  (extends users where role = 'patient')
-- ==============================================================
CREATE TABLE patients (
    user_id             INT PRIMARY KEY,
    date_of_birth       DATE            NOT NULL,
    gender              ENUM('male', 'female', 'other') NOT NULL,
    assigned_doctor_id  INT             NULL,
    chronic_conditions  SET('stroke', 'diabetes', 'hypertension') NOT NULL,
    emergency_contact    VARCHAR(100)   NULL,

    CONSTRAINT fk_patients_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,

    -- RESTRICT: an admin must explicitly reassign patients before a
    -- doctor record can be removed, preventing orphaned patients.
    CONSTRAINT fk_patients_doctor
        FOREIGN KEY (assigned_doctor_id) REFERENCES doctors(user_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_patients_doctor ON patients (assigned_doctor_id);


-- ==============================================================
-- 4. VITALS_RECORDS  (append-only time-series clinical data)
-- ==============================================================
CREATE TABLE vitals_records (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT             NOT NULL,
    recorded_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    systolic_bp     SMALLINT        NULL,   -- mmHg
    diastolic_bp    SMALLINT        NULL,   -- mmHg
    heart_rate      SMALLINT        NULL,   -- bpm
    glucose_level   DECIMAL(6,2)    NULL,   -- mg/dL
    weight_kg       DECIMAL(5,2)    NULL,
    temperature_c   DECIMAL(4,1)    NULL,
    oxygen_saturation SMALLINT      NULL,   -- SpO2 %

    symptoms        TEXT            NULL,   -- free-text patient-reported symptoms
    notes           TEXT            NULL,

    CONSTRAINT fk_vitals_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE,

    -- Sanity-check constraints: reject physiologically impossible values
    -- at the DB layer as a last line of defense (UI validation happens too)
    CONSTRAINT chk_systolic  CHECK (systolic_bp  BETWEEN 40 AND 300),
    CONSTRAINT chk_diastolic CHECK (diastolic_bp BETWEEN 20 AND 200),
    CONSTRAINT chk_hr        CHECK (heart_rate   BETWEEN 20 AND 250),
    CONSTRAINT chk_spo2      CHECK (oxygen_saturation BETWEEN 0 AND 100)
) ENGINE=InnoDB;

-- Most common query: "latest N readings for a patient" -> composite index
CREATE INDEX idx_vitals_patient_time ON vitals_records (patient_id, recorded_at);


-- ==============================================================
-- 5. PREDICTIONS  (derived AI risk output — decoupled from raw vitals)
-- ==============================================================
CREATE TABLE predictions (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT             NOT NULL,
    vitals_id       BIGINT          NOT NULL,
    disease_type    ENUM('stroke', 'diabetes', 'hypertension') NOT NULL,
    risk_score      DECIMAL(5,4)    NOT NULL,   -- probability 0.0000 - 1.0000
    risk_level      ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    model_version   VARCHAR(30)     NOT NULL,   -- e.g. 'stroke_rf_v1.0'
    predicted_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_predictions_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_predictions_vitals
        FOREIGN KEY (vitals_id) REFERENCES vitals_records(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_risk_score CHECK (risk_score BETWEEN 0 AND 1)
) ENGINE=InnoDB;

-- Common query: "latest risk level per disease for this patient"
CREATE INDEX idx_predictions_patient_disease_time
    ON predictions (patient_id, disease_type, predicted_at);


-- ==============================================================
-- 6. ALERTS  (traceable to the prediction that triggered them)
-- ==============================================================
CREATE TABLE alerts (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT             NOT NULL,
    prediction_id   BIGINT          NOT NULL,
    severity        ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    message         VARCHAR(500)    NOT NULL,
    status          ENUM('open', 'acknowledged', 'resolved') NOT NULL DEFAULT 'open',
    acknowledged_by INT             NULL,       -- doctor user_id
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at     DATETIME        NULL,

    CONSTRAINT fk_alerts_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_alerts_prediction
        FOREIGN KEY (prediction_id) REFERENCES predictions(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_alerts_doctor
        FOREIGN KEY (acknowledged_by) REFERENCES doctors(user_id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- Doctor's dashboard queue: "open, high-severity alerts first"
CREATE INDEX idx_alerts_status_severity ON alerts (status, severity);
CREATE INDEX idx_alerts_patient ON alerts (patient_id);


-- ==============================================================
-- 7. CLINICAL_NOTES  (doctor's written observations per patient)
-- ==============================================================
CREATE TABLE clinical_notes (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    doctor_id       INT             NOT NULL,
    patient_id      INT             NOT NULL,
    note            TEXT            NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notes_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctors(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_notes_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_notes_patient_time ON clinical_notes (patient_id, created_at);


-- ==============================================================
-- 8. MEDICATIONS  (prescribed medications per patient)
-- ==============================================================
CREATE TABLE medications (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT             NOT NULL,
    name            VARCHAR(150)    NOT NULL,
    dosage          VARCHAR(50)     NOT NULL,
    frequency       VARCHAR(50)     NOT NULL,
    route           VARCHAR(30)     NOT NULL DEFAULT 'oral',
    start_date      DATE            NOT NULL,
    end_date        DATE            NULL,
    prescribed_by   VARCHAR(100)    NULL,
    notes           TEXT            NULL,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                         ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_medications_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_medications_patient_active ON medications (patient_id, is_active);


-- ==============================================================
-- 9. MEDICATION_LOGS  (daily intake tracking)
-- ==============================================================
CREATE TABLE medication_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    medication_id   INT             NOT NULL,
    patient_id      INT             NOT NULL,
    taken_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    taken           BOOLEAN         NOT NULL DEFAULT TRUE,
    notes           TEXT            NULL,

    CONSTRAINT fk_medlogs_medication
        FOREIGN KEY (medication_id) REFERENCES medications(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_medlogs_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_medlogs_patient_date ON medication_logs (patient_id, taken_at);


-- ==============================================================
-- 10. AUDIT_LOGS  (independent tamper-evident action trail)
-- ==============================================================
CREATE TABLE audit_logs (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT             NULL,   -- NULL = system-generated event
    action          VARCHAR(100)    NOT NULL,   -- e.g. 'LOGIN_SUCCESS', 'VITALS_SUBMITTED'
    details         TEXT            NULL,
    ip_address      VARCHAR(45)     NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_audit_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_audit_user_time ON audit_logs (user_id, created_at);
CREATE INDEX idx_audit_action ON audit_logs (action);


-- ==============================================================
-- 11. APPOINTMENTS  (doctor-patient scheduled visits)
-- ==============================================================
CREATE TABLE appointments (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id           INT             NOT NULL,
    patient_id          INT             NOT NULL,
    appointment_date    DATE            NOT NULL,
    appointment_time    TIME            NOT NULL,
    location            VARCHAR(150)    NOT NULL DEFAULT 'Hospital Clinic',
    reason              TEXT            NULL,
    severity_level      VARCHAR(20)     NOT NULL DEFAULT 'moderate',
    status              VARCHAR(20)     NOT NULL DEFAULT 'scheduled',
    doctor_notes        TEXT            NULL,
    patient_notes       TEXT            NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                             ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_appt_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctors(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_appt_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_appt_doctor_date ON appointments (doctor_id, appointment_date);
CREATE INDEX idx_appt_patient_date ON appointments (patient_id, appointment_date);


-- ==============================================================
-- 12. LIFESTYLE_RECORDS  (BMI, smoking, cholesterol, exercise)
-- ==============================================================
CREATE TABLE lifestyle_records (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    patient_id              INT             NOT NULL,
    recorded_at             DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    height_cm               DECIMAL(5,1)    NULL,
    weight_kg               DECIMAL(5,1)    NULL,
    bmi                     DECIMAL(4,1)    NULL,
    smoking_status          VARCHAR(30)     NULL,
    cigarettes_per_day      INT             NULL,
    alcohol_units_week      INT             NULL,
    total_cholesterol       DECIMAL(5,1)    NULL,
    hdl_cholesterol         DECIMAL(5,1)    NULL,
    ldl_cholesterol         DECIMAL(5,1)    NULL,
    exercise_minutes_week   INT             NULL,
    activity_level          VARCHAR(20)     NULL,
    diet_type               VARCHAR(50)     NULL,
    notes                   TEXT            NULL,

    CONSTRAINT fk_lifestyle_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_lifestyle_patient_time ON lifestyle_records (patient_id, recorded_at);


-- ==============================================================
-- 13. MESSAGES  (patient-doctor communication)
-- ==============================================================
CREATE TABLE messages (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    sender_id       INT             NOT NULL,
    receiver_id     INT             NOT NULL,
    subject         VARCHAR(200)    NOT NULL,
    body            TEXT            NOT NULL,
    is_read         BOOLEAN         NOT NULL DEFAULT FALSE,
    sent_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_msg_sender
        FOREIGN KEY (sender_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_msg_receiver
        FOREIGN KEY (receiver_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_msg_receiver_read ON messages (receiver_id, is_read);
CREATE INDEX idx_msg_sender ON messages (sender_id);


-- ==============================================================
-- 14. PASSWORD_RESET_TOKENS  (OTP-based password reset)
-- ==============================================================
CREATE TABLE password_reset_tokens (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    token       VARCHAR(64)     NOT NULL,
    expires_at  DATETIME        NOT NULL,
    used        BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_prt_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_prt_token UNIQUE (token)
) ENGINE=InnoDB;

CREATE INDEX idx_prt_user ON password_reset_tokens (user_id);


-- ==============================================================
-- 15. EMERGENCY_NOTIFICATIONS  (emergency contact alerts)
-- ==============================================================
CREATE TABLE emergency_notifications (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_id          INT             NOT NULL,
    emergency_contact   VARCHAR(100)    NOT NULL,
    severity            VARCHAR(20)     NOT NULL,
    message             TEXT            NOT NULL,
    vital_snapshot      TEXT            NULL,
    notification_type   VARCHAR(30)     NOT NULL DEFAULT 'sms',
    status              VARCHAR(20)     NOT NULL DEFAULT 'pending',
    sent_at             DATETIME        NULL,
    acknowledged_at     DATETIME        NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_emerg_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_emerg_patient_time ON emergency_notifications (patient_id, created_at);
CREATE INDEX idx_emerg_status ON emergency_notifications (status);


-- ==============================================================
-- 16. PATIENT_CONSENTS  (consent tracking for monitoring)
-- ==============================================================
CREATE TABLE patient_consents (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_id          INT             NOT NULL,
    consent_type        VARCHAR(50)     NOT NULL DEFAULT 'monitoring',
    consent_given       BOOLEAN         NOT NULL DEFAULT FALSE,
    consent_text        TEXT            NULL,
    ip_address          VARCHAR(45)     NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                         ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_consent_patient
        FOREIGN KEY (patient_id) REFERENCES patients(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_consent_patient ON patient_consents (patient_id, consent_type);


-- ==============================================================
-- 17. DOCTOR_SCHEDULES  (available booking hours)
-- ==============================================================
CREATE TABLE doctor_schedules (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id           INT             NOT NULL,
    day_of_week         TINYINT         NOT NULL COMMENT '0=Monday, 6=Sunday',
    start_time          TIME            NOT NULL,
    end_time            TIME            NOT NULL,
    slot_duration_min   INT             NOT NULL DEFAULT 30,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_schedule_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctors(user_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_day_range CHECK (day_of_week BETWEEN 0 AND 6),
    CONSTRAINT chk_time_range CHECK (end_time > start_time)
) ENGINE=InnoDB;

CREATE INDEX idx_schedule_doctor_day ON doctor_schedules (doctor_id, day_of_week);


-- ==============================================================
-- 18. ACTIVE_SESSIONS  (session tracking for management)
-- ==============================================================
CREATE TABLE active_sessions (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT             NOT NULL,
    session_token       VARCHAR(128)    NOT NULL,
    ip_address          VARCHAR(45)     NULL,
    user_agent          VARCHAR(255)    NULL,
    login_at            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_session_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT uq_session_token UNIQUE (session_token)
) ENGINE=InnoDB;

CREATE INDEX idx_session_user ON active_sessions (user_id, is_active);


-- ==============================================================
-- 19. DOCTOR_RATINGS  (patient feedback after appointments)
-- ==============================================================
CREATE TABLE doctor_ratings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_user_id     INT             NOT NULL,
    doctor_user_id      INT             NOT NULL,
    appointment_id      INT             NULL,
    rating              TINYINT         NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment             TEXT            NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rating_patient
        FOREIGN KEY (patient_user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_rating_doctor
        FOREIGN KEY (doctor_user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_rating_appointment
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_rating_doctor ON doctor_ratings (doctor_user_id);
CREATE INDEX idx_rating_patient ON doctor_ratings (patient_user_id);

-- ==============================================================
-- 20. TELECONSULTATIONS  (video call sessions)
-- ==============================================================
CREATE TABLE teleconsultations (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_user_id     INT             NOT NULL,
    doctor_user_id      INT             NOT NULL,
    appointment_id      INT             NULL,
    status              ENUM('scheduled','in_progress','completed','cancelled')
                                        NOT NULL DEFAULT 'scheduled',
    room_id             VARCHAR(64)     NOT NULL,
    started_at          DATETIME        NULL,
    ended_at            DATETIME        NULL,
    notes               TEXT            NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_tele_patient
        FOREIGN KEY (patient_user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_tele_doctor
        FOREIGN KEY (doctor_user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_tele_appointment
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        ON DELETE SET NULL,
    CONSTRAINT uq_tele_room UNIQUE (room_id)
) ENGINE=InnoDB;

CREATE INDEX idx_tele_doctor ON teleconsultations (doctor_user_id);
CREATE INDEX idx_tele_patient ON teleconsultations (patient_user_id);

-- ==============================================================
-- 21. SYSTEM_SETTINGS  (admin-configurable key-value pairs)
-- ==============================================================
CREATE TABLE system_settings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    setting_key         VARCHAR(100)    NOT NULL,
    setting_value       TEXT            NULL,
    description         VARCHAR(255)    NULL,
    updated_by          INT             NULL,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_settings_user
        FOREIGN KEY (updated_by) REFERENCES users(id)
        ON DELETE SET NULL,
    CONSTRAINT uq_setting_key UNIQUE (setting_key)
) ENGINE=InnoDB;
