# ------------------ IMPORTS ------------------
import os
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pyswip import Prolog
import mysql.connector
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

# ------------------ LOAD ENV ------------------
load_dotenv()

# ------------------ APP SETUP ------------------
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-me-in-production')

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    SESSION_REFRESH_EACH_REQUEST=True
)

CORS(app,
     supports_credentials=True,
     origins=["http://localhost", "http://127.0.0.1", "http://localhost:9000",
              "http://127.0.0.1:5500", "http://localhost:5500"],
     allow_headers=["Content-Type", "Authorization",
                    "Accept", "X-Requested-With"],
     expose_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     max_age=3600)

# ------------------ PROLOG ------------------
try:
    prolog = Prolog()
    prolog.consult("smart_study.pl")
    print("✅ Prolog file loaded successfully")
except Exception as e:
    print(f"❌ Error loading Prolog file: {e}")
    prolog = None

# ------------------ DATABASE ------------------


def get_db_connection():
    try:
        print("🔗 Connecting to MySQL database...")
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'smart_study_planner'),
            autocommit=False
        )
        print("✅ Database connected")
        return connection
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

# ------------------ HELPERS ------------------


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            print("⚠️ Unauthorized access attempt")
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def calculate_hours_from_prolog(difficulty, priority, exam_date_str):
    fallback_hours = {'low': 2, 'medium': 4, 'high': 6}.get(difficulty, 2)
    if not prolog:
        return fallback_hours
    try:
        if exam_date_str:
            exam_dt = datetime.strptime(exam_date_str, '%Y-%m-%d')
            days_left = max(0, (exam_dt - datetime.now()).days)
        else:
            days_left = 14
        query = f"calculate_hours({difficulty},{priority},{days_left},Hours)"
        result = list(prolog.query(query))
        if result:
            return int(result[0]['Hours'])
        return fallback_hours
    except Exception as e:
        print(f"❌ Prolog error: {e}")
        return fallback_hours

# ------------------ ROUTES ------------------


@app.route('/health', methods=['GET'])
def health_check():
    db = get_db_connection()
    db_status = "connected" if db else "disconnected"
    if db:
        db.close()
    print(
        f"🩺 Health check: DB={db_status}, Prolog={'loaded' if prolog else 'not loaded'}")
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'prolog': 'loaded' if prolog else 'not loaded',
        'session': 'active' if 'user_id' in session else 'inactive',
        'session_user_id': session.get('user_id', 'none')
    })


@app.route('/check_auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        print(f"✅ User authenticated: {session['user_name']}")
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'name': session['user_name'],
                'email': session['user_email']
            }
        })
    print("⚠️ User not authenticated")
    return jsonify({'authenticated': False})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400
    hashed = hash_password(password)
    db = get_db_connection()
    if not db:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, email, phone FROM users WHERE email = %s AND password = %s",
        (email, hashed)
    )
    user = cursor.fetchone()
    cursor.close()
    db.close()
    if not user:
        print(f"❌ Login failed for email: {email}")
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    session.clear()
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_email'] = user['email']
    session['user_phone'] = user['phone']
    session.permanent = True
    print(f"✅ User logged in: {user['name']} ({email})")
    return jsonify({'success': True, 'user': user, 'message': 'Login successful'})


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True)
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    if not all([name, email, phone, password]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    hashed_password = hash_password(password)
    db = get_db_connection()
    if not db:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
            (name, email, phone, hashed_password)
        )
        db.commit()
        user_id = cursor.lastrowid
        session.clear()
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        session['user_phone'] = phone
        session.permanent = True
        print(f"🆕 New user registered: {name} ({email})")
        return jsonify({'success': True, 'user': {'id': user_id, 'name': name, 'email': email, 'phone': phone}, 'message': 'Registration successful'}), 201
    except mysql.connector.IntegrityError:
        db.rollback()
        print(f"❌ Registration failed: Email already registered ({email})")
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    finally:
        cursor.close()
        db.close()


@app.route('/logout', methods=['POST'])
def logout():
    user = session.get('user_name', 'Unknown')
    session.clear()
    print(f"🔒 User logged out: {user}")
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/get_hours', methods=['POST'])
@login_required
def get_hours():
    user_id = session['user_id']
    data = request.get_json(force=True)
    subject = data.get('subject', '').strip()
    difficulty = data.get('difficulty', '').lower()
    exam_date = data.get('exam_date', '')
    progress = int(data.get('progress', 0))
    try:
        weekly_hours = int(data.get('weekly_hours', 0))
        if weekly_hours < 0:
            weekly_hours = 0
    except:
        weekly_hours = 0
    if not subject or difficulty not in {'low', 'medium', 'high'}:
        return jsonify({'success': False, 'message': 'Invalid subject or difficulty'}), 400
    total_hours = calculate_hours_from_prolog(
        difficulty, difficulty, exam_date)
    hours_to_store = weekly_hours if weekly_hours > 0 else total_hours
    db = get_db_connection()
    if not db:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO subjects (user_id, subject_name, difficulty, hours, exam_date, progress, weekly_hours)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, subject, difficulty, hours_to_store, exam_date, progress, weekly_hours))
        db.commit()
        subject_id = cursor.lastrowid
        print(
            f"📝 Added subject: {subject}, Hours={hours_to_store}, Weekly={weekly_hours}")
        return jsonify({'success': True, 'subject_id': subject_id, 'hours': hours_to_store, 'weekly_hours': weekly_hours, 'message': f'Subject "{subject}" added successfully'})
    except Exception as e:
        db.rollback()
        print(f"❌ /get_hours error: {e}")
        return jsonify({'success': False, 'message': f'Database error: {e}'}), 500
    finally:
        cursor.close()
        db.close()


@app.route('/get_subjects', methods=['GET'])
@login_required
def get_subjects():
    user_id = session['user_id']
    db = get_db_connection()
    if not db:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, subject_name, difficulty, hours, weekly_hours,
               DATE_FORMAT(exam_date, '%Y-%m-%d') AS exam_date, progress
        FROM subjects
        WHERE user_id = %s
        ORDER BY exam_date ASC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    subjects = [{'id': r['id'], 'name': r['subject_name'], 'difficulty': r['difficulty'],
                 'hours': r['hours'], 'weekly_hours': r['weekly_hours'], 'examDate': r['exam_date'], 'progress': r['progress']} for r in rows]
    print(f"📄 Loaded {len(subjects)} subjects for user_id={user_id}")
    return jsonify({'success': True, 'subjects': subjects})


@app.route('/delete_subject/<int:subject_id>', methods=['DELETE'])
@login_required
def delete_subject(subject_id):
    user_id = session['user_id']
    db = get_db_connection()
    if not db:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM subjects WHERE id=%s AND user_id=%s", (subject_id, user_id))
    db.commit()
    affected = cursor.rowcount
    cursor.close()
    db.close()
    if affected == 0:
        print(
            f"⚠️ Delete failed: Subject {subject_id} not found for user {user_id}")
        return jsonify({'success': False, 'message': 'Subject not found or unauthorized'}), 404
    print(f"🗑️ Subject deleted: ID={subject_id}, User={user_id}")
    return jsonify({'success': True, 'message': 'Subject deleted successfully'})


@app.route('/generate_schedule', methods=['GET'])
@login_required
def generate_schedule():
    try:
        user_id = session['user_id']
        db = get_db_connection()
        if not db:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT subject_name, difficulty, hours, weekly_hours, exam_date, progress
            FROM subjects 
            WHERE user_id = %s
            ORDER BY exam_date ASC
        """, (user_id,))
        subjects = cursor.fetchall()
        cursor.close()
        db.close()
        if not subjects:
            print(f"📅 No subjects found for schedule for user_id={user_id}")
            return jsonify({'success': True, 'schedule': {}, 'message': 'No subjects found.'})

        today = datetime.now().date()
        schedule = {}
        print(f"📅 Generating schedule for {len(subjects)} subjects...")

        for subj in subjects:
            if subj['exam_date']:
                exam_date = subj['exam_date']
                if isinstance(exam_date, str):
                    exam_dt = datetime.strptime(exam_date, '%Y-%m-%d').date()
                else:
                    exam_dt = exam_date
                # Study only up to the day BEFORE exam
                days_until_exam = max((exam_dt - today).days - 1, 0)
            else:
                days_until_exam = 7

            weekly_hours = subj.get('weekly_hours', 0)
            total_hours = subj['hours']
            hours_to_allocate = weekly_hours if weekly_hours > 0 else total_hours
            hours_per_day = max(
                1, round(hours_to_allocate / max(days_until_exam, 1)))

            for i in range(days_until_exam + 1):
                day_date = today + timedelta(days=i)
                day_name = day_date.strftime('%A')
                if day_name not in schedule:
                    schedule[day_name] = []
                schedule[day_name].append({
                    'subject': subj['subject_name'],
                    'hours': hours_per_day,
                    'difficulty': subj['difficulty'],
                    'progress': subj['progress'],
                    'days_to_exam': days_until_exam - i
                })
        print(f"✅ Schedule generated successfully for user_id={user_id}")
        return jsonify({'success': True, 'schedule': schedule, 'message': f'Schedule generated for {len(subjects)} subjects'})

    except Exception as e:
        print(f"❌ /generate_schedule error: {e}")
        return jsonify({'success': False, 'message': f'Schedule generation error: {e}'}), 500


# ------------------ RUN ------------------
if __name__ == "__main__":
    print("🚀 Starting Smart Study Planner Backend...")
    app.run(debug=True, port=5000, host='0.0.0.0')
