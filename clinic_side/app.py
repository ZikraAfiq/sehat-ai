from flask import Flask, request, jsonify, render_template, g
from flask_cors import CORS
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai
import re, json, random
from datetime import datetime
import bcrypt

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "http://127.0.0.1:5500", "http://localhost:5000",
    "http://127.0.0.1:5000",   # 👈 add this
    "http://127.0.0.1:5001", "http://localhost:5001"
])


# ---------- Gemini AI Configuration ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠️ Gemini API key not found. The AI chat feature will be disabled.")

# ---------- Database Configuration ----------
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "sehat"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": str(os.getenv("DB_PASSWORD", "1234")),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# ---------- Database Helper Functions ----------
def get_db():
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        except psycopg2.OperationalError as e:
            print(f"❌ Could not connect to the database: {e}")
            return None
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ---------- Routes ----------
@app.route('/')
def home():
    return render_template('index.html', title='HealthCare Assistant')

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html', title='AI Assistant')

@app.route("/clinic")
def clinic_dashboard():
    return render_template("index.html")

@app.route("/clinic/patients")
def clinic_patients():
    return render_template("clinic_patients.html")

@app.route("/clinic/appointments")
def clinic_appointments():
    return render_template("clinic_appointments.html")

# ---------- API Routes ----------

## Chatbot Endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    if not GEMINI_API_KEY:
        return jsonify({"text": "AI Assistant is currently unavailable."}), 503
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"You are a helpful AI assistant for a clinic. User asks: '{user_message}'"
        response = model.generate_content(prompt)
        ai_text = response.text
        return jsonify({"text": ai_text})
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return jsonify({"error": "Failed to get response from AI assistant"}), 500

## Doctors Endpoint
@app.route('/api/clinic/doctors', methods=['GET'])
def get_clinic_doctors():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT doctor_id, first_name, last_name, specialization FROM doctors ORDER BY last_name;")
            doctors = cur.fetchall()
        return jsonify(doctors)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to fetch doctors"}), 500

# ---------- CLINIC API ROUTES ----------

## Patients Endpoints
@app.route('/api/clinic/patients', methods=['GET', 'POST'])
def clinic_handle_patients():
    conn = get_db()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    try:
        if request.method == 'GET':
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.patient_id, p.first_name, p.last_name, p.email, p.phone, TO_CHAR(p.dob, 'YYYY-MM-DD') as dob,
                           COUNT(DISTINCT a.appointment_id) as total_appointments,
                           COUNT(DISTINCT pr.prescription_id) as total_medications
                    FROM patients p
                    LEFT JOIN appointments a ON p.patient_id = a.patient_id
                    LEFT JOIN prescriptions pr ON p.patient_id = pr.patient_id
                    GROUP BY p.patient_id
                    ORDER BY p.last_name, p.first_name;
                """)
                return jsonify(cur.fetchall())
        elif request.method == 'POST':
            data = request.get_json()
            if not all([data.get('first_name'), data.get('last_name'), data.get('email')]):
                return jsonify({"error": "First name, last name, and email are required"}), 400
            password_hash = bcrypt.hashpw(data.get('password', 'default').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            with conn.cursor() as cur:
                cur.execute("SELECT patient_id FROM patients WHERE email = %s", (data['email'],))
                if cur.fetchone(): return jsonify({"error": "Email already exists"}), 409
                cur.execute("""
                    INSERT INTO patients (first_name, last_name, email, password_hash, phone, dob) 
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING patient_id;
                """, (data['first_name'], data['last_name'], data['email'], password_hash, data.get('phone'), data.get('dob')))
                patient_id = cur.fetchone()['patient_id']
                conn.commit()
            return jsonify({"message": "Patient added successfully!", "patient_id": patient_id}), 201
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to handle patients"}), 500

@app.route('/api/clinic/patients/<int:patient_id>', methods=['GET', 'PUT', 'DELETE'])
def clinic_handle_individual_patient(patient_id):
    conn = get_db()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    try:
        if request.method == 'GET':
            with conn.cursor() as cur:
                cur.execute("SELECT patient_id, first_name, last_name, email, phone, TO_CHAR(dob, 'YYYY-MM-DD') as dob FROM patients WHERE patient_id = %s", (patient_id,))
                patient = cur.fetchone()
                if not patient: return jsonify({"error": "Patient not found"}), 404
                cur.execute("SELECT a.*, d.first_name as doctor_first_name, d.last_name as doctor_last_name, d.specialization FROM appointments a JOIN doctors d ON a.doctor_id = d.doctor_id WHERE a.patient_id = %s ORDER BY a.appointment_date DESC;", (patient_id,))
                appointments = cur.fetchall()
                cur.execute("SELECT * FROM prescriptions WHERE patient_id = %s ORDER BY created_at DESC", (patient_id,))
                medications = cur.fetchall()
                return jsonify({"patient": patient, "appointments": appointments, "medications": medications})
        elif request.method == 'PUT':
            data = request.get_json()
            if not all([data.get('first_name'), data.get('last_name'), data.get('email')]):
                return jsonify({"error": "First name, last name, and email are required"}), 400
            with conn.cursor() as cur:
                cur.execute("UPDATE patients SET first_name = %s, last_name = %s, email = %s, phone = %s, dob = %s WHERE patient_id = %s",
                            (data['first_name'], data['last_name'], data['email'], data.get('phone'), data.get('dob'), patient_id))
                conn.commit()
            return jsonify({"message": "Patient updated successfully!"})
        elif request.method == 'DELETE':
            with conn.cursor() as cur:
                cur.execute("DELETE FROM patients WHERE patient_id = %s", (patient_id,))
                conn.commit()
            return jsonify({"message": "Patient deleted successfully!"})
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to handle patient request"}), 500

## Appointments Endpoints
@app.route('/api/clinic/appointments', methods=['GET', 'POST'])
def clinic_handle_appointments():
    conn = get_db()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    try:
        if request.method == 'GET':
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.appointment_id, a.appointment_date, a.reason, a.status,
                           p.patient_id, p.first_name as patient_first_name, p.last_name as patient_last_name,
                           d.doctor_id, d.first_name as doctor_first_name, d.last_name as doctor_last_name
                    FROM appointments a
                    JOIN patients p ON a.patient_id = p.patient_id
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    ORDER BY a.appointment_date DESC;
                """)
                return jsonify(cur.fetchall())
        elif request.method == 'POST':
            data = request.get_json()
            if not all([data.get('patient_id'), data.get('doctor_id'), data.get('appointment_date')]):
                return jsonify({"error": "Patient, doctor, and date are required"}), 400
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, appointment_date, reason, status) 
                    VALUES (%s, %s, %s, %s, 'scheduled') RETURNING appointment_id;
                """, (data['patient_id'], data['doctor_id'], data['appointment_date'], data.get('reason')))
                appointment_id = cur.fetchone()['appointment_id']
                conn.commit()
            return jsonify({"message": "Appointment created!", "appointment_id": appointment_id}), 201
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to handle appointments"}), 500

@app.route('/api/clinic/appointments/<int:appointment_id>', methods=['PUT', 'PATCH', 'DELETE'])
def clinic_handle_individual_appointment(appointment_id):
    conn = get_db()
    if not conn: return jsonify({"error": "Database connection failed"}), 500
    try:
        if request.method == 'PATCH':
            data = request.get_json()
            if data.get('status') not in ['scheduled', 'completed', 'cancelled']:
                return jsonify({"error": "Invalid status"}), 400
            with conn.cursor() as cur:
                cur.execute("UPDATE appointments SET status = %s WHERE appointment_id = %s", (data['status'], appointment_id))
                conn.commit()
            return jsonify({"message": "Appointment status updated"})
        elif request.method == 'PUT':
            data = request.get_json()
            if not all([data.get('patient_id'), data.get('doctor_id'), data.get('appointment_date')]):
                return jsonify({"error": "Patient, doctor, and date are required"}), 400
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE appointments 
                    SET patient_id = %s, doctor_id = %s, appointment_date = %s, reason = %s, status = %s
                    WHERE appointment_id = %s
                """, (data['patient_id'], data['doctor_id'], data['appointment_date'], data.get('reason'), data.get('status'), appointment_id))
                conn.commit()
            return jsonify({"message": "Appointment updated successfully!"})
        elif request.method == 'DELETE':
            with conn.cursor() as cur:
                cur.execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))
                conn.commit()
            return jsonify({"message": "Appointment deleted successfully!"})
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to handle appointment"}), 500

# ---------- Dashboard Endpoints ----------

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cur:
            # Total patients
            cur.execute("SELECT COUNT(*) as total FROM patients")
            total_patients = cur.fetchone()['total']
            
            # Total appointments
            cur.execute("SELECT COUNT(*) as total FROM appointments")
            total_appointments = cur.fetchone()['total']
            
            # Today's appointments
            today = datetime.now().date()
            cur.execute("SELECT COUNT(*) as total FROM appointments WHERE DATE(appointment_date) = %s", (today,))
            today_appointments = cur.fetchone()['total']
            
            # Active medications
            cur.execute("SELECT COUNT(DISTINCT prescription_id) as total FROM prescriptions")
            active_medications = cur.fetchone()['total']
            
            return jsonify({
                "total_patients": total_patients,
                "total_appointments": total_appointments,
                "today_appointments": today_appointments,
                "active_medications": active_medications
            })
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to fetch dashboard stats"}), 500

@app.route('/api/dashboard/recent-appointments', methods=['GET'])
def get_recent_appointments():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.appointment_id, a.appointment_date, a.status, a.reason,
                       p.patient_id, p.first_name as patient_first_name, p.last_name as patient_last_name,
                       d.doctor_id, d.first_name as doctor_first_name, d.last_name as doctor_last_name,
                       d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                ORDER BY a.appointment_date DESC
                LIMIT 10
            """)
            appointments = cur.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for apt in appointments:
                if apt['appointment_date']:
                    apt['appointment_date'] = apt['appointment_date'].isoformat()
            
            return jsonify(appointments)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to fetch recent appointments"}), 500

@app.route('/api/dashboard/recent-activity', methods=['GET'])
def get_recent_activity():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cur:
            # Get recent appointments as activity
            cur.execute("""
                SELECT 
                    'appointment' as type,
                    a.appointment_date as time,
                    CONCAT('Appointment ', a.status) as title,
                    CONCAT(p.first_name, ' ', p.last_name, ' with Dr. ', d.first_name, ' ', d.last_name) as description,
                    a.status
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                ORDER BY a.appointment_date DESC
                LIMIT 8
            """)
            activities = cur.fetchall()
            
            # Convert datetime objects to strings
            for activity in activities:
                if activity['time']:
                    activity['time'] = activity['time'].isoformat()
            
            return jsonify(activities)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to fetch recent activity"}), 500

@app.route('/api/dashboard/patients-overview', methods=['GET'])
def get_patients_overview():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.patient_id, p.first_name, p.last_name, p.email, p.phone, p.dob,
                       COUNT(DISTINCT a.appointment_id) as total_appointments,
                       COUNT(DISTINCT pr.prescription_id) as total_medications
                FROM patients p
                LEFT JOIN appointments a ON p.patient_id = a.patient_id
                LEFT JOIN prescriptions pr ON p.patient_id = pr.patient_id
                GROUP BY p.patient_id
                ORDER BY p.last_name, p.first_name
            """)
            patients = cur.fetchall()
            
            # Convert date objects to strings
            for patient in patients:
                if patient['dob']:
                    patient['dob'] = patient['dob'].isoformat()
            
            return jsonify(patients)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to fetch patients overview"}), 500

app.teardown_appcontext(close_db)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
