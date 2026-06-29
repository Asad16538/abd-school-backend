
import random
import jwt
import requests
import os
import re
import traceback
import time
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from pydantic import BaseModel
from datetime import datetime
from flask import Flask
import os
PORT = int(os.environ.get('PORT', 10000))

# --- DATABASE CONFIGURATION (PostgreSQL for Render, SQLite for Local) ---
DB_NAME = "school.db"  # SQLite fallback for local development
DATABASE_URL = os.environ.get('DATABASE_URL')  # Render PostgreSQL URL

def execute_query(cursor, query, params=()):
    """Execute query with proper placeholders for SQLite or PostgreSQL"""
    if DATABASE_URL:
        # PostgreSQL uses %s
        query = query.replace('?', '%s')
        cursor.execute(query, params)
    else:
        # SQLite uses ?
        cursor.execute(query, params)

def get_db_connection():
    """Returns a database connection (PostgreSQL on Render, SQLite locally)"""
    if DATABASE_URL:
        # PostgreSQL connection for Render (Permanent)
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    else:
        # SQLite connection for local development
        return sqlite3.connect(DB_NAME)  # ← YEH SAHI HAI

# --- MISSING VARIABLES (YAHAN ADD KARO) ---
verification_store = {}
SECRET_KEY = "ab_digital_work_secret_key_secure_⚡"

# File ke top par add karo
TELEGRAM_TOKEN = "8793915550:AAGK3RIR9PDQXkawoxaSp-69sfB5jge87A0"
TELEGRAM_CHAT_ID = "1989970458" # Yahan apni Telegram Chat ID daal dena

# Yeh ek hi function poori file mein hona chahiye
def send_telegram_msg(text):
    # CHAT_ID ko yahan hardcode kar do taaki koi confusion na rahe
    CHAT_ID = "1989970458" 
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=5)
        print("Telegram Response:", response.text) # <--- Isse Render Logs mein dikh jayega ki message gaya ya nahi
    except Exception as e:
        print(f"Telegram Bot Error: {e}")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # =====================================================================
    # 🔥 ALL TABLES WITH POSTGRESQL SYNTAX (SERIAL PRIMARY KEY)
    # =====================================================================
    
    # 1. Users Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # 2. Advanced School Settings Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS school_settings (
            id SERIAL PRIMARY KEY,
            school_name TEXT NOT NULL,
            school_address TEXT,
            school_email TEXT,
            school_mobile TEXT,
            school_logo TEXT,
            school_signature TEXT
        )
    ''')
    
    # 3. Upgraded Students Table (Complete)
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            admission_no TEXT UNIQUE NOT NULL,
            roll_no TEXT,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            section TEXT NOT NULL,
            dob TEXT,
            gender TEXT,
            category TEXT,
            aadhaar_no TEXT, 
            samagra_id TEXT,
            father_name TEXT,
            mother_name TEXT,
            parent_mobile TEXT NOT NULL,
            address TEXT,
            school_fee_total REAL DEFAULT 0,
            school_fee_paid REAL DEFAULT 0,
            transport_fee_total REAL DEFAULT 0,
            transport_fee_paid REAL DEFAULT 0,
            bank_name TEXT,
            account_no TEXT,
            ifsc_code TEXT,
            next_due_date TEXT,
            fee_cycle TEXT DEFAULT 'Annual',
            status TEXT DEFAULT 'Active',
            parent_telegram_id TEXT,
            cycle_fee_amount REAL DEFAULT 0,
            stream TEXT DEFAULT ''
        )
    ''')
    
    # 4. Expenses Table (Updated with all fields)
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            payment_mode TEXT NOT NULL,
            vendor_name TEXT,
            remarks TEXT
        )
    ''')
    
    # 5. Fee Collection Logs (Complete)
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS fee_transactions (
            id SERIAL PRIMARY KEY,
            receipt_no TEXT UNIQUE,
            student_id INTEGER,
            amount_paid REAL,
            school_pay REAL DEFAULT 0,
            transport_pay REAL DEFAULT 0,
            next_due_date TEXT,
            date TEXT NOT NULL
        )
    ''')
    
    # 6. Staff Directory Table (Complete with all columns)
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS staff (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            designation TEXT,
            mobile TEXT NOT NULL,
            base_salary REAL DEFAULT 0,
            status TEXT DEFAULT 'Active',
            pf_enabled INTEGER DEFAULT 0,
            pf_percentage REAL DEFAULT 12.0,
            available_cl INTEGER DEFAULT 12,
            telegram_id TEXT,
            device_token TEXT
        )
    ''')
    
    # 7. Attendance Rules Table (Complete)
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS attendance_rules (
            id SERIAL PRIMARY KEY,
            school_latitude REAL NOT NULL DEFAULT 24.7432,
            school_longitude REAL NOT NULL DEFAULT 78.8561,
            allowed_radius_meters REAL DEFAULT 50.0,
            shift_start_time TEXT DEFAULT '08:00',
            late_buffer_minutes INTEGER DEFAULT 15,
            shift_end_time TEXT DEFAULT '14:00',
            late_fine_per_minute REAL DEFAULT 5.0
        )
    ''')
    
    # 8. Geo-Attendance Logs Table (Complete)
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS staff_attendance (
            id SERIAL PRIMARY KEY,
            staff_id INTEGER,
            date TEXT NOT NULL,
            check_in_time TEXT,
            check_out_time TEXT,
            status TEXT,
            late_fine REAL DEFAULT 0,
            is_half_day INTEGER DEFAULT 0,
            leave_type TEXT DEFAULT 'Present',
            FOREIGN KEY(staff_id) REFERENCES staff(id)
        )
    ''')
    
    # 9. Master Classes Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS classes (
            id SERIAL PRIMARY KEY,
            class_name TEXT NOT NULL UNIQUE,
            room_number TEXT,
            max_capacity INTEGER DEFAULT 40
        )
    ''')
    
    # 10. Sections Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS sections (
            id SERIAL PRIMARY KEY,
            class_id INTEGER,
            section_name TEXT NOT NULL,
            class_teacher_id INTEGER,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )
    ''')
    
    # 11. Subjects Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS subjects (
            id SERIAL PRIMARY KEY,
            class_id INTEGER,
            subject_name TEXT NOT NULL,
            subject_teacher_id INTEGER,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )
    ''')
    
    # 12. Timetable Schedule Master
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS timetables (
            id SERIAL PRIMARY KEY,
            class_id INTEGER,
            section_name TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            period_number INTEGER NOT NULL,
            start_time TEXT,
            end_time TEXT,
            subject_id INTEGER,
            teacher_id INTEGER,
            FOREIGN KEY(class_id) REFERENCES classes(id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id),
            FOREIGN KEY(teacher_id) REFERENCES staff(id)
        )
    ''')
    
    # 13. Attendance Records (Complete)
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            class_name TEXT NOT NULL,
            section_name TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late', 'Leave')),
            marked_by TEXT DEFAULT 'Teacher',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE (student_id, date)
        )
    ''')
    
    # 14. Holidays Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS holidays (
            id SERIAL PRIMARY KEY,
            holiday_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 15. QR Attendance Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS qr_attendance (
            id SERIAL PRIMARY KEY,  
            teacher_id TEXT NOT NULL,
            teacher_name TEXT NOT NULL,
            teacher_subject TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            distance INTEGER,
            status TEXT,
            marked_at TEXT
        )
    ''')
    
    # 16. Staff Advance Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS staff_advance (
            id SERIAL PRIMARY KEY,
            staff_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            purpose TEXT,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
        # =====================================================================
    # 📚 EXAM MANAGEMENT TABLES
    # =====================================================================
    
    # 17. Board Settings Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS board_settings (
            id SERIAL PRIMARY KEY,
            board_name TEXT NOT NULL DEFAULT 'CBSE',
            exam_pattern TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 18. Exams Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS exams (
            id SERIAL PRIMARY KEY,
            exam_id TEXT NOT NULL,
            exam_name TEXT NOT NULL,
            class TEXT NOT NULL,
            section TEXT NOT NULL,
            subject TEXT NOT NULL,
            max_marks INTEGER DEFAULT 100,
            passing_marks INTEGER DEFAULT 33,
            weightage INTEGER DEFAULT 0,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(exam_id, class, section, subject)
        )
    ''')
    
    # 19. Exam Marks Table (Updated with attendance)
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS exam_marks (
            id SERIAL PRIMARY KEY,
            exam_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            marks_obtained REAL DEFAULT 0,
            theory_marks REAL DEFAULT 0,
            internal_marks REAL DEFAULT 0,
            attendance_marks REAL DEFAULT 0,
            grade TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(exam_id, student_id)
        )
    ''')
    
    # 20. Exam Results Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS exam_results (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            class TEXT NOT NULL,
            section TEXT NOT NULL,
            total_marks REAL DEFAULT 0,
            obtained_marks REAL DEFAULT 0,
            percentage REAL DEFAULT 0,
            grade TEXT,
            rank INTEGER,
            result_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE(student_id, class, section)
        )
    ''')
    
    # 21. Grade System Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS grade_system (
            id SERIAL PRIMARY KEY,
            grade_name TEXT NOT NULL,
            min_percentage REAL NOT NULL,
            max_percentage REAL NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 22. Exam Templates Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS exam_templates (
            id SERIAL PRIMARY KEY,
            board_name TEXT NOT NULL,
            template_data TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 23. Exam Patterns Table
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS exam_patterns (
            id SERIAL PRIMARY KEY,
            board_name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            subject_type TEXT NOT NULL,
            theory_marks INTEGER NOT NULL,
            internal_marks INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(board_name, class_name, subject_type)
        )
    ''')
    
    # =====================================================================
    # 📚 DEFAULT EXAM DATA
    # =====================================================================
    
    # Default Board Settings
    execute_query(cursor, "SELECT * FROM board_settings LIMIT 1")
    if not cursor.fetchone():
        execute_query(cursor, '''
            INSERT INTO board_settings (board_name, exam_pattern) VALUES (?, ?)
        ''', ('CBSE', '{"pt1":"Periodic Test 1","term1":"Term 1","pt2":"Periodic Test 2","term2":"Term 2"}'))
    
    # Default Grade System
    execute_query(cursor, "SELECT * FROM grade_system LIMIT 1")
    if not cursor.fetchone():
        grade_data = [
            ('A+', 90, 100, 'Outstanding'),
            ('A', 80, 89, 'Excellent'),
            ('B+', 70, 79, 'Very Good'),
            ('B', 60, 69, 'Good'),
            ('C', 50, 59, 'Average'),
            ('D', 40, 49, 'Below Average'),
            ('F', 0, 39, 'Fail')
        ]
        for g in grade_data:
            execute_query(cursor, '''
                INSERT INTO grade_system (grade_name, min_percentage, max_percentage, description)
                VALUES (?, ?, ?, ?)
            ''', g)
    
    # Default Exam Templates
    execute_query(cursor, "SELECT * FROM exam_templates LIMIT 1")
    if not cursor.fetchone():
        templates = [
            ('CBSE', '{"pt1":"Periodic Test 1","term1":"Term 1","pt2":"Periodic Test 2","term2":"Term 2"}'),
            ('MP Board', '{"quarterly":"Quarterly Exam","half_yearly":"Half Yearly Exam","annual":"Annual Exam"}'),
            ('UP Board', '{"quarterly":"Quarterly Exam","half_yearly":"Half Yearly Exam","pre_board":"Pre-Board Exam","annual":"Annual Exam"}'),
            ('Custom', '{}')
        ]
        for t in templates:
            execute_query(cursor, '''
                INSERT INTO exam_templates (board_name, template_data) VALUES (?, ?)
            ''', t)
    
    # Default Exam Patterns
    execute_query(cursor, "SELECT * FROM exam_patterns LIMIT 1")
    if not cursor.fetchone():
        # CBSE
        execute_query(cursor, '''
            INSERT INTO exam_patterns (board_name, class_name, subject_type, theory_marks, internal_marks) VALUES
            ('CBSE', 'All', 'All', 80, 20)
        ''')
        
        # MP Board
        execute_query(cursor, '''
            INSERT INTO exam_patterns (board_name, class_name, subject_type, theory_marks, internal_marks) VALUES
            ('MP Board', '10', 'Languages', 75, 25),
            ('MP Board', '10', 'Mathematics', 75, 25),
            ('MP Board', '10', 'Social Science', 75, 25),
            ('MP Board', '10', 'Science', 75, 25),
            ('MP Board', '12', 'Non-Practical', 80, 20),
            ('MP Board', '12', 'Practical', 70, 30)
        ''')
        
        # UP Board
        execute_query(cursor, '''
            INSERT INTO exam_patterns (board_name, class_name, subject_type, theory_marks, internal_marks) VALUES
            ('UP Board', 'All', 'All', 100, 0)
        ''')
    
    conn.commit()
    
        # =====================================================================
    # 🔥 FORCE ADD MISSING COLUMNS (For existing databases)
    # =====================================================================
    
    # Students table missing columns
    try:
        execute_query(cursor, "ALTER TABLE students ADD COLUMN IF NOT EXISTS cycle_fee_amount REAL DEFAULT 0")
        execute_query(cursor, "ALTER TABLE students ADD COLUMN IF NOT EXISTS parent_telegram_id TEXT")
        execute_query(cursor, "ALTER TABLE students ADD COLUMN IF NOT EXISTS stream TEXT DEFAULT ''")
    except Exception as e:
        print(f"⚠️ Students columns already exist or error: {e}")
        
    # Staff table missing columns - Add these
    try:
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS roll TEXT DEFAULT 'Teacher'")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS subject TEXT")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS class_teacher TEXT")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS assigned_class TEXT")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS assigned_section TEXT")
    except Exception as e:
        print(f"⚠️ Staff columns already exist or error: {e}")
    
    # Staff table missing columns
    try:
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS device_token TEXT")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS pf_enabled INTEGER DEFAULT 0")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS pf_percentage REAL DEFAULT 12.0")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS available_cl INTEGER DEFAULT 12")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS telegram_id TEXT")
        execute_query(cursor, "ALTER TABLE staff ADD COLUMN IF NOT EXISTS password TEXT")
    except Exception as e:
        print(f"⚠️ Staff columns already exist or error: {e}")
    
    # Attendance rules missing columns
    try:
        execute_query(cursor, "ALTER TABLE attendance_rules ADD COLUMN IF NOT EXISTS late_fine_per_minute REAL DEFAULT 5.0")
    except Exception as e:
        print(f"⚠️ Attendance rules columns already exist or error: {e}")
    
    # Staff attendance missing columns
    try:
        execute_query(cursor, "ALTER TABLE staff_attendance ADD COLUMN IF NOT EXISTS late_fine REAL DEFAULT 0")
        execute_query(cursor, "ALTER TABLE staff_attendance ADD COLUMN IF NOT EXISTS is_half_day INTEGER DEFAULT 0")
        execute_query(cursor, "ALTER TABLE staff_attendance ADD COLUMN IF NOT EXISTS leave_type TEXT DEFAULT 'Present'")
    except Exception as e:
        print(f"⚠️ Staff attendance columns already exist or error: {e}")
    
    # Fee transactions missing columns
    try:
        execute_query(cursor, "ALTER TABLE fee_transactions ADD COLUMN IF NOT EXISTS receipt_no TEXT")
        execute_query(cursor, "ALTER TABLE fee_transactions ADD COLUMN IF NOT EXISTS school_pay REAL DEFAULT 0")
        execute_query(cursor, "ALTER TABLE fee_transactions ADD COLUMN IF NOT EXISTS transport_pay REAL DEFAULT 0")
        execute_query(cursor, "ALTER TABLE fee_transactions ADD COLUMN IF NOT EXISTS next_due_date TEXT")
    except Exception as e:
        print(f"⚠️ Fee transactions columns already exist or error: {e}")
    
    # =====================================================================
    # 🔥 DEFAULT DATA (Admin, Settings, Rules)
    # =====================================================================
    
    # Default Admin Check
    execute_query(cursor, "SELECT * FROM users WHERE username = %s", ("admin",))
    if not cursor.fetchone():
        hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
        execute_query("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", ("admin", hashed_pw, "Admin"))
    
    # Default Settings Check
    execute_query(cursor, "SELECT * FROM school_settings WHERE id = 1")
    if not cursor.fetchone():
        execute_query(cursor, '''
            INSERT INTO school_settings (id, school_name, school_address, school_email, school_mobile, school_logo, school_signature) 
            VALUES (1, 'Smart School ERP', 'Madhya Pradesh, India', 'admin@school.com', '9893260067', NULL, NULL)
        ''')
    
    # Default Rule Entry Check
    execute_query(cursor, "SELECT * FROM attendance_rules WHERE id = 1")
    if not cursor.fetchone():
        execute_query(cursor, '''
            INSERT INTO attendance_rules (id, school_latitude, school_longitude, allowed_radius_meters, shift_start_time, late_buffer_minutes, shift_end_time)
            VALUES (1, 24.7432, 78.8561, 50.0, '08:00', 15, '14:00')
        ''')
    
    conn.commit()
    conn.close()
    print("🚀 Advanced School ERP Database Loaded & Upgraded Successfully!")


def init_expense_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, "DROP TABLE IF EXISTS expenses")  # ← cursor add kiya
    execute_query(cursor, '''CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY, 
        title TEXT NOT NULL, 
        category TEXT NOT NULL, 
        amount REAL NOT NULL, 
        date TEXT NOT NULL, 
        payment_mode TEXT NOT NULL, 
        vendor_name TEXT, 
        remarks TEXT
    )''')
    
    conn.commit()
    conn.close()

# --- APP CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_folder_path = os.path.join(BASE_DIR, 'static')
app = Flask(__name__, static_folder=static_folder_path, static_url_path='/static')
CORS(app, resources={r"/api/*": {"origins": "*"}})
bcrypt = Bcrypt(app)

# --- STARTUP HOOK UPDATE ---
with app.app_context():
    init_db()
    init_expense_table()
    
    # 🎯 TELEGRAM WEBHOOK AUTO-REGISTER (FIXED)
try:
    TOKEN = "8793915550:AAGK3RIR9PDQXkawoxaSp-69sfB5jge87A0"
    # Railway hata kar Render ka URL daalo
    WEBHOOK_URL = "https://abd-school-backend.onrender.com/webhook/" + TOKEN
    
    response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}")
    
    if response.status_code == 200:
        print("✅ Telegram Webhook auto-registered successfully to Render!")
    else:
        print(f"⚠️ Webhook registration failed with status: {response.status_code}")
except Exception as e:
    print("⚠️ Telegram Webhook Auto-register failed:", e)
        
    print("✅ DATABASE INITIALIZED ON STARTUP!")

# --- ROUTES (Yahan se apne saare @app.route wale functions niche paste kar do) ---

# CORS Fix: Har request allow hogi
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

def calculate_distance_meters(lat1, lon1, lat2, lon2):
    import math
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


    
# 📊 1. GET DASHBOARD STATS API (EGADAM CLEAN & ZERO DEFAULT)
@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 🎯 EXACT IS TARAH BADAL DIJIYE BHAI:
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    
    # Kul Chatra Count
    execute_query(cursor, "SELECT COUNT(*) FROM students WHERE status = 'Active'")
    total_students = cursor.fetchone()[0] or 0
    
    # Kul Fees Target (School + Transport)
    execute_query(cursor, "SELECT SUM(school_fee_total + transport_fee_total) FROM students WHERE status = 'Active'")
    total_fees_target = cursor.fetchone()[0] or 0
    
    # Kul Jama (School + Transport)
    execute_query(cursor, "SELECT SUM(school_fee_paid + transport_fee_paid) FROM students WHERE status = 'Active'")
    total_fees_paid = cursor.fetchone()[0] or 0
    
    # Aaj Ki Jama from live transactions table
    execute_query(cursor, "SELECT SUM(amount_paid) FROM fee_transactions WHERE date = ?", (today_str,))
    today_fees_paid = cursor.fetchone()[0] or 0
    
    # Kul Bakaya calculation
    total_pending = total_fees_target - total_fees_paid
    
    # Kul Kharcha
    execute_query(cursor, "SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0
    
    # Kul Aamdani
    total_income = total_fees_paid - total_expenses
    conn.close()
    
    return jsonify({
        "total_students": total_students,
        "total_fees_target": total_fees_target,
        "total_fees_paid": total_fees_paid,
        "today_fees_paid": today_fees_paid,
        "total_pending": total_pending,
        "total_expenses": total_expenses,
        "total_income": total_income
    })

# 📉 MOST PENDING FEE STUDENTS LIST API (High Pending First Sorting Logic)
@app.route('/api/pending-students', methods=['GET'])
def get_pending_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor, '''
        SELECT id, name, class, section, parent_mobile, 
               school_fee_total, school_fee_paid, 
               transport_fee_total, transport_fee_paid,
               ((school_fee_total + transport_fee_total) - (school_fee_paid + transport_fee_paid)) as total_pending
        FROM students
        WHERE ((school_fee_total + transport_fee_total) - (school_fee_paid + transport_fee_paid)) > 0
        ORDER BY total_pending DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    student_list = []
    for r in rows:
        student_list.append({
            "id": r[0], "name": r[1], "class": r[2], "section": r[3], "parent_mobile": r[4],
            "school_fee_total": r[5], "school_fee_paid": r[6],
            "transport_fee_total": r[7], "transport_fee_paid": r[8],
            "total_pending": r[9]
        })
    return jsonify(student_list)


@app.route('/api/submit-fee-advanced', methods=['POST'])
def submit_fee():
    import traceback 
    data = request.json
    print("📥 Frontend Se Aaya Data:", data)

    student_id = data.get('student_id')
    school_pay = float(data.get('school_pay', 0))
    transport_pay = float(data.get('transport_pay', 0))
    
    receipt_no = str(data.get('receipt_no', '')).strip()
    next_due_date = str(data.get('next_due_date', '')).strip()
    today_str = datetime.now().date().strftime("%Y-%m-%d")
    
    if not receipt_no:
        receipt_no = f"REC-{random.randint(100000, 999999)}"
    if not next_due_date:
        next_due_date = today_str
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
                # 1. Update Student Balance
        print("🔄 Step 1: Updating student balance...")
        if DATABASE_URL:
            execute_query(cursor, '''
                UPDATE students 
                SET school_fee_paid = school_fee_paid + %s, 
                    transport_fee_paid = transport_fee_paid + %s 
                WHERE id = %s
            ''', (school_pay, transport_pay, student_id))
        else:
            execute_query(cursor, '''
                UPDATE students 
                SET school_fee_paid = school_fee_paid + ?, 
                    transport_fee_paid = transport_fee_paid + ? 
                WHERE id = ?
            ''', (school_pay, transport_pay, student_id))
        
        total_paid_now = school_pay + transport_pay
        
        # 2. Log Transaction
        print("🔄 Step 2: Inserting into fee_transactions...")
        if total_paid_now > 0:
            execute_query(cursor,'''
                INSERT INTO fee_transactions (receipt_no, student_id, amount_paid, school_pay, transport_pay, next_due_date, date) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (receipt_no, student_id, total_paid_now, school_pay, transport_pay, next_due_date, today_str))
            
        conn.commit()
        print("✅ Step 3: Database Commit Successful!")
        
        # 📱 TELEGRAM INVOICE ALERT ENGINE
        try:
            print("🔄 Step 4: Fetching info for Telegram Alert...")
            execute_query(cursor, "SELECT school_name FROM school_settings WHERE id = 1")
            school_row = cursor.fetchone()
            school_name = school_row[0] if school_row else "Smart School ERP"
            
            execute_query(cursor, "SELECT name FROM students WHERE id = ?", (student_id,))
            s_row = cursor.fetchone()
            
            if s_row:
                student_name = s_row[0]
                
                # Telegram Message Format
                msg = (
                    f"🧾 *[फीस रसीद - {school_name.upper()}]*\n\n"
                    f"नमस्ते,\n\n"
                    f"🍁 *छात्र का नाम:* {student_name}\n"
                    f"🔢 *रसीद संख्या:* {receipt_no}\n"
                    f"💰 *कुल जमा राशि:* *₹{total_paid_now}*\n"
                    f"   - शैक्षणिक फीस: ₹{school_pay}\n"
                    f"   - वाहन/बस FEES: ₹{transport_pay}\n\n"
                    f"⚠️ *अगली देय तिथि:* {next_due_date}\n\n"
                    f"_Powered by: A.B.Digital Work_"
                )
                
                print("🚀 Step 5: Sending request to Telegram Bot...")
                send_telegram_msg(msg) # ✅ TELEGRAM FUNCTION CALL
        except Exception as tel_err:
            print(f"⚠️ Telegram Engine Skipped/Offline: {tel_err}")

        conn.close()
        return jsonify({
            "success": True,
            "receipt_no": receipt_no,
            "message": "🎉 Fees Processed Successfully!"
        })

    except Exception as main_err:
        print("\n❌❌❌ CRITICAL ERROR IN SUBMIT_FEE FUNCTION ❌❌❌")
        traceback.print_exc()
        if 'conn' in locals(): conn.close()
        return jsonify({"success": False, "error": str(main_err)}), 500

# 📥 EXCEL / MANUAL BULK IMPORT API
@app.route('/api/students/bulk-import', methods=['POST'])
def bulk_import_students():
    try:
        data = request.json
        students_list = data.get('students', [])
        
        if not students_list:
            return jsonify({"error": "Data khali hai!"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        success_count = 0
        for s in students_list:
            try:
                # Excel/Form columns mapping safely
                execute_query(cursor, '''
                    INSERT INTO students (
                        admission_no, roll_no, name, class, section, dob, gender, category,
                        aadhaar_no, samagra_id, father_name, mother_name, parent_mobile, address, 
                        fee_cycle, cycle_fee_amount, school_fee_total, transport_fee_total, bank_name, account_no, ifsc_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(s.get('Admission No', s.get('admission_no', ''))), 
                    str(s.get('Roll No', s.get('roll_no', ''))), 
                    s.get('Student Name', s.get('name', '')),
                    s.get('Class', s.get('student_class', '')), 
                    s.get('Section', s.get('section', 'A')), 
                    s.get('DOB', s.get('dob', '')), 
                    s.get('Gender', s.get('gender', 'Male')),
                    s.get('Category', s.get('category', 'General')),
                    str(s.get('Aadhaar No', s.get('aadhaar_no', ''))), 
                    str(s.get('Samagra ID', s.get('samagra_id', ''))), 
                    s.get('Father Name', s.get('father_name', '')),
                    s.get('Mother Name', s.get('mother_name', '')), 
                    str(s.get('WhatsApp No', s.get('whatsapp_no', ''))), 
                    s.get('Address', s.get('address', '')),
                    s.get('Fee Cycle', s.get('fee_cycle', 'Monthly')), # New cycle mapping
                    float(s.get('Cycle Fee Amount', s.get('cycle_fee_amount', 0)) or 0),
                    float(s.get('Total Fee', s.get('school_fee_total', 0)) or 0), # Custom input read
                    float(s.get('Transport Fee', s.get('transport_fee_total', 0)) or 0),
                    s.get('Bank Name', s.get('bank_name', '')), 
                    str(s.get('Account No', s.get('account_no', ''))), 
                    s.get('IFSC Code', s.get('ifsc_code', ''))
                ))
                success_count += 1
            except Exception as e:
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    continue
                # Baaki errors ke liye raise karo
                raise e
                
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"{success_count} bache system mein register ho gaye!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# =====================================================================
# 📦 NEW: ZIP BULK IMPORT WITH PHOTOS API (NAYA - YE ADD KARO)
# =====================================================================
@app.route('/api/students/bulk-import-with-photos', methods=['POST'])
def bulk_import_with_photos():
    import zipfile
    import tempfile
    import shutil
    import pandas as pd
    
    try:
        zip_file = request.files.get('zip_file')
        if not zip_file:
            return jsonify({"error": "ZIP file nahi mila!"}), 400
        
        # Temporary folder banao
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'upload.zip')
        zip_file.save(zip_path)
        
        # ZIP extract karo
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Excel file dhundo
        excel_file = None
        for f in os.listdir(temp_dir):
            if f.endswith(('.xlsx', '.xls', '.csv')):
                excel_file = os.path.join(temp_dir, f)
                break
        
        if not excel_file:
            shutil.rmtree(temp_dir)
            return jsonify({"error": "Excel file ZIP mein nahi mili!"}), 400
        
        # Excel read karo
        df = pd.read_excel(excel_file)
        students_list = df.to_dict('records')
        
        # Photos folder dhundo
        photos_folder = os.path.join(temp_dir, 'photos')
        if not os.path.exists(photos_folder):
            photos_folder = temp_dir
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        success_count = 0
        for s in students_list:
            try:
                roll_no = str(s.get('Roll No', s.get('roll_no', '')))
                student_class = str(s.get('Class', s.get('student_class', '')))
                section = str(s.get('Section', s.get('section', 'A')))
                
                # ✅ PHOTO COPY KARO AGAR MILTI HAI
                photo_filename = f"{roll_no}.jpg"
                photo_path = os.path.join(photos_folder, photo_filename)
                
                # Agar .jpg na mile to .png try karo
                if not os.path.exists(photo_path):
                    photo_path = os.path.join(photos_folder, f"{roll_no}.png")
                
                if os.path.exists(photo_path):
                    upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'student_photos')
                    folder_name = f"{student_class}_{section}"
                    target_folder = os.path.join(upload_folder, folder_name)
                    
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    
                    shutil.copy(photo_path, os.path.join(target_folder, f"{roll_no}.jpg"))
                    print(f"📸 Photo copied: {roll_no}.jpg")
                
                # Database Insertion
                execute_query(cursor, '''
                    INSERT INTO students (
                        admission_no, roll_no, name, class, section, dob, gender, category,
                        aadhaar_no, samagra_id, father_name, mother_name, parent_mobile, address, 
                        fee_cycle, cycle_fee_amount, school_fee_total, transport_fee_total, bank_name, account_no, ifsc_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(s.get('Admission No', s.get('admission_no', ''))), 
                    str(s.get('Roll No', s.get('roll_no', ''))), 
                    s.get('Student Name', s.get('name', '')),
                    s.get('Class', s.get('student_class', '')), 
                    s.get('Section', s.get('section', 'A')), 
                    s.get('DOB', s.get('dob', '')), 
                    s.get('Gender', s.get('gender', 'Male')),
                    s.get('Category', s.get('category', 'General')),
                    str(s.get('Aadhaar No', s.get('aadhaar_no', ''))), 
                    str(s.get('Samagra ID', s.get('samagra_id', ''))), 
                    s.get('Father Name', s.get('father_name', '')),
                    s.get('Mother Name', s.get('mother_name', '')), 
                    str(s.get('WhatsApp No', s.get('whatsapp_no', ''))), 
                    s.get('Address', s.get('address', '')),
                    s.get('Fee Cycle', s.get('fee_cycle', 'Monthly')),
                    float(s.get('Cycle Fee Amount', s.get('cycle_fee_amount', 0)) or 0),
                    float(s.get('Total Fee', s.get('school_fee_total', 0)) or 0),
                    float(s.get('Transport Fee', s.get('transport_fee_total', 0)) or 0),
                    s.get('Bank Name', s.get('bank_name', '')), 
                    str(s.get('Account No', s.get('account_no', ''))), 
                    s.get('IFSC Code', s.get('ifsc_code', ''))
                ))
                success_count += 1
            except Exception as e:
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    continue
                print(f"Error: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
        return jsonify({"success": True, "message": f"{success_count} students imported with photos!"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
# 📸 MANUAL REGISTRATION WITH PHOTO UPLOAD ENGINE
@app.route('/api/students/register-manual', methods=['POST'])
def register_manual_student():
    import os
    from flask import request, jsonify
    
    try:
        # 🎯 MULTIPART FORM DATA SE DATA AUR FILE DONO LO
        # Agar JSON hai to JSON se lo, agar FormData hai to form se lo
        if request.is_json:
            data = request.json
            photo_file = None
        else:
            data = request.form.to_dict()
            photo_file = request.files.get('student_photo')
        
        admission_no = data.get('admission_no', '').strip()
        roll_no = data.get('roll_no', '').strip()
        name = data.get('name', '')
        student_class = data.get('class', '')
        section = data.get('section', 'A')
        stream = data.get('stream', '')
        dob = data.get('dob', '')
        gender = data.get('gender', 'Male')
        category = data.get('category', 'General')
        aadhaar_no = data.get('aadhaar_no', '')
        samagra_id = data.get('samagra_id', '')
        father_name = data.get('father_name', '')
        mother_name = data.get('mother_name', '')
        whatsapp_no = data.get('whatsapp_no', '')
        address = data.get('address', '')
        fee_cycle = data.get('fee_cycle', 'Monthly')
        cycle_fee_amount = float(data.get('cycle_fee_amount', 0) or 0)
        school_fee_total = float(data.get('school_fee_total', 0) or 0)
        transport_fee_total = float(data.get('transport_fee_total', 0) or 0)
        bank_name = data.get('bank_name', '')
        account_no = data.get('account_no', '')
        ifsc_code = data.get('ifsc_code', '')

        if not admission_no or not name or not student_class:
            return jsonify({"success": False, "error": "Admission No, Name aur Class zaroori hain!"}), 400

        # 📸 PHOTO SAVE ENGINE - ENABLED
        if photo_file and photo_file.filename:
            upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'student_photos')
            
            # ✅ Class-Section folder create karo
            folder_name = f"{student_class}_{section}"
            target_folder = os.path.join(upload_folder, folder_name)
            
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            
            # ✅ Roll number se photo save karo (ID Card ke hisaab se)
            file_extension = os.path.splitext(photo_file.filename)[1].lower() or '.jpg'
            photo_filename = f"{roll_no}.jpg"
            photo_save_path = os.path.join(target_folder, photo_filename)
            photo_file.save(photo_save_path)
            print(f"📸 PHOTO SAVED: {photo_save_path}")

        # Database Insertion
        conn = get_db_connection()
        cursor = conn.cursor()

        if DATABASE_URL:
            execute_query(cursor, '''
                INSERT INTO students (
                    admission_no, roll_no, name, class, section, stream, dob, gender, category,
                    aadhaar_no, samagra_id, father_name, mother_name, parent_mobile, address, 
                    fee_cycle, cycle_fee_amount, school_fee_total, transport_fee_total, bank_name, account_no, ifsc_code
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                admission_no, roll_no, name, student_class, section, stream, dob, gender, category,
                aadhaar_no, samagra_id, father_name, mother_name, whatsapp_no, address,
                fee_cycle, cycle_fee_amount, school_fee_total, transport_fee_total, bank_name, account_no, ifsc_code
            ))
        else:
            execute_query(cursor, '''
                INSERT INTO students (
                    admission_no, roll_no, name, class, section, stream, dob, gender, category,
                    aadhaar_no, samagra_id, father_name, mother_name, parent_mobile, address, 
                    fee_cycle, cycle_fee_amount, school_fee_total, transport_fee_total, bank_name, account_no, ifsc_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                admission_no, roll_no, name, student_class, section, stream, dob, gender, category,
                aadhaar_no, samagra_id, father_name, mother_name, whatsapp_no, address,
                fee_cycle, cycle_fee_amount, school_fee_total, transport_fee_total, bank_name, account_no, ifsc_code
            ))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "🎉 Student profile successfully registered!"})

    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return jsonify({"success": False, "error": "❌ सावधान : यह Admission Number पहले से ही किसी और छात्र का है!"}), 400
        print("❌ Manual Registration Core Error Log:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500
    
# =====================================================================
# 💰 1. CLASS-WISE FEES REPORT WITH ROUTE/CLASS FILTERS API
# =====================================================================
@app.route('/api/payroll/fees-class-report', methods=['GET'])
def get_fees_class_report():
    target_class = request.args.get('class')
    target_section = request.args.get('section', 'All')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Base query string builder
    query = '''
        SELECT id, admission_no, roll_no, name, class, section, parent_mobile,
               school_fee_total, school_fee_paid, 
               transport_fee_total, transport_fee_paid,
               bank_name, account_no, ifsc_code,
               ((school_fee_total + transport_fee_total) - (school_fee_paid + transport_fee_paid)) as pending_balance
        FROM students 
        WHERE status = 'Active'
    '''
    params = []
    
    if target_class and target_class != 'All':
        query += " AND class = ?"
        params.append(target_class)
        
    if target_section and target_section != 'All':
        query += " AND section = ?"
        params.append(target_section)
        
    query += " ORDER BY pending_balance DESC"
    
    try:
        if DATABASE_URL:
            # PostgreSQL uses %s
            postgres_query = query.replace('?', '%s')
            execute_query(cursor, postgres_query, tuple(params))
        else:
            # SQLite uses ?
            execute_query(cursor, query, tuple(params))
        
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        conn.close()
        
        report_list = []
        for r in rows:
            report_list.append(dict(zip(columns, r)))
            
        return jsonify({"success": True, "report": report_list})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/payroll/send-bulk-fee-reminders', methods=['POST'])
def send_bulk_fee_reminders():
    import time
    data = request.json or {}
    student_ids = data.get('student_ids', [])
    
    if not student_ids:
        return jsonify({"success": False, "error": "Kripya kam se kam ek bache ko select karein!"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor, "SELECT school_name FROM school_settings WHERE id = 1")
    school_row = cursor.fetchone()
    school_name = school_row[0] if school_row else "Smart School ERP"
    
    success_sent = 0
    failed_sent = 0
    
    for s_id in student_ids:
        try:
            execute_query(cursor, 'SELECT name, (school_fee_total - school_fee_paid), (transport_fee_total - transport_fee_paid) FROM students WHERE id = ? AND status = "Active"', (s_id,))
            row = cursor.fetchone()
            if row:
                student_name, pending_school, pending_trans = row
                total_due = pending_school + pending_trans
                if total_due <= 0: continue
                
                # Telegram Message
                telegram_msg = (
                    f"🔔 *[फीस अनुस्मारक - {school_name.upper()}]*\n\n"
                    f"आदरणीय अभिभावक,\n\n{student_name} की फीस विवरण:\n"
                    f"📚 शैक्षणिक: ₹{pending_school}\n"
                    f"🚌 वाहन: ₹{pending_trans}\n\n"
                    f"💰 *कुल देय राशि:* *₹{total_due}*\n\n"
                    f"_System Powered by A.B.Digital Work_"
                )
                
                # ✅ Telegram function call
                send_telegram_msg(telegram_msg)
                success_sent += 1
                time.sleep(1) # Cooldown
        except Exception as e:
            print(f"⚠️ Telegram Bulk Error: {e}")
            failed_sent += 1
            
    conn.close()
    return jsonify({"success": True, "message": f"🎉 {success_sent} Reminders Telegram par bhej diye gaye!"})

# 📲 INSTANT FEE REMINDER API (UPDATED TEMPLATE)
@app.route('/api/fee-reminder', methods=['POST'])
def send_fee_reminder():
    data = request.json
    student_id = data.get('student_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. School Name Fetch
    execute_query(cursor, "SELECT school_name FROM school_settings WHERE id = 1")
    school_name_row = cursor.fetchone()
    school_name = school_name_row[0] if school_name_row else "SMART SCHOOL ERP"
    
    # 2. Student Data Fetch
    execute_query(cursor, '''
        SELECT name, 
               (school_fee_total - school_fee_paid) as pending_school, 
               (transport_fee_total - transport_fee_paid) as pending_trans 
        FROM students WHERE id = ?
    ''', (student_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        student_name, pending_school, pending_trans = row
        total_due = pending_school + pending_trans
        
        # 3. Naya Template (Wahi jo tumne manga tha)
        msg = (
            f"🔔 *[FEE REMINDER - {school_name.upper()}]*\n\n"
            f"नमस्त्ते ,\n\n"
            f"🍁 *Student Name:* {student_name}\n"
            f"📊 *Pending School Fee:* ₹{pending_school}\n"
            f"🚌 *Pending Van/Bus Fee:* ₹{pending_trans}\n\n"
            f"💰 *Total Outstanding Amount:* *₹{total_due}*\n\n"
            f"कृप्या फीस का भुगतान समय से करें.\n\n"
            f"_System Powered by A.B.Digital Work_"
        )
        
        try:
            send_telegram_msg(msg) # Yeh function global wala use karega
            return jsonify({"success": True, "message": "🎉 Reminder instantly sent to Telegram!"})
        except Exception as e:
            return jsonify({"success": False, "message": "Telegram Bot Offline!"})
            
    return jsonify({"success": False, "message": "Record not found!"})

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        execute_query(cursor, "SELECT school_name, school_address, school_email, school_mobile, school_logo, school_signature FROM school_settings WHERE id = 1")
        row = cursor.fetchone()
        
        execute_query(cursor, "SELECT school_latitude, school_longitude, allowed_radius_meters FROM attendance_rules WHERE id = 1")
        rules_row = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "school_name": row[0] if row else "Smart School ERP", 
            "school_address": row[1] if row else "", 
            "school_email": row[2] if row else "", 
            "school_mobile": row[3] if row else "", 
            "school_logo": row[4] if row else None, 
            "school_signature": row[5] if row else None,
            "school_latitude": rules_row[0] if rules_row else 24.7432,
            "school_longitude": rules_row[1] if rules_row else 78.8561,
            "school_location_radius": rules_row[2] if rules_row else 50
        })
        
    else:
        data = request.json or {}
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 1. School Profile Metadata Updates
            execute_query(cursor, '''
                UPDATE school_settings 
                SET school_name=?, school_address=?, school_email=?, school_mobile=?, school_logo=?, school_signature=? 
                WHERE id=1
            ''', (data.get('school_name'), data.get('school_address'), data.get('school_email'), data.get('school_mobile'), data.get('school_logo'), data.get('school_signature')))
            
            # 2. 🎯 EXACT KEYS INTERCEPTOR: Frontend aur backend keys ko tightly bind kiya
            new_lat = data.get('school_latitude') if data.get('school_latitude') is not None else data.get('latitude')
            new_lng = data.get('school_longitude') if data.get('school_longitude') is not None else data.get('longitude')
            new_rad = data.get('school_location_radius') if data.get('school_location_radius') is not None else data.get('allowed_radius_meters')
            
            # 3. Direct auto-sync parameter injection into rules table
            if new_lat is not None and new_lng is not None:
                execute_query("""
                    UPDATE attendance_rules 
                    SET school_latitude = ?, school_longitude = ?, allowed_radius_meters = ? 
                    WHERE id = 1
                """, (float(new_lat), float(new_lng), float(new_rad) if new_rad else 50.0))
                print(f"🚀 [AUTO-SYNC PERFECT] Attendance rules strictly synchronized: Lat={new_lat}, Lng={new_lng}")
                
            conn.commit()
        except Exception as sync_err:
            print("⚠️ Settings Rules Engine Fallback Logged Safely:", sync_err)
            
        conn.close()
        return jsonify({"success": True, "message": "⚙️ Settings and Attendance parameters saved globally!"})
    
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        execute_query(cursor, "SELECT id, password, role FROM users WHERE username = %s", (data.get('username'),))
    else:
        execute_query(cursor, "SELECT id, password, role FROM users WHERE username = ?", (data.get('username'),))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and bcrypt.check_password_hash(user[1], data.get('password')):
        token = jwt.encode({'user_id': user[0], 'role': user[2]}, SECRET_KEY, algorithm='HS256')
        return jsonify({"success": True, "token": token, "role": user[2]})
    return jsonify({"success": False, "message": "Galat Username/Password"})

@app.route('/api/send-verification', methods=['POST'])
def send_verification():
    global verification_store
    data = request.json
    username = data.get('username', '').strip().lower()
    
    if username == "admin":
        otp = str(random.randint(100000, 999999))
        verification_store['admin'] = otp
        
        # 🔐 OTP Message taiyaar kiya
        message = f"🔐 *[SECURITY ALERT]*\n\nYour Smart School ERP verification OTP is: *{otp}*\n\nValid for 5 minutes."
        
        # ✅ Telegram function call kiya
        send_telegram_msg(message)
        
        return jsonify({
            "success": True, 
            "message": "🎉 OTP tumhare Telegram par bhej diya gaya hai!"
        })
    
    return jsonify({"success": False, "message": "User nahi mila!"})

@app.route('/api/verify-and-reset', methods=['POST'])
def verify_and_reset():
    data = request.json
    username = data.get('username')
    otp = data.get('otp')
    new_password = data.get('new_password')
    if verification_store.get(username) == str(otp):
        hashed_pw = bcrypt.generate_password_hash(new_password).decode('utf-8')
        conn = get_db_connection()
        cursor = conn.cursor()
        execute_query("UPDATE users SET password = ? WHERE username = ?", (hashed_pw, username))
        conn.commit()
        conn.close()
        verification_store.pop(username, None)
        return jsonify({"success": True, "message": "🔒 Password successfully reset!"})
    return jsonify({"success": False, "message": "Galat verification code!"})

# 🧾 12. GET SPECIFIC TRANSACTION DETAILS FOR PRINTING
@app.route('/api/transactions/<receipt_no>', methods=['GET'])
def get_transaction_details(receipt_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch transaction along with student details
    execute_query(cursor, '''
        SELECT t.receipt_no, t.amount_paid, t.school_pay, t.transport_pay, t.next_due_date, t.date,
               s.name, s.father_name, s.class, s.section, s.admission_no,
               (s.school_fee_total + s.transport_fee_total) as total_target,
               ((s.school_fee_total + s.transport_fee_total) - (s.school_fee_paid + s.transport_fee_paid)) as total_due
        FROM fee_transactions t
        JOIN students s ON t.student_id = s.id
        WHERE t.receipt_no = ?
    ''', (receipt_no,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            "receipt_no": row[0], "amount_paid": row[1], "school_pay": row[2], "transport_pay": row[3],
            "next_due_date": row[4], "date": row[5], "student_name": row[6], "father_name": row[7],
            "class": row[8], "section": row[9], "admission_no": row[10], "total_fees": row[11], "balance": row[12]
        })
    return jsonify({"success": False, "message": "Receipt nahi mili"}), 404

# 🎯 IS ROUTE KO FILE KE EKDAM NEECHE COPIED-PASTE KAREIN
@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor, "SELECT * FROM students WHERE status = 'Active'")
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    
    student_list = []
    for r in rows:
        student_list.append(dict(zip(columns, r)))
    return jsonify(student_list)

# =====================================================================
# 🗑️ STUDENT PROFILE DELETE API ENDPOINT (YAHAN CHIPKAO ASAD BHAI)
# =====================================================================
@app.route('/api/students/delete/<int:student_id>', methods=['DELETE', 'OPTIONS'])
def delete_student(student_id):
    """Database se student ko uski ID ke mutabik safely delete karna"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True}), 200
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Check karte hain ki kya is ID ka bacha database mein hai
        execute_query(cursor, "SELECT name FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return jsonify({"success": False, "error": "Bhai, is ID ka koi student mila hi nahi!"}), 404
            
        student_name = student[0]
        
        # 2. Student ko delete karne ki query execute karte hain
        # Note: attendance_records table me CASCADE laga hua hai, toh uske saare records bhi safely drop ho jayenge
        execute_query(cursor, "DELETE FROM students WHERE id = ?", (student_id,))
        
        conn.commit()
        conn.close()
        
        print(f"🗑️ [A.B.Digital Work] Student {student_name} (ID: {student_id}) deleted successfully!")
        return jsonify({
            "success": True, 
            "message": f"Student {student_name} ko kamyabi se system se hata diya gaya hai!"
        }), 200
        
    except Exception as e:
        if 'conn' in locals(): 
            conn.close()
        print("❌ Student Delete Error Log:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

# 🎯 LOCATION: backend/app.py me file ke ekdam neeche app.run se theek pehle paste karein
@app.route('/api/students/update-profile', methods=['POST'])
def update_student_profile():
    data = request.json
    student_id = data.get('id')
    if not student_id:
        return jsonify({"success": False, "error": "Student ID missing hai!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Saare customized enterprise level fields ko update karne ki absolute query
        execute_query(cursor, '''
            UPDATE students 
            SET admission_no=?, roll_no=?, name=?, class=?, section=?, dob=?, gender=?, category=?,
                aadhaar_no=?, samagra_id=?, father_name=?, mother_name=?, parent_mobile=?, address=?, 
                fee_cycle=?, cycle_fee_amount=?, school_fee_total=?, transport_fee_total=?, 
                bank_name=?, account_no=?, ifsc_code=?
            WHERE id=?
        ''', (
            str(data.get('admission_no', '')), str(data.get('roll_no', '')), data.get('name', ''),
            str(data.get('class', '')), data.get('section', 'A'), data.get('dob', ''),
            data.get('gender', 'Male'), data.get('category', 'General'),
            str(data.get('aadhaar_no', '')), str(data.get('samagra_id', '')), data.get('father_name', ''),
            data.get('mother_name', ''), str(data.get('parent_mobile', '')), data.get('address', ''),
            data.get('fee_cycle', 'Monthly'), float(data.get('cycle_fee_amount', 0) or 0),
            float(data.get('school_fee_total', 0) or 0), float(data.get('transport_fee_total', 0) or 0),
            data.get('bank_name', ''), str(data.get('account_no', '')), data.get('ifsc_code', ''),
            student_id
        ))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "🎉 Student Profile Matrix Updated Successfully!"})
    except Exception as e:
        try:
            conn.close()
        except:
            pass
        return jsonify({"success": False, "error": str(e)}), 500

# 📜 FEE HISTORY API - Student ki complete payment history fetch karne ke liye
@app.route('/api/fee-history/<int:student_id>', methods=['GET'])
def get_fee_history(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Pehle check karo ki student exist karta hai ya nahi
        execute_query(cursor, "SELECT id, name FROM students WHERE id = ?", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return jsonify({"success": False, "error": "Student not found"}), 404
        
        # Student ki saari transactions fetch karo
        execute_query(cursor, '''
            SELECT receipt_no, school_pay, transport_pay, date, next_due_date, amount_paid
            FROM fee_transactions 
            WHERE student_id = ? 
            ORDER BY date DESC, id DESC
        ''', (student_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history_list = []
        for row in rows:
            history_list.append({
                "receipt_no": row[0] if row[0] else f"REC-{random.randint(100000, 999999)}",
                "school_fee_paid": float(row[1]) if row[1] else 0,
                "transport_fee_paid": float(row[2]) if row[2] else 0,
                "date": row[3] if row[3] else datetime.date.today().strftime("%Y-%m-%d"),
                "next_due_date": row[4] if row[4] else 'N/A',
                "amount_paid": float(row[5]) if row[5] else 0
            })
        
        print(f"✅ Found {len(history_list)} transactions for student {student_id}")
        
        return jsonify({"success": True, "history": history_list})
    
    except Exception as e:
        print(f"❌ Error in fee-history: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            conn.close()
        except:
            pass
        return jsonify({"success": False, "error": str(e)}), 500
    
# 🎯 Is route ko is tarah se tight filter par map kijiye:
@app.route('/api/staff', methods=['GET', 'POST'])
def manage_staff():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'GET':
        # Check karenge ki kya frontend ne koi specific mobile number bheja hai
        mobile_filter = request.args.get('mobile', '').strip()
        if mobile_filter:
            clean_mobile = mobile_filter[-10:] if len(mobile_filter) >= 10 else mobile_filter
            execute_query(cursor, "SELECT id, name, designation, mobile, base_salary, status FROM staff WHERE (mobile LIKE ? OR mobile LIKE ?) AND status = 'Active'", (f"%{clean_mobile}", f"%{clean_mobile}"))
        else:
            execute_query(cursor, "SELECT id, name, designation, mobile, base_salary, status FROM staff WHERE status = 'Active'")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([{"id": r[0], "name": r[1], "designation": r[2], "mobile": r[3], "base_salary": r[4], "status": r[5]} for r in rows])
    
    else:  # POST - Add new staff
        try:
            data = request.json
            name = data.get('name', '').strip()
            designation = data.get('designation', '').strip()
            mobile = str(data.get('mobile', '')).strip()
            base_salary = float(data.get('base_salary', 0))
            
            # ✅ VALIDATION: Check if all required fields are present
            if not name or not mobile:
                conn.close()
                return jsonify({"success": False, "error": "Name and Mobile are required!"}), 400
            
            # ✅ VALIDATION: Check if staff with same mobile already exists
            execute_query(cursor, "SELECT id FROM staff WHERE mobile = ? AND status = 'Active'", (mobile,))
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return jsonify({"success": False, "error": "Staff with this mobile number already exists!"}), 400
            
            # ✅ INSERT with all required fields
            if DATABASE_URL:
                execute_query(cursor, '''
                    INSERT INTO staff (name, designation, mobile, base_salary, status, pf_enabled, pf_percentage, available_cl) 
                    VALUES (%s, %s, %s, %s, 'Active', 0, 12.0, 12)
                ''', (name, designation, mobile, base_salary))
            else:
                execute_query(cursor, '''
                    INSERT INTO staff (name, designation, mobile, base_salary, status, pf_enabled, pf_percentage, available_cl) 
                    VALUES (?, ?, ?, ?, 'Active', 0, 12.0, 12)
                ''', (name, designation, mobile, base_salary))
            
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "Staff member registered successfully!"})
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            print(f"❌ Error adding staff: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

# ⚙️ 2. GET/UPDATE ATTENDANCE RULES API (FALLBACK SYSTEM FIXED ⚡)
@app.route('/api/attendance-rules', methods=['GET', 'POST'])
def manage_attendance_rules():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'GET':
        execute_query(cursor, "SELECT school_latitude, school_longitude, allowed_radius_meters, shift_start_time, late_buffer_minutes, shift_end_time FROM attendance_rules WHERE id = 1")
        row = cursor.fetchone()
        
        # Agar database me entry nahi mili toh safe default data bhejein
        if row is None:
            # Table me turant ek default row insert bhi kar dete hain taaki aage dikkat na ho
            execute_query(cursor, '''
                INSERT OR IGNORE INTO attendance_rules (id, school_latitude, school_longitude, allowed_radius_meters, shift_start_time, late_buffer_minutes, shift_end_time)
                VALUES (1, 24.7432, 78.8561, 50.0, '08:00', 15, '14:00')
            ''')
            conn.commit()
            conn.close()
            return jsonify({"latitude": 24.7432, "longitude": 78.8561, "radius": 50.0, "start_time": "08:00", "buffer": 15, "end_time": "14:00"})
            
        conn.close()
        return jsonify({"latitude": row[0], "longitude": row[1], "radius": row[2], "start_time": row[3], "buffer": row[4], "end_time": row[5]})
    else:
        data = request.json
        # Baki ka POST section pehle jaisa hi rahega...
        execute_query(cursor, '''
            UPDATE attendance_rules 
            SET school_latitude=?, school_longitude=?, allowed_radius_meters=?, shift_start_time=?, late_buffer_minutes=?, shift_end_time=? 
            WHERE id = 1
        ''', (float(data.get('latitude')), float(data.get('longitude')), float(data.get('radius', 50)), data.get('start_time'), int(data.get('buffer', 15)), data.get('end_time')))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Attendance rule-book configurations updated!"})

@app.route('/api/staff/mark-attendance', methods=['POST'])
def mark_staff_attendance():
    data = request.json or {}
    staff_id = data.get('staff_id')
    device_token = data.get('device_token', '').strip()
    
    try:
        user_lat = float(data.get('latitude', 0))
        user_lng = float(data.get('longitude', 0))
    except (ValueError, TypeError):
        user_lat = 0.0
        user_lng = 0.0
    
    if user_lat == 0.0 or user_lng == 0.0:
        return jsonify({
            "success": False,
            "status": "error",
            "message": "🚨 GPS Signal Missing! Kripya apne mobile ki Location Settings/Permission chalu karein aur page refresh karein."
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    school_lat = 0.0
    school_lng = 0.0
    allowed_radius = 50.0
    
    try:
        execute_query(cursor, "SELECT * FROM school_settings LIMIT 1")
        settings_row = cursor.fetchone()
        if settings_row:
            col_names = [desc[0].lower() for desc in cursor.description]
            for idx, name in enumerate(col_names):
                if 'school_latitude' in name or 'latitude' == name or 'lat' in name:
                    if settings_row[idx] is not None:
                        school_lat = float(settings_row[idx])
                if 'school_longitude' in name or 'longitude' == name or 'lng' in name or 'long' in name:
                    if settings_row[idx] is not None:
                        school_lng = float(settings_row[idx])
                if 'radius' in name or 'range' in name:
                    if settings_row[idx] is not None:
                        allowed_radius = float(settings_row[idx])
    except Exception as e:
        print("⚠️ school_settings fetch handled safely:", e)

    try:
        execute_query(cursor, "SELECT allowed_radius_meters, shift_start_time, late_buffer_minutes, late_fine_per_minute, shift_end_time, school_latitude, school_longitude FROM attendance_rules WHERE id = 1")
        time_rule = cursor.fetchone()
        if time_rule:
            rule_radius, start_time, buffer_min, late_fine_rate, end_time, rule_lat, rule_lng = time_rule
            if school_lat == 0.0 or school_lng == 0.0:
                school_lat = float(rule_lat) if rule_lat else 24.7432
                school_lng = float(rule_lng) if rule_lng else 78.8561
            if allowed_radius == 50.0 and rule_radius:
                allowed_radius = float(rule_radius)
        else:
            start_time, buffer_min, late_fine_rate, end_time = '08:00', 15, 0.0, '14:00'
            if school_lat == 0.0 or school_lng == 0.0:
                school_lat, school_lng = 24.7432, 78.8561
    except Exception as e:
        print("⚠️ attendance_rules missing execution fallback:", e)
        start_time, buffer_min, late_fine_rate, end_time = '08:00', 15, 0.0, '14:00'
        if school_lat == 0.0 or school_lng == 0.0:
            school_lat, school_lng = 24.7432, 78.8561
    
    print(f"--- LIVE ERP LOCATION VERIFIER ---")
    print(f"Active Operational Spot (Target Panel): Lat={school_lat}, Lng={school_lng} | Allowed Range={allowed_radius}M")
    print(f"Staff Punch In Spot (Device GPS): Lat={user_lat}, Lng={user_lng}")
    
    try:
        distance = calculate_distance_meters(school_lat, school_lng, user_lat, user_lng)
    except Exception as distance_err:
        conn.close()
        return jsonify({"success": False, "error": f"❌ Location computation mathematical error: {str(distance_err)}"}), 500

    if distance > allowed_radius:
        conn.close()
        return jsonify({
            "success": False, 
            "error": f"❌ Scope Bound Error: Aap campus range se {round(distance - allowed_radius)} meters door hain!"
        }), 403
        
    now = datetime.now()
    today_str = now.strftime("%d/%m/%Y")
    current_time_str = now.strftime("%H:%M:%S")
    current_hour = now.hour
    
    greeting = "Good Morning" if current_hour < 12 else "Good Afternoon"
    
    # ✅ FIXED - CURSOR ADDED
    execute_query(cursor, "SELECT name, mobile, device_token FROM staff WHERE id = ? AND status = 'Active'", (staff_id,))
    staff_row = cursor.fetchone()
    if not staff_row:
        conn.close()
        return jsonify({"success": False, "error": "Staff profile not active or found."}), 404
    staff_name, mobile, registered_device = staff_row
    
    if device_token:
        # ✅ FIXED - CURSOR ADDED
        execute_query(cursor, "SELECT name FROM staff WHERE device_token = ? AND id != ? AND status = 'Active'", (device_token, staff_id))
        existing_owner = cursor.fetchone()
        
        if existing_owner:
            conn.close()
            return jsonify({
                "success": False,
                "error": f"❌ Proxy Blocked! Yeh mobile pehle se Mr./Ms. {existing_owner[0]} ke naam par locked hai. Ek mobile se doosra staff punch nahi kar sakta!"
            }), 403

        # ✅ FIXED - CURSOR ADDED
        if not registered_device:
            execute_query(cursor, "UPDATE staff SET device_token = ? WHERE id = ?", (device_token, staff_id))
            conn.commit()
            print(f"🔒 [DEVICE RECOGNIZED & LOCKED]: Staff '{staff_name}' is now tightly linked to device footprint.")
        elif registered_device != device_token:
            conn.close()
            return jsonify({
                "success": False,
                "error": "❌ Access Denied: Proxy Blocked! Aap kisi doosre staff ke mobile se apni attendance nahi laga sakte hain."
            }), 403
    
    # ✅ FIXED - CURSOR ADDED
    execute_query(cursor, "SELECT id, check_in_time, check_out_time FROM staff_attendance WHERE staff_id = ? AND date = ?", (staff_id, today_str))
    attendance_record = cursor.fetchone()
    
    formatted_mobile = str(mobile).strip() if mobile else ""
    if formatted_mobile and not formatted_mobile.startswith('91') and len(formatted_mobile) == 10:
        formatted_mobile = f"91{formatted_mobile}"

    if not attendance_record:
        late_fine = 0.0
        status = "On-Time"
        late_minutes = 0
        
        try:
            start_h, start_m = map(int, start_time.split(':'))
            actual_start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            import datetime as dt_module
            buffer_deadline = actual_start + dt_module.timedelta(minutes=int(buffer_min))
            if now > buffer_deadline:
                status = "Late"
                late_minutes = round((now - actual_start).total_seconds() / 60)
                late_fine = late_minutes * float(late_fine_rate if late_fine_rate else 0)
        except Exception as e:
            print("⚠️ Late fine math calculation failed safely:", e)
        
        execute_query(cursor, "INSERT INTO staff_attendance (staff_id, date, check_in_time, status, late_fine, leave_type) VALUES (?, ?, ?, ?, ?, 'Present')",
                       (staff_id, today_str, current_time_str, status, late_fine))
        conn.commit()
        conn.close()
        
        whatsapp_msg = (
            f"✨ *{greeting} Mr. {staff_name}*,\n\n"
            f"Your *CAMPUS ENTRY* attendance has been marked successfully. ✅\n\n"
            f"⏱️ *Entry Time:* {current_time_str}\n"
            f"📊 *Status:* {status}\n"
        )
        if status == "Late":
            whatsapp_msg += (
                f"⚠️ *Delayed Minutes:* {late_minutes} Mins\n\n"
                f"🚨 *📢 ERP Rules Reminder:* स्कूल नियम के अनुसार *3 बार लेट* होने पर आपका *1 दिन का वेतनमान* कट जाएगा. कृप्या समय का विशेष ध्यान रखें! 🏫\n"
            )
        else:
            whatsapp_msg += f"\nHave a great and productive day ahead! 🏫\n"
        whatsapp_msg += f"_Powered by: A.B.Digital Work_"
        
        try:
            send_telegram_msg(whatsapp_msg)
        except Exception as e:
            print(f"⚠️ Telegram alert error: {e}")
            
        return jsonify({"success": True, "message": f"Campus Entry Complete! Status: {status}"})

    else:
        attn_id, check_in, check_out = attendance_record
        if check_out:
            conn.close()
            return jsonify({"success": False, "error": "🚨 Access Limit Blocked: Ek din me sirf 2 baar hi attendance lag sakti hai!"}), 400
            
        is_half_day = 0
        half_day_text = ""
        
        try:
            end_h, end_m = map(int, end_time.split(':'))
            shift_end_datetime = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
            if now < shift_end_datetime:
                is_half_day = 1
                half_day_text = "\n⚠️ *Status Updated:* Half-Day Rule Active (Early Departure Logged)"
        except Exception as e:
            print("⚠️ Half-day check runtime evaluation error:", e)
        
        execute_query(cursor, "UPDATE staff_attendance SET check_out_time = ?, is_half_day = ? WHERE id = ?", (current_time_str, is_half_day, attn_id))
        conn.commit()
        conn.close()
        
        evening_greeting = "Good Evening" if now.hour >= 16 else "Good Afternoon"
        whatsapp_msg = (
            f"✨ *{evening_greeting} Mr. {staff_name}*,\n\n"
            f"Your *CAMPUS EXIT* attendance has been logged successfully. 🚗\n\n"
            f"⏱️ *Exit Time:* {current_time_str}{half_day_text}\n\n"
            f"Thank you for your valuable services today! Have a safe journey home. 🙏\n"
            f"_Powered by: A.B.Digital Work_"
        )
        try:
            send_telegram_msg(whatsapp_msg)
        except Exception as e:
            print(f"⚠️ Telegram Error: {e}")
        
        return jsonify({"success": True, "message": "Campus Exit Complete!"})
    
# ==================== 📍 QR ATTENDANCE APIs (YAHAN SE PASTE KARO) ====================

@app.route('/api/attendance/today', methods=['GET'])
def get_today_attendance():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 🎯 BADLAAV 1: Date ka format DD/MM/YYYY kar diya jisse data filter ho sake
    import datetime
    today = datetime.date.today().strftime("%d/%m/%Y")
    
    # 🎯 BADLAAV 2: Table ka naam 'staff_attendance' kiya aur columns sahi kiye
    # Kyunki staff attendance lagne par data isi table me check_in_time ke sath jata hai
    execute_query(cursor, '''
        SELECT s.name, s.designation, sa.check_in_time, sa.check_out_time, sa.date
        FROM staff_attendance sa
        JOIN staff s ON sa.staff_id = s.id
        WHERE sa.date = ?
        ORDER BY sa.check_in_time DESC
    ''', (today,))
    
    rows = cursor.fetchall()
    conn.close()
    
    attendance = []
    for row in rows:
        attendance.append({
            "teacher_name": row[0],       # Staff/Teacher ka naam
            "teacher_subject": row[1],    # Designation (Post)
            "time": row[2],               # School Entry (Check-In) Time
            "distance": row[3] if row[3] else "--:--", # Exit (Check-Out) Time 
            "marked_at": row[4]           # Log Date (DD/MM/YYYY)
        })
    
    return jsonify({"success": True, "attendance": attendance})

@app.route('/api/attendance/mark', methods=['POST'])
def mark_qr_attendance():
    data = request.json or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table if not exists
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS qr_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT NOT NULL,
            teacher_name TEXT NOT NULL,
            teacher_subject TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            distance INTEGER,
            status TEXT,
            marked_at TEXT
        )
    ''')
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 🛡️ GLOBAL IP OVERRIDE ENGINE (Bina file dhoondhe panga khatam):
    # Agar frontend se data purani IP par aa raha hai, toh use live route par override karo
    target_teacher_id = data.get('teacher_id')
    
    # Check if already marked today
    execute_query(cursor, '''
        SELECT id FROM qr_attendance 
        WHERE teacher_id = ? AND date = ?
    ''', (target_teacher_id, today))
    
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "Attendance already marked for today!"})
    
    execute_query(cursor, '''
        INSERT INTO qr_attendance 
        (teacher_id, teacher_name, teacher_subject, date, time, latitude, longitude, distance, status, marked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        target_teacher_id,
        data.get('teacher_name'),
        data.get('teacher_subject'),
        today,
        data.get('time'),
        data.get('latitude'),
        data.get('longitude'),
        data.get('distance'),
        'present',
        now
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Attendance marked successfully!"})

# ==================== 📊 LIVE PAYROLL & ATTENDANCE DATA ENGINE ====================

# 🗓️ 1. TODAY'S ATTENDANCE DIRECTORY ROUTE
@app.route('/api/payroll/today-report', methods=['GET'])
def get_today_payroll_report():
    # Sahi tarika:
    today_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    execute_query(cursor, '''
        SELECT s.name, s.designation, sa.date, sa.check_in_time, sa.check_out_time, 
               sa.late_fine, sa.is_half_day, sa.leave_type, s.pf_enabled
        FROM staff_attendance sa
        JOIN staff s ON sa.staff_id = s.id
        WHERE sa.date = ?
    ''', (today_str,))
    rows = cursor.fetchall()
    conn.close()
    
    report = []
    for r in rows:
        report.append({
            "name": r[0], "designation": r[1], "date": r[2], 
            "entry_time": r[3] if r[3] else "N/A", "exit_time": r[4] if r[4] else "N/A",
            "late_fine": r[5], "half_day": "Yes" if r[6] == 1 else "No", 
            "leave": r[7], "pf": "Yes" if r[8] == 1 else "No"
        })
    return jsonify(report)

# 📅 2. MONTHLY MASTER SHEET REPORT ROUTE (3 LATE = 1 DAY SALARY CUT & DD/MM/YYYY FORMAT)
@app.route('/api/payroll/monthly-report', methods=['GET'])
def get_monthly_payroll_report():
    import datetime
    month_filter = request.args.get('month') 
    if not month_filter:
        month_filter = datetime.date.today().strftime("%Y-%m")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, '''
        SELECT s.id, s.name, s.designation, sa.date, sa.check_in_time, sa.check_out_time, 
               sa.late_fine, sa.is_half_day, sa.leave_type, s.pf_enabled, CAST(s.base_salary AS REAL)
        FROM staff_attendance sa
        JOIN staff s ON sa.staff_id = s.id
        WHERE sa.date LIKE ?
        ORDER BY s.id, sa.date ASC
    ''', (f"{month_filter}%",))
    rows = cursor.fetchall()
    conn.close()
    
    # Pre-calculate pure mahine ka late mapping array
    staff_late_rows = {}
    for r in rows:
        staff_id = r[0]
        is_late = float(r[6] or 0) > 0 
        if is_late:
            if staff_id not in staff_late_rows:
                staff_late_rows[staff_id] = []
            staff_late_rows[staff_id].append(r[3])

    report = []
    for r in rows:
        staff_id = r[0]
        monthly_salary = r[10] or 0.0
        db_date = r[3] 
        
        formatted_date = "N/A"
        if db_date:
            try:
                date_obj = datetime.datetime.strptime(db_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m/%Y")
            except Exception:
                formatted_date = db_date
        
        late_dates_list = staff_late_rows.get(staff_id, [])
        total_lates = len(late_dates_list)
        
        salary_cut_days = total_lates // 3
        one_day_salary = monthly_salary / 30.0
        total_calculated_fine = round(salary_cut_days * one_day_salary, 2)
        
        is_current_row_late = float(r[6] or 0) > 0
        final_row_fine = 0
        
        if is_current_row_late and total_lates >= 3:
            if db_date == late_dates_list[-1]:
                final_row_fine = total_calculated_fine
            else:
                final_row_fine = 0
        else:
            final_row_fine = 0

        report.append({
            "name": r[1], "designation": r[2], "date": formatted_date, 
            "entry_time": r[4] if r[4] else "N/A", "exit_time": r[5] if r[5] else "N/A",
            "late_fine": final_row_fine, "half_day": "Yes" if r[7] == 1 else "No", 
            "leave": r[8] if r[8] else "Present", "pf": "Yes" if r[9] == 1 else "No"
        })
        
    return jsonify(report)


# 💰 3. DYNAMIC PAY-SLIP & SALARY ACCOUNTING ENGINE (SYNCED WITH 3-LATE RULE)
@app.route('/api/payroll/payslip/<int:staff_id>', methods=['GET'])
def generate_staff_payslip_metrics(staff_id):
    import datetime
    month_filter = request.args.get('month', datetime.date.today().strftime("%Y-%m"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, "SELECT name, designation, base_salary, pf_enabled, pf_percentage, available_cl FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    if not staff:
        conn.close()
        return jsonify({"success": False, "error": "Staff member not found"}), 404
        
    name, designation, base_salary, pf_enabled, pf_percentage, available_cl = staff
    
    # Attendance details nikalenge exact calculation ke liye
    execute_query(cursor, '''
        SELECT late_fine, is_half_day 
        FROM staff_attendance 
        WHERE staff_id = ? AND date LIKE ?
    ''', (staff_id, f"{month_filter}%"))
    attendance_rows = cursor.fetchall()
    
    # 🎯 COUNT REAL LATES: Jin rows me late_fine entry mapped hai
    total_lates = sum(1 for row in attendance_rows if float(row[0] or 0) > 0)
    total_half_days = sum(1 for row in attendance_rows if row[1] == 1)
    days_present = len(attendance_rows)
    
    # 🔥 STRICT RULE MATH: 3 Late = 1 Day Salary Cut
    per_day_salary = base_salary / 30.0
    salary_cut_days = total_lates // 3
    total_late_fine = round(salary_cut_days * per_day_salary, 2)
    
    half_day_deduction = total_half_days * (per_day_salary * 0.5)
    
    pf_deduction_amount = 0.0
    if pf_enabled == 1:
        pf_deduction_amount = (base_salary * pf_percentage) / 100.0
        
    net_payout = base_salary - total_late_fine - half_day_deduction - pf_deduction_amount
    conn.close()
    
    return jsonify({
        "staff_id": staff_id, "name": name, "designation": designation, "month": month_filter,
        "base_salary": round(base_salary, 2), "days_present": days_present,
        "late_fines_deducted": total_late_fine, "half_days_count": total_half_days,
        "half_day_deductions": round(half_day_deduction, 2), "pf_deducted": round(pf_deduction_amount, 2),
        "net_salary_payout": round(max(0, net_payout), 2), "cl_remaining": available_cl
    })
    

# 📊 MANAGEMENT MONTHLY MASTER PAYROLL SHEET API (SYNCED WITH 3-LATE RULE)
@app.route('/api/payroll/management-sheet', methods=['GET'])
def get_management_payroll_sheet():
    import datetime
    month_filter = request.args.get('month', datetime.date.today().strftime("%Y-%m-%d")[:7])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, "SELECT id, name, designation, base_salary, pf_enabled, pf_percentage, available_cl FROM staff WHERE status = 'Active'")
    all_staff = cursor.fetchall()
    
    management_sheet = []
    
    for staff_id, name, designation, base_salary, pf_enabled, pf_percentage, available_cl in all_staff:
        execute_query(cursor, '''
            SELECT id, late_fine, is_half_day
            FROM staff_attendance 
            WHERE staff_id = ? AND date LIKE ?
        ''', (staff_id, f"{month_filter}%"))
        
        attendance_rows = cursor.fetchall()
        days_present = len(attendance_rows)
        
        # 🎯 COUNT REAL LATES USING LATE_FINE ATTRIBUTE OVERRIDE
        total_lates = sum(1 for row in attendance_rows if float(row[1] or 0) > 0)
        total_half_days = sum(1 for row in attendance_rows if row[2] == 1)
        
        # Advance checking
        try:
            execute_query(cursor, "SELECT SUM(amount) FROM staff_advance WHERE staff_id = ? AND date LIKE ?", (staff_id, f"{month_filter}%"))
            advance_row = cursor.fetchone()
            total_advance_taken = advance_row[0] or 0.0
        except Exception:
            total_advance_taken = 0.0
        
        per_day_salary = base_salary / 30.0
        
        # 🔥 EXACT RULE SYNC: 3 Late = 1 Day Salary Deduction
        late_salary_cuts_days = total_lates // 3
        late_rule_salary_deduction = round(late_salary_cuts_days * per_day_salary, 2)
        
        half_day_deduction_amount = total_half_days * (per_day_salary * 0.5)
        pf_deduction_amount = (base_salary * pf_percentage / 100.0) if pf_enabled == 1 else 0.0
        
        net_calculated = base_salary - late_rule_salary_deduction - half_day_deduction_amount - pf_deduction_amount - total_advance_taken
        
        management_sheet.append({
            "staff_id": staff_id,
            "name": name,
            "designation": designation,
            "base_salary": round(base_salary, 2),
            "days_present": days_present,
            "total_lates": total_lates,
            "late_salary_cut_amount": late_rule_salary_deduction,
            "half_days": total_half_days,
            "half_day_deduction": round(half_day_deduction_amount, 2),
            "pf_deduction": round(pf_deduction_amount, 2),
            "advance_taken": round(total_advance_taken, 2),
            "cl_remaining": available_cl,
            "base_net_payout": round(max(0, net_calculated), 2)
        })
        
    conn.close()
    return jsonify(management_sheet)

# =====================================================================
# 📊 INCOME & EXPENSES (ACCOUNTING SYSTEM) BACKEND CORE
# =====================================================================

# Note: Kripya dhyan dein ki jahan aapka database initialization function hai (jaise setup_database() ya db_init()), 
# wahan yeh table structure execute hona chahiye. Aap ise direct 'app.py' me routes ke sath register kar sakte hain:



@app.route('/api/accounting/add-expense', methods=['POST'])
def add_new_expense():
    import datetime # Import ko double-safe karne ke liye function ke andar hi rakh diya
    data = request.json or {}
    title = data.get('title')
    category = data.get('category')
    amount = data.get('amount')
    
    # 🎯 FIX: 'datetime.datetime.now()' ka sateek upyog kiya
    date = data.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
    payment_mode = data.get('payment_mode', 'Cash') # Cash, Bank, UPI
    vendor_name = data.get('vendor_name', 'Generic Vendor')
    remarks = data.get('remarks', '')

    if not title or not category or not amount:
        return jsonify({"success": False, "error": "Title, Category aur Amount bhejnah zaroori hai!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        execute_query(cursor, '''
            INSERT INTO expenses (title, category, amount, date, payment_mode, vendor_name, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, category, float(amount), date, payment_mode, vendor_name, remarks))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "🎉 Kharcha register ho gaya hai!"})
    except Exception as e:
        if 'conn' in locals(): conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 📊 UNIQUE INCOME & EXPENSES SYSTEM (BULLETPROOF PARSING ENGINE)
# =====================================================================

@app.route('/api/accounting/save-new-expense', methods=['POST'])
def unique_save_new_expense_route():
    import datetime
    data = request.json or {}
    title = data.get('title')
    category = data.get('category')
    amount = data.get('amount')
    date = data.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
    payment_mode = data.get('payment_mode', 'Cash')
    vendor_name = data.get('vendor_name', 'Generic Vendor')
    remarks = data.get('remarks', '')

    if not title or not category or not amount:
        return jsonify({"success": False, "error": "Title, Category aur Amount bhejna zaroori hai!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        execute_query(cursor, '''
            INSERT INTO expenses (title, category, amount, date, payment_mode, vendor_name, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(title), str(category), float(amount), str(date), str(payment_mode), str(vendor_name), str(remarks)))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "🎉 Kharcha register ho gaya hai!"})
    except Exception as e:
        if 'conn' in locals(): conn.close()
        print("❌ Save Expense Error Log:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/accounting/fetch-expenses-list', methods=['GET'])
def unique_fetch_expenses_list_route():
    category_filter = request.args.get('category', 'All')
    try:
        conn = get_db_connection()
        # Force regular tuple response to prevent dictionary model crashes
        conn.row_factory = None 
        cursor = conn.cursor()
        
        query = "SELECT id, title, category, amount, date, payment_mode, vendor_name, remarks FROM expenses"
        params = []
        
        if category_filter and category_filter != 'All':
            query += " WHERE category = ?"
            params.append(category_filter)
            
        query += " ORDER BY date DESC"
        
        execute_query(cursor, query, tuple(params))
        rows = cursor.fetchall()
        
        expenses_list = []
        for r in rows:
            expenses_list.append({
                "id": r[0],
                "title": r[1],
                "category": r[2],
                "amount": r[3],
                "date": r[4],
                "payment_mode": r[5],
                "vendor_name": r[6],
                "remarks": r[7]
            })
            
        conn.close()
        return jsonify({"success": True, "expenses": expenses_list})
    except Exception as e:
        if 'conn' in locals(): conn.close()
        print("❌ Fetch Expenses List Error Log:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/accounting/fetch-financial-summary', methods=['GET'])
def unique_fetch_financial_summary_route():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ✅ Check if expenses table exists and has data
        try:
            execute_query(cursor, "SELECT COALESCE(SUM(amount), 0) FROM expenses")
            res_exp = cursor.fetchone()
            total_expenses = float(res_exp[0]) if res_exp and res_exp[0] else 0.0
        except Exception as e:
            print(f"Expenses query error: {e}")
            total_expenses = 0.0
        
        try:
            execute_query(cursor, "SELECT COALESCE(SUM(school_fee_paid + transport_fee_paid), 0) FROM students")
            res_inc = cursor.fetchone()
            total_income = float(res_inc[0]) if res_inc and res_inc[0] else 0.0
        except Exception as sql_err:
            print(f"Income query error: {sql_err}")
            total_income = 0.0
        
        net_profit = total_income - total_expenses
        
        conn.close()
        return jsonify({
            "success": True,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_profit": net_profit
        })
    except Exception as e:
        print(f"Financial summary error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    
# 🗑️ STAFF PROFILE DELETE API ENDPOINT (FIXED FOR POST/DELETE METHODS)
@app.route('/api/staff/delete/<int:staff_id>', methods=['DELETE', 'POST', 'OPTIONS'])
def delete_staff_profile(staff_id):
    if request.method == 'OPTIONS':
        return jsonify({"success": True}), 200
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ✅ Check if staff exists
        execute_query(cursor, "SELECT id, name FROM staff WHERE id = ?", (staff_id,))
        staff = cursor.fetchone()
        
        if not staff:
            conn.close()
            return jsonify({"success": False, "error": "Staff not found"}), 404
        
        staff_name = staff[1]
        
        # ✅ Delete attendance records first
        execute_query(cursor, "DELETE FROM staff_attendance WHERE staff_id = ?", (staff_id,))
        
        # ✅ Delete staff
        execute_query(cursor, "DELETE FROM staff WHERE id = ?", (staff_id,))
        
        conn.commit()
        conn.close()
        
        print(f"🗑️ Staff deleted: {staff_name} (ID: {staff_id})")
        return jsonify({"success": True, "message": f"Staff {staff_name} deleted successfully!"}), 200
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        print(f"❌ Staff Delete Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    
# 📡 API ROUTE: FETCH STUDENTS FOR CLASS-WISE ID CARD GENERATION (SMART STREAM PARSER)
@app.route('/api/academic/class-students-cards', methods=['GET'])
def get_class_students_for_cards():
    from flask import request, jsonify
    import os
    
    full_class_name = request.args.get('class_name', '')
    section_name = request.args.get('section', 'All')
    
    if not full_class_name:
        return jsonify({"success": False, "error": "Class name select karna zaroori hai!"}), 400
        
    # 🎯 SMART TEXT PARSER: "Class 12th (Science)" -> Class="12", Stream="Science"
    target_class = full_class_name
    target_stream = ""
    
    if "11th" in full_class_name or "11" in full_class_name:
        target_class = "11"
    elif "12th" in full_class_name or "12" in full_class_name:
        target_class = "12"
    else:
        # Agar normal class room hai (1st to 10th), toh sirf number nikal lo
        target_class = ''.join(filter(str.isdigit, full_class_name)) or full_class_name

    if "(" in full_class_name:
        # Bracket ke andar se stream ka naam nikalo (e.g., Science, Commerce, Arts)
        target_stream = full_class_name.split("(")[1].replace(")", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Base query active students ke liye
    query = "SELECT id, name, father_name, roll_no, class, section, parent_mobile, address FROM students WHERE (class = ? OR class = ?) AND status = 'Active'"
    
    # Hame "12" aur "Class 12th" dono configurations safe side check karni hain
    params = [target_class, full_class_name]
    
    # Agar 11th ya 12th hai toh stream check bhi laga do condition me
    if target_stream:
        query += " AND (stream = ? OR stream IS NULL OR stream = '')"
        params.append(target_stream)
        
    if section_name and section_name != 'All':
        query += " AND section = ?"
        params.append(section_name)
        
    try:
        execute_query(cursor, query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        
        # 🎯 BASE URL for photos
        BASE_URL = "https://abd-school-backend.onrender.com"
        
        students_list = []
        for r in rows:
            display_class = r[4]
            if r[4] == '11' or r[4] == '12':
                display_class = f"Class {r[4]}th"
            
            # 🎯 DYNAMIC PHOTO URL GENERATE KARO
            roll_no = str(r[3]).strip() if r[3] else ''
            student_class = str(r[4]).strip() if r[4] else ''
            section = str(r[5]).strip() if r[5] else 'A'
            
            # ✅ Folder name: "10_B" format
            folder_name = f"{student_class}_{section}"
            
            # ✅ Photo URL: Roll No se
            photo_url = f"{BASE_URL}/static/student_photos/{folder_name}/{roll_no}.jpg"
            
            # ✅ FALLBACK 1: Agar roll_no se na mile to admission_no se try karo
            # (admission_no column additional hai, agar chahiye to)
            
            # ✅ FINAL FALLBACK: Placeholder
            # Photo check karne ke liye HEAD request
            # (Simple approach - direct URL bhejo, frontend handle kar lega)
            
            students_list.append({
                "id": r[0],
                "name": r[1],
                "father_name": r[2],
                "roll_no": r[3],
                "class": display_class,
                "section": r[5],
                "phone": r[6],
                "address": r[7],
                "photo": photo_url,  # ✅ DYNAMIC PHOTO URL
                "photo_fallback": "https://via.placeholder.com/150?text=No+Photo"  # Fallback for frontend
            })
            
        print(f"🎯 SYSTEM SYNC: Found {len(students_list)} active students for Class {target_class} {target_stream}")
        return jsonify({"success": True, "students": students_list})
        
    except Exception as e:
        if 'conn' in locals(): conn.close()
        print("❌ ID Card Fetch Operational Error:", str(e))
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive", "timestamp": datetime.now().isoformat()})
    
@app.route('/api/student-photos/<path:folder_and_file>')
def get_student_photo_bypass(folder_and_file):
    # 1. Pehle 'backend' folder ke parent (root directory) ka path nikalenge
    base_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 2. Main target static/student_photos folder path
    target_dir = os.path.join(base_project_dir, 'static', 'student_photos')
    
    # 3. Safe fallback agar static folder galti se backend/ ke andar hi bana ho
    if not os.path.exists(target_dir):
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(backend_dir, 'static', 'student_photos')
        
    return send_from_directory(target_dir, folder_and_file)

# =====================================================================
# 📅 1. FETCH DYNAMIC TIMETABLE ROUTINE BY CLASS ID & SECTION SECTION
# =====================================================================
@app.route('/api/timetable/fetch', methods=['GET'])
def fetch_class_timetable_relational():
    class_id = request.args.get('class_id', '')
    section = request.args.get('section', 'A')
    
    if not class_id:
        return jsonify({"success": False, "error": "Class ID select karna zaroori hai!"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        execute_query(cursor, '''
            SELECT t.id, t.day_of_week, t.period_number, t.start_time, t.end_time, sub.subject_name, s.name, t.subject_id, t.teacher_id
            FROM timetables t
            LEFT JOIN subjects sub ON t.subject_id = sub.id
            LEFT JOIN staff s ON t.teacher_id = s.id
            WHERE t.class_id = ? AND t.section_name = ?
            ORDER BY t.period_number ASC
        ''', (class_id, section))
        
        rows = cursor.fetchall()
        conn.close()
        
        timetable_data = []
        for r in rows:
            timetable_data.append({
                "id": r[0], "day": r[1], "period": r[2],
                "start_time": r[3], "end_time": r[4],
                "subject_name": r[5] or "No Subject", "teacher_name": r[6] or "Not Assigned",
                "subject_id": r[7], "teacher_id": r[8]
            })
            
        return jsonify({"success": True, "timetable": timetable_data})
    except Exception as e:
        if 'conn' in locals(): conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# =====================================================================
# 💾 2. SAVE OR UPDATE TIMETABLE PERIOD SLOT (WITH ANTI-CLASH ENGINE)
# =====================================================================
@app.route('/api/timetable/save-slot', methods=['POST'])
def save_timetable_slot_relational():
    data = request.json or {}
    class_id = data.get('class_id')
    section = data.get('section', 'A')
    day = data.get('day')
    period = int(data.get('period', 1))
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    subject_id = data.get('subject_id')
    teacher_id = data.get('teacher_id')
    
    if not class_id or not day or not period:
        return jsonify({"success": False, "error": "Required fields missing hain!"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 🛡️ ANTI-CLASH INTERCEPTOR: Ek hi time par teacher doosri class me na fas jaye
        if teacher_id:
            execute_query(cursor, '''
                SELECT c.class_name, t.section_name FROM timetables t
                JOIN classes c ON t.class_id = c.id
                WHERE t.day_of_week = ? AND t.period_number = ? AND t.teacher_id = ? AND NOT (t.class_id = ? AND t.section_name = ?)
            ''', (day, period, teacher_id, class_id, section))
            clash = cursor.fetchone()
            if clash:
                conn.close()
                return jsonify({
                    "success": False, 
                    "error": f"❌ Teacher Clash! Yeh teacher pehle se {clash[0]} - {clash[1]} ke isi period me busy hain!"
                }), 400

        # Upsert logic (Pehle se slot bana hai to update, nahi to fresh register)
        execute_query(cursor, '''
            SELECT id FROM timetables WHERE class_id = ? AND section_name = ? AND day_of_week = ? AND period_number = ?
        ''', (class_id, section, day, period))
        existing = cursor.fetchone()
        
        if existing:
            execute_query(cursor, '''
                UPDATE timetables 
                SET start_time=?, end_time=?, subject_id=?, teacher_id=?
                WHERE id = ?
            ''', (start_time, end_time, subject_id, teacher_id, existing[0]))
        else:
            execute_query(cursor, '''
                INSERT INTO timetables (class_id, section_name, day_of_week, period_number, start_time, end_time, subject_id, teacher_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (class_id, section, day, period, start_time, end_time, subject_id, teacher_id))
            
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "🎉 Period matrix saved seamlessly!"})
    except Exception as e:
        if 'conn' in locals(): conn.close()
        return jsonify({"success": False, "error": str(e)}), 500
    
# =====================================================================
# 🎙️ VOICE COMMAND COMMAND INTELLIGENT ROUTER (REGEX + GROQ HYBRID)
# =====================================================================

class VoiceRequest(BaseModel):
    text: str

@app.route('/api/voice-command', methods=['POST'])
def voice_command_endpoint():
    # Flask syntax ke hisab se json data extract kiya
    data = request.json or {}
    raw_text = data.get('text', '')
    text = raw_text.lower().strip()
    
    print(f"🎙️ Voice Command Received: {raw_text}")
    
    # 1. OPTION A: ULTRA-FAST REGEX MAPPING (100% Free & Micro-seconds)
    if re.search(r'(dashboard|overview|home|main page)', text):
        return jsonify({"intent": "NAVIGATE", "target": "/dashboard", "payload": {}})
        
    if re.search(r'(fee report|fees card|paisa report|class.*fee)', text):
        return jsonify({"intent": "NAVIGATE", "target": "/finance/reports", "payload": {}})

    if re.search(r'(fee jama|pay fee|fees collect|fees.*jama)', text):
        return jsonify({"intent": "ACTION", "target": "OPEN_FEE_MODAL", "payload": {}})

    if re.search(r'(receipt print|slip nikalo|print bill|receipt.*print)', text):
        return jsonify({"intent": "ACTION", "target": "TRIGGER_PRINT", "payload": {}})

    # 2. OPTION B: GROQ API LLAMA-3 FALLBACK (For complex or conversational commands)
    try:
        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": "Bearer YOUR_GROQ_API_KEY", # <-- Asad bhai yahan apni key daal lena
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        You are an ERP Voice Assistant. Categorize this command into a clean JSON object.
        Command: "{raw_text}"
        Allowed Intents: NAVIGATE, ACTION, WHATSAPP_MSG, NOTIFICATION, COMPLEX_JOB
        Output only raw JSON format, no explanation:
        {{
            "intent": "INTENT_NAME",
            "target": "TARGET_ROUTING_OR_FUNCTION",
            "payload": {{ "target_group": "pending_students", "action_type": "whatsapp" }}
        }}
        """
        
        response = requests.post(groq_url, headers=headers, json={
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }, timeout=4)
        
        import json
        result_text = response.json()['choices'][0]['message']['content'].strip()
        return jsonify(json.loads(result_text))
        
    except Exception as e:
        print(f"⚠️ Groq Engine Error/Timeout: {e}")
        return jsonify({"intent": "UNKNOWN", "target": "NONE", "payload": {}, "error": str(e)})
    
    
# ==========================================
# 🎯 CLASS-WISE ATTENDANCE ROUTES (YAHAN PASTE KAREIN)
# ==========================================

@app.route('/api/attendance/students', methods=['GET'])
def get_students_for_attendance():
    """Class, Section aur Date ke mutabik check karna aur students list nikalna"""
    class_name = request.args.get('class')
    section_name = request.args.get('section')
    # Frontend se selected date aayegi, agar nahi aayi toh aaj ki date auto-set hogi
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    if not class_name or not section_name:
        return jsonify({"error": "Class aur Section dono zaroori hain!"}), 400
        
    try:
        # 1. 📅 SUNDAY CHECK (Automated)
        # Python mein datetime.strptime se date parse karke day nikalte hain
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        if date_obj.weekday() == 6:  # 6 ka matlab Sunday hota hai bhai
            return jsonify({
                "status": "LOCKED",
                "message": "🔒 Attendance Locked: आज Sunday है, आज की छुट्टी है!"
            }), 200

        conn = get_db_connection()  # ← PostgreSQL use karega
        cursor = conn.cursor()

        # 2. 🏖️ HOLIDAY TABLE CHECK (Database validation)
        # Hum check karenge ki selected date kya chuttiyon ki range ke beech aati hai
        holiday_query = """
            SELECT holiday_name FROM holidays 
            WHERE ? BETWEEN start_date AND end_date
        """
        execute_query(cursor, holiday_query, (date_str,))
        holiday = cursor.fetchone()
        
        if holiday:
            conn.close()
            return jsonify({
                "status": "LOCKED",
                "message": f"🔒 Attendance Locked: Aaj {holiday[0]} ki wajah se school ki chutti hai!"
            }), 200

        # 3. 📝 NORMAL DAY: Agar Sunday/Holiday nahi hai, toh students ki list nikalo
        query = "SELECT id, roll_no, name FROM students WHERE class = ? AND section = ? ORDER BY roll_no ASC"
        execute_query(query, (class_name, section_name))
        students = cursor.fetchall()
        conn.close()
        
        student_list = []
        for row in students:
            student_list.append({
                "id": row[0],
                "roll_no": row[1],
                "name": row[2]
            })
            
        return jsonify({
            "status": "OPEN",
            "students": student_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/attendance/submit', methods=['POST'])
def submit_attendance():
    data = request.json
    class_name = data.get('class')
    section_name = data.get('section')
    date_str = data.get('date')
    records = data.get('records')
    
    if not all([class_name, section_name, date_str, records]):
        return jsonify({"error": "Data adhura hai!"}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Purani attendance delete karna
        execute_query(cursor, "DELETE FROM attendance_records WHERE class_name = ? AND section_name = ? AND date = ?", 
                       (class_name, section_name, date_str))
        
        absent_student_ids = []
        for record in records:
            execute_query("INSERT INTO attendance_records (student_id, class_name, section_name, date, status) VALUES (?, ?, ?, ?, ?)", 
                           (record['student_id'], class_name, section_name, date_str, record['status']))
            if record['status'] == 'Absent':
                absent_student_ids.append(record['student_id'])
        
        conn.commit()
        
        # 2. Telegram Trigger (Agar absent bachhe hain)
        if absent_student_ids:
            execute_query(cursor, "SELECT school_name FROM school_settings WHERE id = 1")
            school_name = cursor.fetchone()[0] if cursor.fetchone() else "Smart School ERP"
            
            placeholders = ', '.join(['?'] * len(absent_student_ids))
            execute_query(f"SELECT name FROM students WHERE id IN ({placeholders})", absent_student_ids)
            
            for (name,) in cursor.fetchall():
                msg = f"🧾 *[अनुपस्थिति सूचना - {school_name.upper()}]*\nनमस्ते, *{name}* आज स्कूल में अनुपस्थित (ABSENT) है।"
                try:
                    # ✅ TELEGRAM CALL (No Railway URL needed)
                    send_telegram_msg(msg)
                except Exception as e:
                    print(f"⚠️ Telegram Alert Error: {e}")
        
        conn.close()
        return jsonify({"message": "Attendance save ho gayi aur Telegram par alert bhej diya gaya!"}), 200
        
    except Exception as e:
        if 'conn' in locals(): conn.close()
        return jsonify({"error": str(e)}), 500

# Telegram Bot API Token
TELEGRAM_TOKEN = "8793915550:AAGK3RIR9PDQXkawoxaSp-69sfB5jge87A0"

@app.route('/webhook/8793915550:AAGK3RIR9PDQXkawoxaSp-69sfB5jge87A0', methods=['POST'])
def telegram_webhook():
    update = request.json
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
        # 🤖 Tumhara Command Logic
        if text.lower() == "/start":
            reply = "Namaste! Main tumhara Smart School ERP Assistant hoon. Main tumhari madad kar sakta hoon."
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={chat_id}&text={reply}")
            
        elif text.lower() == "/dashboard":
            # Yahan tum dashboard-stats fetch karke uska summary bhej sakte ho
            reply = "Dashboard Summary: Total Students - 50, Pending Fees - ₹20,000"
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={chat_id}&text={reply}")

    return jsonify({"status": "ok"}), 200

@app.route('/api/link-telegram', methods=['POST'])
def link_telegram():
    data = request.json
    phone = str(data.get('phone')).strip()
    telegram_id = str(data.get('telegram_id')).strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Database mein number search karke ID save karo
    execute_query("UPDATE students SET parent_telegram_id = ? WHERE parent_mobile = ?", (telegram_id, phone))
    
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "🎉 Aapka Telegram account link ho gaya hai!"})
    else:
        conn.close()
        return jsonify({"success": False, "error": "❌ Number hamare record mein nahi mila!"})
    
# =====================================================================
# 💰 ADVANCE SALARY MANAGEMENT APIs
# =====================================================================

@app.route('/api/payroll/add-advance', methods=['POST'])
def add_advance_payment():
    """Save advance payment for a staff member"""
    data = request.json
    staff_id = data.get('staff_id')
    amount = data.get('amount')
    purpose = data.get('purpose', 'Personal Advance')
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    if not staff_id or not amount:
        return jsonify({"success": False, "error": "Staff ID and amount required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if DATABASE_URL:
            execute_query(cursor, '''
                CREATE TABLE IF NOT EXISTS staff_advance (
                    id SERIAL PRIMARY KEY,
                    staff_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    purpose TEXT,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            execute_query(cursor, '''
                INSERT INTO staff_advance (staff_id, amount, purpose, date)
                VALUES (%s, %s, %s, %s)
            ''', (staff_id, amount, purpose, date))
        else:
            execute_query(cursor, '''
                CREATE TABLE IF NOT EXISTS staff_advance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    purpose TEXT,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            execute_query(cursor, '''
                INSERT INTO staff_advance (staff_id, amount, purpose, date)
                VALUES (?, ?, ?, ?)
            ''', (staff_id, amount, purpose, date))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Advance payment recorded"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route('/api/payroll/advance-history/<int:staff_id>', methods=['GET'])
def get_advance_history(staff_id):
    """Fetch all advance payments for a staff member"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Ensure table exists
        if DATABASE_URL:
            execute_query(cursor, '''
                CREATE TABLE IF NOT EXISTS staff_advance (
                    id SERIAL PRIMARY KEY,
                    staff_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    purpose TEXT,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            execute_query(cursor, '''
                SELECT id, staff_id, amount, purpose, date, created_at
                FROM staff_advance
                WHERE staff_id = %s
                ORDER BY date DESC, id DESC
            ''', (staff_id,))
        else:
            execute_query(cursor, '''
                CREATE TABLE IF NOT EXISTS staff_advance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    purpose TEXT,
                    date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            execute_query(cursor, '''
                SELECT id, staff_id, amount, purpose, date, created_at
                FROM staff_advance
                WHERE staff_id = ?
                ORDER BY date DESC, id DESC
            ''', (staff_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "staff_id": row[1],
                "amount": row[2],
                "purpose": row[3],
                "date": row[4],
                "created_at": row[5]
            })
        
        return jsonify(history)
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/payroll/download-advance-history/<int:staff_id>', methods=['GET'])
def download_advance_history(staff_id):
    """Download advance history as CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get staff name
    if DATABASE_URL:
        execute_query(cursor, "SELECT name FROM staff WHERE id = %s", (staff_id,))
    else:
        execute_query(cursor, "SELECT name FROM staff WHERE id = ?", (staff_id,))
    staff_row = cursor.fetchone()
    staff_name = staff_row[0] if staff_row else "Unknown"
    
    # Get advance history
    if DATABASE_URL:
        execute_query(cursor, '''
            SELECT date, amount, purpose, staff_id
            FROM staff_advance
            WHERE staff_id = %s
            ORDER BY date DESC
        ''', (staff_id,))
    else:
        execute_query(cursor, '''
            SELECT date, amount, purpose, staff_id
            FROM staff_advance
            WHERE staff_id = ?
            ORDER BY date DESC
        ''', (staff_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Amount (₹)', 'Purpose', 'Staff ID', 'Staff Name'])
    
    for row in rows:
        writer.writerow([row[0], f"₹{row[1]}", row[2], row[3], staff_name])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=advance_history_{staff_name}_{staff_id}.csv'}
    )  
    
# =====================================================================
# 👨‍👩‍👧 PARENT APP APIs
# =====================================================================

@app.route('/api/parent/login', methods=['POST'])
def parent_login():
    """Parent login with mobile + password (DOB)"""
    data = request.json
    mobile = data.get('mobile')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Ensure parent_accounts table exists
        execute_query(cursor, '''
            CREATE TABLE IF NOT EXISTS parent_accounts (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                mobile TEXT NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        ''')
        conn.commit()
        
        # ✅ Check if parent account exists
        execute_query(cursor, '''
            SELECT pa.id, pa.student_id, pa.password, pa.mobile, 
                   s.name as student_name, s.class, s.section, s.roll_no,
                   (s.school_fee_total - s.school_fee_paid) as pending_fees
            FROM parent_accounts pa
            JOIN students s ON pa.student_id = s.id
            WHERE pa.mobile = ?
        ''', (mobile,))
        row = cursor.fetchone()
        
        # ✅ If no account exists, create one automatically!
        if not row:
            # Get student with this mobile
            execute_query(cursor, '''
                SELECT id, name, class, section, roll_no, dob, 
                       (school_fee_total - school_fee_paid) as pending_fees
                FROM students 
                WHERE parent_mobile = ? AND status = 'Active'
            ''', (mobile,))
            student = cursor.fetchone()
            
            if student:
                # Auto-create parent account
                student_id = student[0]
                # Password is DOB (DDMMYYYY)
                dob_password = student[5].replace('/', '') if student[5] else '01012000'
                hashed = bcrypt.generate_password_hash(dob_password).decode('utf-8')
                
                execute_query(cursor, '''
                    INSERT INTO parent_accounts (student_id, mobile, password)
                    VALUES (?, ?, ?)
                ''', (student_id, mobile, hashed))
                conn.commit()
                
                # ✅ Now fetch the newly created account
                execute_query(cursor, '''
                    SELECT pa.id, pa.student_id, pa.password, pa.mobile, 
                           s.name as student_name, s.class, s.section, s.roll_no,
                           (s.school_fee_total - s.school_fee_paid) as pending_fees
                    FROM parent_accounts pa
                    JOIN students s ON pa.student_id = s.id
                    WHERE pa.mobile = ?
                ''', (mobile,))
                row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return jsonify({"success": False, "message": "❌ Mobile number not found. Please contact school."}), 401
        
        # Verify password (bcrypt)
        if bcrypt.check_password_hash(row[2], password):
            token = jwt.encode({'parent_id': row[0], 'student_id': row[1]}, SECRET_KEY, algorithm='HS256')
            return jsonify({
                "success": True,
                "token": token,
                "parent": {
                    "id": row[0],
                    "mobile": row[3],
                    "name": "Parent",
                    "student": {
                        "id": row[1],
                        "name": row[4],
                        "class": row[5],
                        "section": row[6],
                        "roll_no": row[7],
                        "pending_fees": row[8] or 0
                    }
                }
            })
        
        return jsonify({"success": False, "message": "❌ गलत पासवर्ड"}), 401
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/parent/verify', methods=['GET'])
def parent_verify():
    """Verify JWT token for parent"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        parent_id = payload.get('parent_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        execute_query(cursor, '''
            SELECT pa.id, pa.mobile, pa.student_id, s.name as student_name, 
                   s.class, s.section, s.roll_no,
                   (s.school_fee_total - s.school_fee_paid) as pending_fees
            FROM parent_accounts pa
            JOIN students s ON pa.student_id = s.id
            WHERE pa.id = ?
        ''', (parent_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                "success": True,
                "parent": {
                    "id": row[0],
                    "mobile": row[1],
                    "name": "Parent",
                    "student": {
                        "id": row[2],
                        "name": row[3],
                        "class": row[4],
                        "section": row[5],
                        "roll_no": row[6],
                        "pending_fees": row[7] or 0
                    }
                }
            })
        
        return jsonify({"success": False, "message": "Invalid token"}), 401
    except:
        return jsonify({"success": False, "message": "Invalid token"}), 401


@app.route('/api/parent/forgot-password', methods=['POST'])
def parent_forgot_password():
    """Send OTP for password reset"""
    data = request.json
    mobile = data.get('mobile')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor, "SELECT id FROM parent_accounts WHERE mobile = ?", (mobile,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"success": False, "message": "❌ मोबाइल नंबर नहीं मिला"}), 404
    
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    verification_store[mobile] = otp
    
    # Send OTP via email (console log for now)
    print(f"📧 OTP for {mobile}: {otp}")
    
    return jsonify({"success": True, "message": "✅ OTP sent to your registered email"})


@app.route('/api/parent/reset-password', methods=['POST'])
def parent_reset_password():
    """Reset password with OTP"""
    data = request.json
    mobile = data.get('mobile')
    otp = data.get('otp')
    new_password = data.get('new_password')
    
    if verification_store.get(mobile) != otp:
        return jsonify({"success": False, "message": "❌ OTP गलत है"}), 400
    
    hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')
    conn = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor, "UPDATE parent_accounts SET password = ? WHERE mobile = ?", (hashed, mobile))
    conn.commit()
    conn.close()
    
    verification_store.pop(mobile, None)
    return jsonify({"success": True, "message": "✅ पासवर्ड बदल गया"})


@app.route('/api/parent/notifications/<int:parent_id>', methods=['GET'])
def parent_notifications(parent_id):
    """Get all notifications for a parent"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ensure parent_notifications table exists
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS parent_notifications (
            id SERIAL PRIMARY KEY,
            parent_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            title TEXT,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'notice',
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    # Get student_id from parent
    execute_query(cursor, "SELECT student_id FROM parent_accounts WHERE id = ?", (parent_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": True, "notifications": []})
    
    student_id = row[0]
    
    execute_query(cursor, '''
        SELECT id, title, message, type, is_read, created_at
        FROM parent_notifications
        WHERE student_id = ? OR parent_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (student_id, parent_id))
    
    rows = cursor.fetchall()
    conn.close()
    
    notifications = []
    for r in rows:
        notifications.append({
            "id": r[0],
            "title": r[1] or "सूचना",
            "message": r[2],
            "type": r[3] or "notice",
            "is_read": bool(r[4]),
            "created_at": r[5].strftime("%Y-%m-%d %H:%M") if r[5] else str(r[5])
        })
    
    return jsonify({"success": True, "notifications": notifications})


@app.route('/api/parent/notification/read/<int:notification_id>', methods=['POST'])
def parent_mark_read(notification_id):
    """Mark notification as read"""
    conn = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor, "UPDATE parent_notifications SET is_read = TRUE WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route('/api/student/attendance/<int:student_id>', methods=['GET'])
def get_student_attendance(student_id):
    """Get attendance history for a student"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, '''
        SELECT date, status, class_name, section_name
        FROM attendance_records
        WHERE student_id = ?
        ORDER BY date DESC
        LIMIT 30
    ''', (student_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    attendance = []
    for r in rows:
        attendance.append({
            "date": r[0],
            "status": r[1],
            "class_name": r[2],
            "section_name": r[3]
        })
    
    return jsonify({"success": True, "attendance": attendance})


# =====================================================================
# 👨‍🏫 STAFF APP APIs
# =====================================================================

@app.route('/api/staff/login', methods=['POST'])
def staff_login():
    """Staff login with mobile + password"""
    data = request.json
    mobile = data.get('mobile')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, "SELECT id, name, designation, mobile, base_salary, password FROM staff WHERE mobile = ? AND status = 'Active'", (mobile,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"success": False, "message": "❌ Staff member not found"}), 401
    
    # Password check - if no password set, use mobile as default
    stored_password = row[5]
    if not stored_password or stored_password == '':
        # First time login - set default password
        hashed = bcrypt.generate_password_hash(mobile).decode('utf-8')
        conn = get_db_connection()
        cursor = conn.cursor()
        execute_query(cursor, "UPDATE staff SET password = ? WHERE id = ?", (hashed, row[0]))
        conn.commit()
        conn.close()
        stored_password = hashed
    
    if bcrypt.check_password_hash(stored_password, password):
        token = jwt.encode({'staff_id': row[0], 'mobile': mobile}, SECRET_KEY, algorithm='HS256')
        return jsonify({
            "success": True,
            "token": token,
            "staff": {
                "id": row[0],
                "name": row[1],
                "designation": row[2],
                "mobile": row[3],
                "base_salary": row[4]
            }
        })
    
    return jsonify({"success": False, "message": "❌ गलत पासवर्ड"}), 401


@app.route('/api/staff/verify', methods=['GET'])
def staff_verify():
    """Verify staff JWT token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        staff_id = payload.get('staff_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        execute_query(cursor, "SELECT id, name, designation, mobile, base_salary FROM staff WHERE id = ? AND status = 'Active'", (staff_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                "success": True,
                "staff": {
                    "id": row[0],
                    "name": row[1],
                    "designation": row[2],
                    "mobile": row[3],
                    "base_salary": row[4]
                }
            })
        
        return jsonify({"success": False, "message": "Invalid token"}), 401
    except:
        return jsonify({"success": False, "message": "Invalid token"}), 401


@app.route('/api/staff/notifications/<int:staff_id>', methods=['GET'])
def staff_notifications(staff_id):
    """Get staff notifications"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ensure staff_notifications table exists
    execute_query(cursor, '''
        CREATE TABLE IF NOT EXISTS staff_notifications (
            id SERIAL PRIMARY KEY,
            staff_id INTEGER NOT NULL,
            title TEXT,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'notice',
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    execute_query(cursor, '''
        SELECT id, title, message, type, is_read, created_at
        FROM staff_notifications
        WHERE staff_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (staff_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    notifications = []
    for r in rows:
        notifications.append({
            "id": r[0],
            "title": r[1] or "सूचना",
            "message": r[2],
            "type": r[3] or "notice",
            "is_read": bool(r[4]),
            "created_at": r[5].strftime("%Y-%m-%d %H:%M") if r[5] else str(r[5])
        })
    
    return jsonify({"success": True, "notifications": notifications})


@app.route('/api/staff/notification/read/<int:notification_id>', methods=['POST'])
def staff_mark_read(notification_id):
    """Mark staff notification as read"""
    conn = get_db_connection()
    cursor = conn.cursor()
    execute_query(cursor, "UPDATE staff_notifications SET is_read = TRUE WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route('/api/staff/attendance/today/<int:staff_id>', methods=['GET'])
def staff_attendance_today(staff_id):
    """Get today's attendance for staff"""
    today_str = datetime.now().strftime("%d/%m/%Y")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, '''
        SELECT id, check_in_time, check_out_time, status, late_fine
        FROM staff_attendance
        WHERE staff_id = ? AND date = ?
    ''', (staff_id, today_str))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return jsonify({
            "success": True,
            "attendance": {
                "id": row[0],
                "check_in_time": row[1],
                "check_out_time": row[2],
                "status": row[3],
                "late_fine": row[4]
            }
        })
    
    return jsonify({"success": True, "attendance": None})


@app.route('/api/staff/attendance/history/<int:staff_id>', methods=['GET'])
def staff_attendance_history(staff_id):
    """Get attendance history for staff"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, '''
        SELECT date, check_in_time, check_out_time, status
        FROM staff_attendance
        WHERE staff_id = ?
        ORDER BY date DESC
        LIMIT 30
    ''', (staff_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    attendance = []
    for r in rows:
        attendance.append({
            "date": r[0],
            "check_in_time": r[1] or "--:--",
            "check_out_time": r[2] or "--:--",
            "status": r[3] or "N/A"
        })
    
    return jsonify({"success": True, "attendance": attendance})


@app.route('/api/staff/attendance/checkin', methods=['POST'])
def staff_checkin():
    """Staff check-in"""
    data = request.json
    staff_id = data.get('staff_id')
    
    today_str = datetime.now().strftime("%d/%m/%Y")
    current_time = datetime.now().strftime("%H:%M:%S")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if already checked in today
    execute_query(cursor, "SELECT id FROM staff_attendance WHERE staff_id = ? AND date = ?", (staff_id, today_str))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        return jsonify({"success": False, "message": "Already checked in today"}), 400
    
    execute_query(cursor, '''
        INSERT INTO staff_attendance (staff_id, date, check_in_time, status)
        VALUES (?, ?, ?, 'Present')
    ''', (staff_id, today_str, current_time))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "✅ Check-in successful"})


@app.route('/api/staff/checkout', methods=['POST'])
def staff_checkout():
    """Staff check-out with Telegram notification"""
    data = request.json
    staff_id = data.get('staff_id')
    
    now = datetime.now()
    today_str = now.strftime("%d/%m/%Y")
    current_time_str = now.strftime("%H:%M:%S")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if checked in today
    execute_query(cursor, "SELECT id, check_in_time FROM staff_attendance WHERE staff_id = ? AND date = ? AND check_out_time IS NULL", (staff_id, today_str))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "❌ Aapne aaj entry nahi kiya hai. Pehle entry karein!"}), 400
    
    attendance_id = row[0]
    check_in_time = row[1]
    
    # Update check-out time
    execute_query(cursor, "UPDATE staff_attendance SET check_out_time = ? WHERE id = ?", (current_time_str, attendance_id))
    conn.commit()
    
    # Get staff details
    execute_query(cursor, "SELECT name, mobile FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    staff_name = staff[0] if staff else "Staff"
    
    conn.close()
    
    # ✅ TELEGRAM NOTIFICATION - Campus Exit
    try:
        telegram_msg = (
            f"🚗 *CAMPUS EXIT* ✅\n\n"
            f"👨‍🏫 *Staff:* {staff_name}\n"
            f"🆔 *ID:* {staff_id}\n"
            f"📅 *Date:* {today_str}\n"
            f"⏱️ *Check-in Time:* {check_in_time}\n"
            f"⏱️ *Exit Time:* {current_time_str}\n\n"
            f"_Powered by A.B.Digital Work_"
        )
        send_telegram_msg(telegram_msg)
        print(f"✅ Telegram exit notification sent for {staff_name}")
    except Exception as e:
        print(f"⚠️ Telegram exit notification failed: {e}")
    
    return jsonify({"success": True, "message": "🚗 Campus Exit successful!"})


@app.route('/api/staff/students/<int:staff_id>', methods=['GET'])
def staff_students(staff_id):
    """Get students assigned to a staff member"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get staff's class/section from staff table
    execute_query(cursor, "SELECT designation FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    
    # For demo - return all students if no specific class assigned
    execute_query(cursor, '''
        SELECT id, name, class, section, status
        FROM students
        WHERE status = 'Active'
        ORDER BY name
        LIMIT 20
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    students = []
    for r in rows:
        students.append({
            "id": r[0],
            "name": r[1],
            "class": r[2],
            "section": r[3],
            "status": "Present"  # Default status
        })
    
    return jsonify({"success": True, "students": students})


@app.route('/api/staff/dashboard-stats', methods=['GET'])
def staff_dashboard_stats():
    """Get staff dashboard statistics"""
    today_str = datetime.now().strftime("%d/%m/%Y")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total students
    execute_query(cursor, "SELECT COUNT(*) FROM students WHERE status = 'Active'")
    total_students = cursor.fetchone()[0] or 0
    
    # Present today
    execute_query(cursor, "SELECT COUNT(*) FROM staff_attendance WHERE date = ?", (today_str,))
    present_today = cursor.fetchone()[0] or 0
    
    # Absent today (total - present)
    absent_today = max(0, total_students - present_today)
    
    conn.close()
    
    return jsonify({
        "success": True,
        "stats": {
            "total_students": total_students,
            "present_today": present_today,
            "absent_today": absent_today
        }
    })
    
@app.route('/api/staff/update-profile/<int:staff_id>', methods=['PUT'])
def update_staff_profile(staff_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, '''
        UPDATE staff SET 
            roll = ?, subject = ?, class_teacher = ?, 
            assigned_class = ?, assigned_section = ?
        WHERE id = ?
    ''', (
        data.get('roll', 'Teacher'),
        data.get('subject', ''),
        data.get('class_teacher', ''),
        data.get('assigned_class', ''),
        data.get('assigned_section', ''),
        staff_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Staff profile updated"}) 

@app.route('/api/staff/assigned-students/<int:staff_id>', methods=['GET'])
def get_assigned_students(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, "SELECT assigned_class, assigned_section FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    
    if not staff or not staff[0]:
        conn.close()
        return jsonify({"success": True, "students": []})
    
    assigned_class, assigned_section = staff
    
    query = "SELECT id, name, roll_no, class, section FROM students WHERE class = ? AND status = 'Active'"
    params = [assigned_class]
    if assigned_section:
        query += " AND section = ?"
        params.append(assigned_section)
    
    execute_query(cursor, query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    students = []
    for r in rows:
        students.append({
            "id": r[0],
            "name": r[1],
            "roll_no": r[2],
            "class": r[3],
            "section": r[4]
        })
    
    return jsonify({"success": True, "students": students})

@app.route('/api/staff/qr-checkin', methods=['POST'])
def staff_qr_checkin():
    """QR Code se staff attendance mark karna"""
    data = request.json
    staff_id = data.get('staff_id')
    qr_data = data.get('qr_data', {})
    latitude = data.get('latitude', 0)
    longitude = data.get('longitude', 0)
    device_token = data.get('device_token', '')
    
    if not staff_id:
        return jsonify({"success": False, "message": "Staff ID not found"}), 400
    
    try:
        # ✅ 1. Staff validate karo
        conn = get_db_connection()
        cursor = conn.cursor()
        
        execute_query(cursor, "SELECT id, name, mobile, device_token FROM staff WHERE id = ? AND status = 'Active'", (staff_id,))
        staff = cursor.fetchone()
        
        if not staff:
            conn.close()
            return jsonify({"success": False, "message": "Staff not found or inactive"}), 404
        
        staff_name, mobile, registered_device = staff
        
        # ✅ 2. Device token check (Ek mobile se ek staff)
        if device_token:
            # Check if device is linked to another staff
            execute_query(cursor, "SELECT name FROM staff WHERE device_token = ? AND id != ? AND status = 'Active'", (device_token, staff_id))
            existing_owner = cursor.fetchone()
            if existing_owner:
                conn.close()
                return jsonify({"success": False, "message": f"❌ This device is already linked to {existing_owner[0]}"}), 403
            
            # Link device if not registered
            if not registered_device:
                execute_query(cursor, "UPDATE staff SET device_token = ? WHERE id = ?", (device_token, staff_id))
                conn.commit()
        
        # ✅ 3. Check if already checked in today
        today_str = datetime.now().strftime("%d/%m/%Y")
        execute_query(cursor, "SELECT id, check_in_time, check_out_time FROM staff_attendance WHERE staff_id = ? AND date = ?", (staff_id, today_str))
        existing = cursor.fetchone()
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if existing:
            attn_id, check_in, check_out = existing
            if check_out:
                conn.close()
                return jsonify({"success": False, "message": "❌ Already checked out today"}), 400
            
            # ✅ Already checked in -> Check out
            execute_query(cursor, "UPDATE staff_attendance SET check_out_time = ? WHERE id = ?", (current_time, attn_id))
            conn.commit()
            conn.close()
            
            # ✅ Telegram message for Check-out
            try:
                telegram_msg = (
                    f"🚗 *CAMPUS EXIT* ✅\n\n"
                    f"👨‍🏫 *Staff:* {staff_name}\n"
                    f"⏱️ *Exit Time:* {current_time}\n"
                    f"📱 *Mobile:* {mobile}\n\n"
                    f"_Powered by A.B.Digital Work_"
                )
                send_telegram_msg(telegram_msg)
            except Exception as e:
                print(f"Telegram error: {e}")
            
            return jsonify({"success": True, "message": "✅ Campus Exit successful!", "action": "checkout"})
        
        # ✅ 4. New check-in with location validation
        # Get school location from settings
        execute_query(cursor, "SELECT school_latitude, school_longitude, allowed_radius_meters FROM attendance_rules WHERE id = 1")
        rules = cursor.fetchone()
        
        if rules:
            school_lat, school_lng, allowed_radius = rules
            distance = calculate_distance_meters(school_lat, school_lng, latitude, longitude)
            
            if distance > (allowed_radius or 100):
                conn.close()
                return jsonify({
                    "success": False, 
                    "message": f"❌ You are {round(distance)} meters away from school (Allowed: {allowed_radius or 100}m)"
                }), 403
        
        # ✅ 5. Insert attendance (Check-in)
        execute_query(cursor, '''
            INSERT INTO staff_attendance (staff_id, date, check_in_time, status, leave_type)
            VALUES (?, ?, ?, 'Present', 'Present')
        ''', (staff_id, today_str, current_time))
        conn.commit()
        conn.close()
        
        # ✅ Telegram message for Check-in
        try:
            telegram_msg = (
                f"🏫 *CAMPUS ENTRY* ✅\n\n"
                f"👨‍🏫 *Staff:* {staff_name}\n"
                f"⏱️ *Entry Time:* {current_time}\n"
                f"📱 *Mobile:* {mobile}\n\n"
                f"_Powered by A.B.Digital Work_"
            )
            send_telegram_msg(telegram_msg)
        except Exception as e:
            print(f"Telegram error: {e}")
        
        return jsonify({"success": True, "message": "✅ Campus Entry successful!", "action": "checkin"})
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({"success": False, "message": str(e)}), 500
    
# =====================================================================
# 📚 BOARD SETTINGS API
# =====================================================================

@app.route('/api/board-settings', methods=['GET', 'POST'])
def manage_board_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        execute_query(cursor, "SELECT board_name, exam_pattern FROM board_settings LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                "success": True,
                "board_name": row[0],
                "exam_pattern": row[1]
            })
        return jsonify({"success": True, "board_name": "CBSE", "exam_pattern": "{}"})
    
    else:  # POST
        data = request.json
        board_name = data.get('board_name', 'CBSE')
        exam_pattern = data.get('exam_pattern', '{}')
        
        execute_query(cursor, '''
            UPDATE board_settings SET board_name = ?, exam_pattern = ? WHERE id = 1
        ''', (board_name, exam_pattern))
        
        if cursor.rowcount == 0:
            execute_query(cursor, '''
                INSERT INTO board_settings (board_name, exam_pattern) VALUES (?, ?)
            ''', (board_name, exam_pattern))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Board updated to {board_name}"})
    
# =====================================================================
# 📊 GRADE SYSTEM API
# =====================================================================

@app.route('/api/grade-system', methods=['GET', 'POST'])
def manage_grade_system():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        execute_query(cursor, "SELECT grade_name, min_percentage, max_percentage, description FROM grade_system ORDER BY min_percentage DESC")
        rows = cursor.fetchall()
        conn.close()
        
        grades = []
        for r in rows:
            grades.append({
                "grade": r[0],
                "min": r[1],
                "max": r[2],
                "description": r[3]
            })
        return jsonify({"success": True, "grades": grades})
    
    else:  # POST
        data = request.json
        grades = data.get('grades', [])
        
        # Delete existing
        execute_query(cursor, "DELETE FROM grade_system")
        
        # Insert new grades
        for g in grades:
            execute_query(cursor, '''
                INSERT INTO grade_system (grade_name, min_percentage, max_percentage, description)
                VALUES (?, ?, ?, ?)
            ''', (g['grade'], g['min'], g['max'], g['description']))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Grade system updated"})
    
# =====================================================================
# 📚 EXAM TEMPLATES API
# =====================================================================

@app.route('/api/exam-templates', methods=['GET'])
def get_exam_templates():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, "SELECT board_name, template_data FROM exam_templates WHERE is_active = TRUE")
    rows = cursor.fetchall()
    conn.close()
    
    templates = {}
    for r in rows:
        templates[r[0]] = r[1]
    
    return jsonify({"success": True, "templates": templates})

# =====================================================================
# 📝 CREATE EXAM API
# =====================================================================

@app.route('/api/exams/create', methods=['POST'])
def create_exam():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if exam already exists
        execute_query(cursor, '''
            SELECT id FROM exams WHERE exam_name = ? AND class = ? AND section = ? AND subject = ?
        ''', (data.get('exam_name'), data.get('class'), data.get('section'), data.get('subject')))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({"success": False, "error": "Exam already exists for this class and subject"}), 400
        
        # Generate exam_id
        exam_id = f"{data.get('exam_type', 'exam').lower().replace(' ', '_')}_{data.get('class')}"
        
        execute_query(cursor, '''
            INSERT INTO exams (exam_id, exam_name, class, section, subject, max_marks, passing_marks, weightage, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            exam_id,
            data.get('exam_name'),
            data.get('class'),
            data.get('section'),
            data.get('subject'),
            int(data.get('max_marks', 100)),
            int(data.get('passing_marks', 33)),
            int(data.get('weightage', 0)),
            data.get('date')
        ))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Exam created successfully"})
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500
    
# =====================================================================
# 📋 GET ALL EXAMS API
# =====================================================================

@app.route('/api/exams', methods=['GET'])
def get_all_exams():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    class_filter = request.args.get('class')
    subject_filter = request.args.get('subject')
    
    query = "SELECT id, exam_id, exam_name, class, section, subject, max_marks, passing_marks, weightage, date FROM exams"
    params = []
    conditions = []
    
    if class_filter:
        conditions.append("class = ?")
        params.append(class_filter)
    if subject_filter:
        conditions.append("subject = ?")
        params.append(subject_filter)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY date DESC"
    
    execute_query(cursor, query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    exams = []
    for r in rows:
        exams.append({
            "id": r[0],
            "exam_id": r[1],
            "exam_name": r[2],
            "class": r[3],
            "section": r[4],
            "subject": r[5],
            "max_marks": r[6],
            "passing_marks": r[7],
            "weightage": r[8],
            "date": r[9]
        })
    
    return jsonify({"success": True, "exams": exams})

# =====================================================================
# 👨‍🎓 GET STUDENTS FOR EXAM API
# =====================================================================

@app.route('/api/exams/<int:exam_id>/students', methods=['GET'])
def get_students_for_exam(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get exam details
    execute_query(cursor, '''
        SELECT id, exam_name, class, section, subject, max_marks FROM exams WHERE id = ?
    ''', (exam_id,))
    exam = cursor.fetchone()
    
    if not exam:
        conn.close()
        return jsonify({"success": False, "error": "Exam not found"}), 404
    
    # Get students
    execute_query(cursor, '''
        SELECT id, roll_no, name FROM students 
        WHERE class = ? AND section = ? AND status = 'Active'
        ORDER BY roll_no ASC
    ''', (exam[2], exam[3]))
    
    students = cursor.fetchall()
    
    # Get existing marks
    execute_query(cursor, '''
        SELECT student_id, marks_obtained, grade FROM exam_marks WHERE exam_id = ?
    ''', (exam_id,))
    marks = cursor.fetchall()
    
    conn.close()
    
    marks_dict = {}
    for m in marks:
        marks_dict[m[0]] = {"marks_obtained": m[1], "grade": m[2]}
    
    student_list = []
    for s in students:
        student_list.append({
            "id": s[0],
            "roll_no": s[1],
            "name": s[2],
            "marks_obtained": marks_dict.get(s[0], {}).get("marks_obtained", None),
            "grade": marks_dict.get(s[0], {}).get("grade", None)
        })
    
    return jsonify({
        "success": True,
        "exam": {
            "id": exam[0],
            "exam_name": exam[1],
            "class": exam[2],
            "section": exam[3],
            "subject": exam[4],
            "max_marks": exam[5]
        },
        "students": student_list
    })
    
# =====================================================================
# 💾 SAVE MARKS API
# =====================================================================

@app.route('/api/exams/save-marks', methods=['POST'])
def save_exam_marks():
    data = request.json
    exam_id = data.get('exam_id')
    marks_list = data.get('marks', [])
    
    if not exam_id:
        return jsonify({"success": False, "error": "Exam ID required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for m in marks_list:
            student_id = m.get('student_id')
            attendance = m.get('attendance', 0)
            
            # Update attendance in students table
            execute_query(cursor, '''
                UPDATE students SET attendance_days = ? WHERE id = ?
            ''', (attendance, student_id))
            
            # Save subject marks
            subject_marks = m.get('subject_marks', {})
            for subject_id, marks in subject_marks.items():
                theory = marks.get('theory', 0)
                practical = marks.get('practical', 0)
                internal = marks.get('internal', 0)
                total = theory + practical + internal
                
                execute_query(cursor, '''
                    INSERT INTO exam_marks (exam_id, student_id, subject_id, theory_marks, practical_marks, internal_marks, marks_obtained)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(exam_id, student_id, subject_id) 
                    DO UPDATE SET theory_marks = ?, practical_marks = ?, internal_marks = ?, marks_obtained = ?
                ''', (exam_id, student_id, subject_id, theory, practical, internal, total,
                      theory, practical, internal, total))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Marks saved successfully"})
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

def get_grade_from_percentage(percentage):
    """Helper function to get grade from percentage"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    execute_query(cursor, '''
        SELECT grade_name FROM grade_system 
        WHERE min_percentage <= ? AND max_percentage >= ?
        LIMIT 1
    ''', (percentage, percentage))
    
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else "F"

# =====================================================================
# 📊 GENERATE RESULT API
# =====================================================================

@app.route('/api/exams/generate-result/<int:exam_id>', methods=['POST'])
def generate_exam_result(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get exam details
        execute_query(cursor, '''
            SELECT id, class, section, subject, max_marks FROM exams WHERE id = ?
        ''', (exam_id,))
        exam = cursor.fetchone()
        
        if not exam:
            conn.close()
            return jsonify({"success": False, "error": "Exam not found"}), 404
        
        # Get all marks
        execute_query(cursor, '''
            SELECT student_id, marks_obtained FROM exam_marks WHERE exam_id = ?
        ''', (exam_id,))
        marks = cursor.fetchall()
        
        # Calculate results
        results = []
        for m in marks:
            student_id = m[0]
            marks_obtained = m[1]
            percentage = (marks_obtained / exam[4]) * 100 if exam[4] > 0 else 0
            grade = get_grade_from_percentage(percentage)
            
            results.append({
                "student_id": student_id,
                "marks_obtained": marks_obtained,
                "percentage": round(percentage, 2),
                "grade": grade
            })
        
        # Save results
        for r in results:
            execute_query(cursor, '''
                INSERT INTO exam_results (student_id, class, section, total_marks, obtained_marks, percentage, grade)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, class, section) 
                DO UPDATE SET total_marks = ?, obtained_marks = ?, percentage = ?, grade = ?
            ''', (
                r['student_id'], exam[1], exam[2], exam[4], r['marks_obtained'], r['percentage'], r['grade'],
                exam[4], r['marks_obtained'], r['percentage'], r['grade']
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Result generated", "results": results})
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500
    
# =====================================================================
# 🗑️ DELETE EXAM API
# =====================================================================

@app.route('/api/exams/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete marks first (cascade will handle)
        execute_query(cursor, "DELETE FROM exam_marks WHERE exam_id = ?", (exam_id,))
        execute_query(cursor, "DELETE FROM exams WHERE id = ?", (exam_id,))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Exam deleted successfully"})
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500
    
# =====================================================================
# 👨‍🏫 STAFF - ASSIGNED EXAMS API
# =====================================================================

@app.route('/api/staff/exams/<int:staff_id>', methods=['GET'])
def get_staff_exams(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get staff's assigned class
    execute_query(cursor, "SELECT assigned_class, assigned_section FROM staff WHERE id = ?", (staff_id,))
    staff = cursor.fetchone()
    
    if not staff or not staff[0]:
        conn.close()
        return jsonify({"success": True, "exams": []})
    
    assigned_class = staff[0]
    assigned_section = staff[1] or 'A'
    
    # Get exams for this class
    execute_query(cursor, '''
        SELECT id, exam_name, class, section, subject, max_marks, date 
        FROM exams 
        WHERE class = ? AND section = ?
        ORDER BY date DESC
    ''', (assigned_class, assigned_section))
    
    rows = cursor.fetchall()
    conn.close()
    
    exams = []
    for r in rows:
        exams.append({
            "id": r[0],
            "exam_name": r[1],
            "class": r[2],
            "section": r[3],
            "subject": r[4],
            "max_marks": r[5],
            "date": r[6]
        })
    
    return jsonify({"success": True, "exams": exams})

# =====================================================================
# 📊 GET EXAM PATTERN API
# =====================================================================

@app.route('/api/exam-pattern', methods=['GET'])
def get_exam_pattern():
    board = request.args.get('board', 'CBSE')
    class_name = request.args.get('class', 'All')
    subject_type = request.args.get('subject_type', 'All')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First try to get specific pattern
    execute_query(cursor, '''
        SELECT theory_marks, internal_marks FROM exam_patterns 
        WHERE board_name = ? AND class_name = ? AND subject_type = ?
    ''', (board, class_name, subject_type))
    
    row = cursor.fetchone()
    
    # If not found, try generic pattern
    if not row:
        execute_query(cursor, '''
            SELECT theory_marks, internal_marks FROM exam_patterns 
            WHERE board_name = ? AND class_name = 'All' AND subject_type = 'All'
        ''', (board,))
        row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return jsonify({
            "success": True,
            "board": board,
            "class": class_name,
            "theory_marks": row[0],
            "internal_marks": row[1],
            "total_marks": row[0] + row[1]
        })
    
    # Default fallback
    return jsonify({
        "success": True,
        "board": board,
        "class": class_name,
        "theory_marks": 80,
        "internal_marks": 20,
        "total_marks": 100
    })

# =====================================================================
# 📚 SUBJECTS MANAGEMENT API (YAHAN ADD KARO)
# =====================================================================

@app.route('/api/subjects/class/<class_name>', methods=['GET'])
def get_subjects_by_class(class_name):
    """Get all subjects assigned to a specific class"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Ensure class_subjects and subjects_master tables exist
        execute_query(cursor, '''
            CREATE TABLE IF NOT EXISTS subjects_master (
                id SERIAL PRIMARY KEY,
                subject_name TEXT NOT NULL,
                subject_code TEXT,
                max_marks INTEGER DEFAULT 100,
                is_compulsory INTEGER DEFAULT 1
            )
        ''')
        
        execute_query(cursor, '''
            CREATE TABLE IF NOT EXISTS class_subjects (
                id SERIAL PRIMARY KEY,
                class_name TEXT NOT NULL,
                subject_id INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                FOREIGN KEY(subject_id) REFERENCES subjects_master(id)
            )
        ''')
        conn.commit()
        
        # Get subjects for this class
        if DATABASE_URL:
            execute_query(cursor, '''
                SELECT sm.id, sm.subject_name, sm.max_marks, sm.subject_code, cs.display_order
                FROM subjects_master sm
                JOIN class_subjects cs ON sm.id = cs.subject_id
                WHERE cs.class_name = %s AND cs.is_active = 1
                ORDER BY cs.display_order ASC
            ''', (class_name,))
        else:
            execute_query(cursor, '''
                SELECT sm.id, sm.subject_name, sm.max_marks, sm.subject_code, cs.display_order
                FROM subjects_master sm
                JOIN class_subjects cs ON sm.id = cs.subject_id
                WHERE cs.class_name = ? AND cs.is_active = 1
                ORDER BY cs.display_order ASC
            ''', (class_name,))
        
        rows = cursor.fetchall()
        conn.close()
        
        subjects = []
        for r in rows:
            subjects.append({
                "id": r[0],
                "subject_name": r[1],
                "max_marks": r[2] or 100,
                "subject_code": r[3] or "",
                "display_order": r[4] or 0
            })
        
        return jsonify({"success": True, "subjects": subjects})
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        print(f"❌ Subjects fetch error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/subjects/add-to-class', methods=['GET', 'POST'])
def add_subject_to_class():
    """Add a subject to a class - Supports both GET and POST"""
    
    # GET se bhi data le sakte hain
    if request.method == 'GET':
        class_name = request.args.get('class_name')
        subject_name = request.args.get('subject_name')
        max_marks = request.args.get('max_marks', 100)
    else:
        data = request.json or {}
        class_name = data.get('class_name')
        subject_name = data.get('subject_name')
        max_marks = data.get('max_marks', 100)
    
    if not class_name or not subject_name:
        return jsonify({"success": False, "error": "Class and Subject required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 🔥 FIX: Pehle check karo subject exists ya nahi
        if DATABASE_URL:
            execute_query(cursor, "SELECT id FROM subjects_master WHERE subject_name = %s", (subject_name,))
        else:
            execute_query(cursor, "SELECT id FROM subjects_master WHERE subject_name = ?", (subject_name,))
        
        existing = cursor.fetchone()
        
        if existing:
            subject_id = existing[0]
        else:
            # Insert new subject
            if DATABASE_URL:
                execute_query(cursor, '''
                    INSERT INTO subjects_master (subject_name, max_marks) 
                    VALUES (%s, %s)
                ''', (subject_name, max_marks))
            else:
                execute_query(cursor, '''
                    INSERT INTO subjects_master (subject_name, max_marks) 
                    VALUES (?, ?)
                ''', (subject_name, max_marks))
            
            # Get new subject id
            if DATABASE_URL:
                execute_query(cursor, "SELECT id FROM subjects_master WHERE subject_name = %s", (subject_name,))
            else:
                execute_query(cursor, "SELECT id FROM subjects_master WHERE subject_name = ?", (subject_name,))
            subject_id = cursor.fetchone()[0]
        
        # 🔥 FIX: Class-subject mapping mein pehle check karo
        if DATABASE_URL:
            execute_query(cursor, '''
                SELECT id FROM class_subjects WHERE class_name = %s AND subject_id = %s
            ''', (class_name, subject_id))
        else:
            execute_query(cursor, '''
                SELECT id FROM class_subjects WHERE class_name = ? AND subject_id = ?
            ''', (class_name, subject_id))
        
        existing_mapping = cursor.fetchone()
        
        if not existing_mapping:
            # Add to class_subjects
            if DATABASE_URL:
                execute_query(cursor, '''
                    INSERT INTO class_subjects (class_name, subject_id, is_active) 
                    VALUES (%s, %s, 1)
                ''', (class_name, subject_id))
            else:
                execute_query(cursor, '''
                    INSERT INTO class_subjects (class_name, subject_id, is_active) 
                    VALUES (?, ?, 1)
                ''', (class_name, subject_id))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Subject '{subject_name}' added to {class_name}"})
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/subjects/remove-from-class', methods=['POST'])
def remove_subject_from_class():
    """Remove a subject from a class"""
    data = request.json
    class_name = data.get('class_name')
    subject_id = data.get('subject_id')
    
    if not class_name or not subject_id:
        return jsonify({"success": False, "error": "Class and Subject ID required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        execute_query(cursor, '''
            DELETE FROM class_subjects WHERE class_name = ? AND subject_id = ?
        ''', (class_name, subject_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Subject removed from class"})
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

# 2. AUR SABSE NICHE (File ka end yahan hona chahiye)
if __name__ == '__main__':
    # Render automatically PORT variable provide karta hai
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
