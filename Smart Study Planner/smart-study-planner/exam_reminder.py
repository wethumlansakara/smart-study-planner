import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from datetime import datetime, timedelta
import mysql.connector
from dotenv import load_dotenv

# ------------------ LOAD ENV ------------------
load_dotenv()

# ------------------ CONFIGURATION ------------------
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'smart_study_planner')
}

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    raise SystemExit("❌ EMAIL_ADDRESS and EMAIL_PASSWORD must be set in .env")

# ------------------ DATABASE CONNECTION ------------------
db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor(dictionary=True)

# Send reminders for exams scheduled tomorrow
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
print("Checking exams for:", tomorrow)

# Fetch all users with exams tomorrow
cursor.execute("""
    SELECT u.id, u.name, u.email,
           GROUP_CONCAT(s.subject_name SEPARATOR ', ') AS subjects,
           MIN(s.exam_date) AS exam_date
    FROM subjects s
    JOIN users u ON s.user_id = u.id
    WHERE DATE(s.exam_date) = %s
    GROUP BY u.id
""", (tomorrow,))

exams = cursor.fetchall()
cursor.close()
db.close()

if not exams:
    print("No exams scheduled for tomorrow.")
else:
    print(f"Found {len(exams)} user(s) with exams tomorrow.")

# ------------------ SEND EMAILS ------------------
for exam in exams:
    name = exam['name']
    email = exam['email']
    subjects = exam['subjects']
    exam_date = exam['exam_date']

    msg = MIMEMultipart("alternative")
    msg['Subject'] = "📚 Exam Reminder: You Have Exams NearBy!"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email

    html_content = f"""
    <html>
      <body>
        <p>Hi {name},</p>
        <p>You have the following exam(s) scheduled for <b>{exam_date}</b>:</p>
        <ul>
    """

    for sub in subjects.split(','):
        html_content += f"<li>{sub.strip()}</li>"

    html_content += """
        </ul>
        <p>You are the best! 💪 We trust you — DO YOUR BEST 👌</p>
        <p>– Smart Study Planner</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✅ Reminder sent to {email}")
    except Exception as e:
        print(f"❌ Failed to send email to {email}: {e}")
