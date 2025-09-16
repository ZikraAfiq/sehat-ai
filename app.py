from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai
import re, json, random
from datetime import date, timedelta

app = Flask(__name__)
CORS(app)

# ---------- Gemini Config ----------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ---------- Database Config ----------

DB_CONFIG = {
    "dbname": "todos_db",
    "user": "postgres",
    "password": 2108,
    "host": "localhost",
    "port": 5432
}

# ---------- Asisstance Functions ----------

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def willdoLater(): 
    pass
    #TODO

# ---------- Asisstance Functions ----------


# ---------- Main ----------

if __name__ == "__main__":
    app.run(debug=True)