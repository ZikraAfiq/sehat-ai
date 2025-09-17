from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai
import re, json, random
from datetime import datetime

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS for requests from the frontend which runs on a different origin
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500"]) 

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
    "password": str(os.getenv("DB_PASSWORD", "2108")), # Password must be a string
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# ---------- Database Helper Function ----------
def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database: {e}")
        return None
    
## Fetching all Data
def fetch_appointments():
    with get_db_connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM appointments")
            return cur.fetchall()

def fetch_doctors():
    with get_db_connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM doctors")
            return cur.fetchall()

## Also Known As - User Login ID
def fetch_patients():
    with get_db_connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM patients")
            return cur.fetchall()

def fetch_prescriptions():
    with get_db_connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM prescriptions")
            return cur.fetchall()

def fetch_reminders():
    with get_db_connection as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM reminders")
            return cur.fetchall()

## Adding Schedules | Appointments









# ---------- Routes ----------

@app.route("/")
def home():
    return render_template("index.html")





# ---------- API Routes ----------
## Chatbot Endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    if not GEMINI_API_KEY:
        return jsonify({"text": "AI Assistant is currently unavailable. Please check the server configuration."}), 503

    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        model = genai.GenerativeModel('gemini-pro')
        # A simple prompt to guide the model's behavior
        prompt = f"""You are a friendly and helpful healthcare AI assistant. 
        Your goal is to assist users with their health-related questions.
        Provide concise, clear, and safe information. 
        IMPORTANT: Always include a disclaimer that you are not a real doctor and users should consult a professional for medical advice.
        User's question: "{user_message}"
        """
        response = model.generate_content(prompt)
        
        # Simple response handling
        ai_text = response.text if hasattr(response, 'text') else "I'm sorry, I couldn't process that request."
        
        return jsonify({"text": ai_text, "suggestions": [
            "Ask about symptoms", "Book an appointment", "Set medication reminder"
        ]})

    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return jsonify({"error": "Failed to get response from AI assistant"}), 500


## Doctors Endpoint
@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT doctor_id as id, first_name, last_name, specialization, phone, available_days, available_hours FROM doctors ORDER BY first_name;")
            doctors = cur.fetchall()
        return jsonify(doctors)
    except Exception as e:
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to fetch doctors"}), 500
    finally:
        conn.close()

## Appointments Endpoint
@app.route('/api/appointments', methods=['POST'])
def book_appointment():
    data = request.get_json()
    # For this demo, we'll assume a logged-in user with patient_id = 1
    patient_id = 1
    doctor_id = data.get('doctor_id')
    date = data.get('date')
    time = data.get('time')
    reason = data.get('reason')

    if not all([doctor_id, date, time]):
        return jsonify({"error": "Doctor, date, and time are required"}), 400

    try:
        # Combine date and time into a single timestamp
        appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return jsonify({"error": "Invalid date or time format"}), 400

    conn = get_db_connection()
    if conn is None: return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO appointments (patient_id, doctor_id, appointment_date, reason) VALUES (%s, %s, %s, %s) RETURNING appointment_id;",
                (patient_id, doctor_id, appointment_datetime, reason)
            )
            appointment_id = cur.fetchone()['appointment_id']
            conn.commit()
        return jsonify({"message": "Appointment booked successfully!", "appointment_id": appointment_id}), 201
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        return jsonify({"error": "Failed to book appointment"}), 500
    finally:
        conn.close()

## Medications Endpoint
@app.route('/api/medications', methods=['GET', 'POST'])
def handle_medications():
    conn = get_db_connection()
    if conn is None: return jsonify({"error": "Database connection failed"}), 500
    
    # For this demo, we'll assume a logged-in user with patient_id = 1
    patient_id = 1

    try:
        if request.method == 'GET':
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT prescription_id as id, medication_name, dosage, frequency, reminder_times FROM prescriptions WHERE patient_id = %s ORDER BY created_at DESC;",
                    (patient_id,)
                )
                medications = cur.fetchall()
            return jsonify(medications)
        
        elif request.method == 'POST':
            data = request.get_json()
            medication_name = data.get('medication_name')
            dosage = data.get('dosage')
            frequency = data.get('frequency')
            # Convert reminder_times list to a JSON string for the DB
            reminder_times = json.dumps(data.get('reminder_times', []))

            if not medication_name or not dosage:
                return jsonify({"error": "Medication name and dosage are required"}), 400

            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO prescriptions (patient_id, medication_name, dosage, frequency, reminder_times) VALUES (%s, %s, %s, %s, %s) RETURNING prescription_id;",
                    (patient_id, medication_name, dosage, frequency, reminder_times)
                )
                new_id = cur.fetchone()['prescription_id']
                conn.commit()
            return jsonify({"message": "Medication added successfully!", "id": new_id}), 201
            
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        return jsonify({"error": "An error occurred with medications"}), 500
    finally:
        conn.close()

# ---------- Main Execution Block ----------
if __name__ == "__main__":
    # The frontend expects the server on port 5001
    app.run(debug=True, port=5001)