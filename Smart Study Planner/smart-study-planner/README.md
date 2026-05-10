# Smart Study Planner

An AI-powered study planner that uses **Prolog rules** to recommend study hours based on subject difficulty, priority, and how close the exam is. Built with Flask, MySQL, and a simple HTML/CSS/JS frontend.

## Features

- 🔐 User registration & login (sessions + hashed passwords)
- 📚 Add subjects with difficulty, exam date, weekly hours, and progress
- 🧠 Prolog rule engine recommends study hours per subject
- 📅 Auto-generated daily study schedule up to the exam
- 📧 Automated email reminder one day before each exam

## Tech Stack

- **Backend:** Python, Flask, Flask-CORS
- **AI Engine:** SWI-Prolog via `pyswip`
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript

## Prerequisites

- Python 3.9 or newer
- MySQL Server
- [SWI-Prolog](https://www.swi-prolog.org/Download.html) installed and on your PATH
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) (for the reminder script)

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/smart-study-planner.git
   cd smart-study-planner
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   mysql -u root -p < schema.sql
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and fill in your real values (database password, Gmail app password, etc.).

6. **Run the backend**
   ```bash
   python app.py
   ```
   The API will start on `http://localhost:5000`.

7. **Open the frontend**
   Open `UI.html` in your browser (or serve it with VS Code Live Server).

## Sending Exam Reminders

Run the reminder script manually:
```bash
python exam_reminder.py
```
It sends an email to every user who has an exam scheduled for tomorrow.

To run it automatically every day, schedule it with **cron** (Linux/macOS) or **Task Scheduler** (Windows).

## Project Structure

```
smart-study-planner/
├── app.py              # Flask backend
├── exam_reminder.py    # Email reminder script
├── prolog_engine.py    # Standalone Prolog wrapper (testing)
├── smart_study.pl      # Prolog rules
├── UI.html             # Frontend
├── schema.sql          # MySQL schema
├── requirements.txt    # Python dependencies
├── .env.example        # Env variables template
└── .gitignore
```

## How the Prolog Engine Works

Study hours are computed as:
```
Hours = base(difficulty) + bonus(priority) + bonus(urgency)
```
- `low / medium / high` difficulty → 2 / 4 / 6 base hours
- `low / medium / high` priority → +0 / +1 / +2 hours
- ≤7 days to exam → +2, ≤14 days → +1, otherwise +0

## License

MIT — feel free to use and modify.
