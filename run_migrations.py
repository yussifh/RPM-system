"""
run_migrations.py
-----------------
Run once to create the new tables for Ratings, Teleconsultations, and Settings.
Usage:  python run_migrations.py
"""
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "rpm_system"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
)

cursor = conn.cursor()

SQL = """
-- 19. DOCTOR_RATINGS
CREATE TABLE IF NOT EXISTS doctor_ratings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_user_id     INT             NOT NULL,
    doctor_user_id      INT             NOT NULL,
    appointment_id      INT             NULL,
    rating              TINYINT         NOT NULL,
    comment             TEXT            NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rating_patient FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rating_doctor  FOREIGN KEY (doctor_user_id)  REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_rating_appt    FOREIGN KEY (appointment_id)  REFERENCES appointments(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 20. TELECONSULTATIONS
CREATE TABLE IF NOT EXISTS teleconsultations (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    patient_user_id     INT             NOT NULL,
    doctor_user_id      INT             NOT NULL,
    appointment_id      INT             NULL,
    status              ENUM('scheduled','in_progress','completed','cancelled') NOT NULL DEFAULT 'scheduled',
    room_id             VARCHAR(64)     NOT NULL,
    started_at          DATETIME        NULL,
    ended_at            DATETIME        NULL,
    notes               TEXT            NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tele_patient   FOREIGN KEY (patient_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_tele_doctor    FOREIGN KEY (doctor_user_id)  REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_tele_appt      FOREIGN KEY (appointment_id)  REFERENCES appointments(id) ON DELETE SET NULL,
    CONSTRAINT uq_tele_room UNIQUE (room_id)
) ENGINE=InnoDB;

-- 21. SYSTEM_SETTINGS
CREATE TABLE IF NOT EXISTS system_settings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    setting_key         VARCHAR(100)    NOT NULL,
    setting_value       TEXT            NULL,
    description         VARCHAR(255)    NULL,
    updated_by          INT             NULL,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_settings_user FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_setting_key    UNIQUE (setting_key)
) ENGINE=InnoDB;
"""

for statement in SQL.split(";"):
    # Remove leading comment lines, then check if any real SQL remains.
    stmt_lines = [
        line for line in statement.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    stmt = "\n".join(stmt_lines).strip()
    if stmt:
        cursor.execute(stmt)
        print(f"OK: {stmt[:60]}...")

conn.commit()
cursor.close()
conn.close()
print("\nAll 3 tables created successfully!")
