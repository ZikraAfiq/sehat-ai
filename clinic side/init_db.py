import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# ---------- Database Connection ----------
# It's better to get sensitive info from environment variables
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "sehat"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "1234"), # Ensure password is a string
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# ----------  Table Creation Queries ----------

# -- Drop existing tables to ensure a clean slate
DROP_TABLES = '''
DROP TABLE IF EXISTS reminders, prescriptions, appointments, doctors, patients CASCADE;
'''

# -- Patients (for future login/signup functionality)
CREATE_TABLE_PATIENTS = '''
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    dob DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

# -- Doctors
CREATE_TABLE_DOCTORS = '''
CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(20),
    available_days JSONB, -- e.g., ["Monday", "Wednesday", "Friday"]
    available_hours JSONB, -- e.g., {"start": "09:00", "end": "17:00"}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

# -- Appointments (Updated with Foreign Keys)
CREATE_TABLE_APPOINTMENT = '''
CREATE TABLE appointments (
    appointment_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id INT REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    appointment_date TIMESTAMP NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, completed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

# -- Prescriptions (Updated with Foreign Keys)
CREATE_TABLE_PRESCRIPTIONS = '''
CREATE TABLE prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id) ON DELETE CASCADE,
    appointment_id INT REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    medication_name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50),
    frequency VARCHAR(50),
    reminder_times JSONB, -- e.g., ["08:00", "20:00"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

# -- Reminders (Updated with Foreign Keys)
CREATE_TABLE_REMINDERS = '''
CREATE TABLE reminders (
    reminder_id SERIAL PRIMARY KEY,
    prescription_id INT REFERENCES prescriptions(prescription_id) ON DELETE CASCADE,
    reminder_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, dismissed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

# -- Seed Doctors Data
SEED_DOCTORS = '''
INSERT INTO doctors (first_name, last_name, specialization, phone, available_days, available_hours) VALUES
('Amelia', 'Tan', 'Cardiology', '+673 223 4567', '["Monday", "Wednesday", "Friday"]', '{"start": "09:00", "end": "17:00"}'),
('Benny', 'Chen', 'Dermatology', '+673 223 4568', '["Tuesday", "Thursday"]', '{"start": "10:00", "end": "18:00"}'),
('Charlotte', 'Lim', 'Pediatrics', '+673 223 4569', '["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]', '{"start": "08:30", "end": "16:30"}');
'''

# -- Seed a dummy patient for testing
SEED_PATIENTS = '''
INSERT INTO patients (first_name, last_name, email, password_hash, phone, dob) VALUES
('John', 'Doe', 'john.doe@email.com', 'hashed_password_placeholder', '+673 888 1234', '1990-01-15');
'''

# -- Seed a Appointments for Testing
SEED_APPOINTMENTS = '''
INSERT INTO appointments (patient_id, doctor_id, appointment_date, reason, status) VALUES
(1, 1, '2025-09-20 10:00:00', 'Routine heart checkup', 'scheduled'),
(1, 2, '2025-09-21 14:00:00', 'Skin rash consultation', 'scheduled'),
(1, 3, '2025-09-22 09:30:00', 'Pediatric checkup (family member)', 'completed');
'''

# ---------- Seed Prescriptions ----------
SEED_PRESCRIPTIONS = '''
INSERT INTO prescriptions (patient_id, appointment_id, medication_name, dosage, frequency, reminder_times) VALUES
(1, 1, 'Atenolol', '50mg', 'Once daily', '["08:00"]'),
(1, 2, 'Hydrocortisone Cream', 'Apply thin layer', 'Twice daily', '["09:00", "21:00"]'),
(1, 3, 'Paracetamol', '500mg', 'Every 6 hours', '["08:00", "14:00", "20:00"]');
'''

# ---------- Seed Reminders ----------
SEED_REMINDERS = '''
INSERT INTO reminders (prescription_id, reminder_time, status) VALUES
(1, '2025-09-20 08:00:00', 'pending'),
(2, '2025-09-21 09:00:00', 'pending'),
(2, '2025-09-21 21:00:00', 'pending'),
(3, '2025-09-22 08:00:00', 'pending'),
(3, '2025-09-22 14:00:00', 'pending'),
(3, '2025-09-22 20:00:00', 'pending');
'''


# ---------- Main Function ----------

def init_db():
    """Initializes the database by creating and seeding tables."""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                print("Dropping existing tables...")
                cur.execute(DROP_TABLES)
                
                print("Creating tables...")
                cur.execute(CREATE_TABLE_PATIENTS)
                cur.execute(CREATE_TABLE_DOCTORS)
                cur.execute(CREATE_TABLE_APPOINTMENT)
                cur.execute(CREATE_TABLE_PRESCRIPTIONS)
                cur.execute(CREATE_TABLE_REMINDERS)
                
                print("Seeding data...")
                cur.execute(SEED_DOCTORS)
                cur.execute(SEED_PATIENTS)
                cur.execute(SEED_APPOINTMENTS)
                cur.execute(SEED_PRESCRIPTIONS)
                cur.execute(SEED_REMINDERS)

                conn.commit()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    init_db()