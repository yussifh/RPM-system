-- ==============================================================
-- Seed Data — FOR DEVELOPMENT/DEMO PURPOSES ONLY
-- ==============================================================
-- Run AFTER schema.sql:
--   mysql -u root -p rpm_system < database/seed_data.sql
--
-- Credentials (login via 1_Login.py):
--   Admin:   admin@rpm.com          / admin1234
--   Doctor:  doctor@rpm.com         / doctor1234
--   Patient: patient@rpm.com        / patient1234
--
-- Passwords are real bcrypt hashes generated with 12 rounds.
-- ==============================================================

USE rpm_system;

-- --- Admin ---
INSERT INTO users (full_name, email, password_hash, role, phone_number) VALUES
('System Administrator', 'admin@rpm.com', '$2b$12$oqKIOO7hNEpTG74q/s4fcubq2Gbbkj7flHHJVsr7NQtsurqcC5nma', 'admin', '+233 20 000 0001');

-- --- Doctors ---
INSERT INTO users (full_name, email, password_hash, role, phone_number) VALUES
('Dr. Ama Owusu', 'doctor@rpm.com', '$2b$12$JypA5ywKFI39rd/yfZsfouSdTMlHHrObcJv3/X70j6tAB3ZCSgRSe', 'doctor', '+233 24 111 1111'),
('Dr. Kwame Boateng', 'kwame.boateng@rpm-system.local', '$2b$12$JypA5ywKFI39rd/yfZsfouSdTMlHHrObcJv3/X70j6tAB3ZCSgRSe', 'doctor', '+233 24 222 2222');

INSERT INTO doctors (user_id, specialization, license_number) VALUES
((SELECT id FROM users WHERE email = 'doctor@rpm.com'), 'Neurology', 'LIC-1001'),
((SELECT id FROM users WHERE email = 'kwame.boateng@rpm-system.local'), 'Endocrinology', 'LIC-1002');

-- --- Patients ---
INSERT INTO users (full_name, email, password_hash, role, phone_number) VALUES
('John Mensah', 'patient@rpm.com', '$2b$12$qE83RkY6nGFppSzNwnWqwONtxBFB1Loa30D9dtgjnQb/3Zdy3KJmS', 'patient', '+233 24 333 3333'),
('Grace Adjei', 'grace.adjei@rpm-system.local', '$2b$12$qE83RkY6nGFppSzNwnWqwONtxBFB1Loa30D9dtgjnQb/3Zdy3KJmS', 'patient', '+233 24 444 4444');

INSERT INTO patients (user_id, date_of_birth, gender, assigned_doctor_id, chronic_conditions, emergency_contact) VALUES
(
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    '1968-03-14', 'male',
    (SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'),
    'stroke,hypertension',
    'Mrs. Mensah — +233 20 555 5555'
),
(
    (SELECT id FROM users WHERE email = 'grace.adjei@rpm-system.local'),
    '1975-11-02', 'female',
    (SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'),
    'diabetes',
    'Mr. Adjei — +233 20 666 6666'
);

-- --- Sample vitals for John Mensah ---
INSERT INTO vitals_records (patient_id, systolic_bp, diastolic_bp, heart_rate, glucose_level, weight_kg, oxygen_saturation, symptoms)
VALUES
(
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    168, 102, 88, 110.5, 82.3, 96, 'Mild headache, slight dizziness'
);

-- --- Sample vitals for Grace Adjei ---
INSERT INTO vitals_records (patient_id, systolic_bp, diastolic_bp, heart_rate, glucose_level, weight_kg, oxygen_saturation, symptoms)
VALUES
(
    (SELECT id FROM users WHERE email = 'grace.adjei@rpm-system.local'),
    122, 78, 74, 185.0, 68.0, 98, 'Increased thirst, fatigue'
);

-- --- Sample medications for John Mensah (stroke + hypertension) ---
INSERT INTO medications (patient_id, name, dosage, frequency, route, start_date, prescribed_by, notes)
VALUES
(
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    'Lisinopril', '10mg', 'Once daily', 'oral', '2025-01-15',
    'Dr. Ama Owusu', 'Take in the morning. Monitor for dizziness.'
),
(
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    'Aspirin', '81mg', 'Once daily', 'oral', '2025-01-15',
    'Dr. Ama Owusu', 'Low-dose for stroke prevention. Take with food.'
),
(
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    'Atorvastatin', '20mg', 'Every night', 'oral', '2025-02-01',
    'Dr. Ama Owusu', 'Take at bedtime for cholesterol management.'
);

-- --- Sample medications for Grace Adjei (diabetes) ---
INSERT INTO medications (patient_id, name, dosage, frequency, route, start_date, prescribed_by, notes)
VALUES
(
    (SELECT id FROM users WHERE email = 'grace.adjei@rpm-system.local'),
    'Metformin', '500mg', 'Twice daily', 'oral', '2025-01-20',
    'Dr. Kwame Boateng', 'Take with meals to reduce stomach upset.'
),
(
    (SELECT id FROM users WHERE email = 'grace.adjei@rpm-system.local'),
    'Glipizide', '5mg', 'Once daily', 'oral', '2025-03-01',
    'Dr. Kwame Boateng', 'Take 30 minutes before breakfast.'
);

-- --- Sample medication logs for John Mensah (last 7 days) ---
INSERT INTO medication_logs (medication_id, patient_id, taken_at, taken)
SELECT m.id, m.patient_id, CURDATE() - INTERVAL d.n DAY, IF(RAND() > 0.15, TRUE, FALSE)
FROM medications m
CROSS JOIN (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
    UNION SELECT 5 UNION SELECT 6 UNION SELECT 7
) d
WHERE m.patient_id = (SELECT id FROM users WHERE email = 'patient@rpm.com')
  AND m.is_active = TRUE;

-- --- Sample medication logs for Grace Adjei (last 7 days) ---
INSERT INTO medication_logs (medication_id, patient_id, taken_at, taken)
SELECT m.id, m.patient_id, CURDATE() - INTERVAL d.n DAY, IF(RAND() > 0.2, TRUE, FALSE)
FROM medications m
CROSS JOIN (
    SELECT 1 AS n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
    UNION SELECT 5 UNION SELECT 6 UNION SELECT 7
) d
WHERE m.patient_id = (SELECT id FROM users WHERE email = 'grace.adjei@rpm-system.local')
  AND m.is_active = TRUE;

-- --- Sample lifestyle records for John Mensah ---
INSERT INTO lifestyle_records (patient_id, height_cm, weight_kg, bmi, smoking_status, cigarettes_per_day, total_cholesterol, hdl_cholesterol, ldl_cholesterol, exercise_minutes_week, activity_level, diet_type)
VALUES
(
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    175.0, 82.3, 26.9, 'formerly smoked', 0, 210.0, 42.0, 140.0, 90, 'light', 'low-salt'
),
(
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    175.0, 80.5, 26.3, 'never smoked', 0, 198.0, 45.0, 130.0, 120, 'moderate', 'low-salt, low-sugar'
);

-- --- Sample lifestyle records for Grace Adjei ---
INSERT INTO lifestyle_records (patient_id, height_cm, weight_kg, bmi, smoking_status, total_cholesterol, hdl_cholesterol, ldl_cholesterol, exercise_minutes_week, activity_level, diet_type)
VALUES
(
    (SELECT id FROM users WHERE email = 'grace.adjei@rpm-system.local'),
    162.0, 68.0, 25.9, 'never smoked', 220.0, 50.0, 150.0, 60, 'sedentary', 'low-sugar'
);

-- --- Sample messages ---
INSERT INTO messages (sender_id, receiver_id, subject, body, is_read, sent_at)
VALUES
(
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    (SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'),
    'Blood pressure concern',
    'Dr. Owusu, my blood pressure has been higher than usual the past few days. Should I adjust my medication?',
    TRUE, NOW() - INTERVAL 3 DAY
),
(
    (SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'),
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    'Re: Blood pressure concern',
    'Please continue taking Lisinopril as prescribed. Monitor twice daily and let me know if it stays above 150/100.',
    TRUE, NOW() - INTERVAL 2 DAY
),
(
    (SELECT id FROM users WHERE email = 'grace.adjei@rpm-system.local'),
    (SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'),
    'Glucose readings question',
    'Dr. Boateng, my fasting glucose has been around 160 lately. Is that within the target range?',
    FALSE, NOW() - INTERVAL 1 DAY
);

-- --- Sample appointments ---
INSERT INTO appointments (doctor_id, patient_id, appointment_date, appointment_time, location, reason, severity_level, status)
VALUES
(
    (SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'),
    (SELECT id FROM users WHERE email = 'patient@rpm.com'),
    DATE_ADD(CURDATE(), INTERVAL 7 DAY), '10:00:00',
    'RPM Clinic, Room 3', 'Follow-up: hypertension management', 'moderate', 'scheduled'
),
(
    (SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'),
    (SELECT id FROM users WHERE email = 'grace.adjei@rpm-system.local'),
    DATE_ADD(CURDATE(), INTERVAL 14 DAY), '14:30:00',
    'RPM Clinic, Room 5', 'Quarterly diabetes review', 'low', 'scheduled'
);

-- --- Doctor availability schedules ---
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, is_active)
VALUES
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'), 0, '09:00:00', '17:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'), 1, '09:00:00', '17:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'), 2, '09:00:00', '17:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'), 3, '09:00:00', '17:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'), 4, '09:00:00', '15:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'), 5, '00:00:00', '00:00:01', FALSE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1001'), 6, '00:00:00', '00:00:01', FALSE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'), 0, '08:00:00', '16:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'), 1, '08:00:00', '16:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'), 2, '08:00:00', '16:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'), 3, '08:00:00', '16:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'), 4, '08:00:00', '14:00:00', TRUE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'), 5, '00:00:00', '00:00:01', FALSE),
((SELECT user_id FROM doctors WHERE license_number = 'LIC-1002'), 6, '00:00:00', '00:00:01', FALSE);

-- --- Patient consents ---
INSERT INTO patient_consents (patient_id, consent_text, consent_given)
VALUES
((SELECT id FROM users WHERE email = 'patient@rpm.com'),
 'Patient consented to remote monitoring via web interface. Acknowledged AI-based risk assessment and emergency contact notification policy.',
 TRUE);
