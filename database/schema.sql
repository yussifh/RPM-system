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
DROP TABLE IF EXISTS audit_logs;
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
-- 8. AUDIT_LOGS  (independent tamper-evident action trail)
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
