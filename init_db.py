import psycopg2

# ---------- Database Connection ----------

DB_CONFIG = {
    "dbname": "todos_db",
    "user": "postgres",
    "password": 2108,
    "host": "localhost",
    "port": 5432
}

# ----------  Database Config ----------

# -- Appointments
CREATE_TABLE_APPOINTMENT = '''
CREATE TABLE appointments (
    appointment_id SERIAL PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    clinic_name VARCHAR(100),
    appointment_date TIMESTAMP NOT NULL,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, completed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

# -- Prescriptions
CREATE_TABLE_PRESCRIPTIONS = '''
CREATE TABLE prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    appointment_id INT,  -- no foreign key, just a plain number
    medicine_name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50),
    frequency VARCHAR(50),
    duration_days INT,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

# -- Reminders (Optional)
CREATE_TABLE_REMINDERS = '''
CREATE TABLE reminders (
    reminder_id SERIAL PRIMARY KEY,
    prescription_id INT, -- no foreign key, just a plain number
    reminder_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);'''

# ---------- Function ----------

def init_db():
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_APPOINTMENT)
                cur.execute(CREATE_TABLE_PRESCRIPTIONS)
                cur.execute(CREATE_TABLE_REMINDERS)
                conn.commit()
        print("✅ tasks table created successfully!")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    init_db()
