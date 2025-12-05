import sqlite3

# IMPORTANT: please, do not push this file if contains sensible data.
#   git rm --cached config.p
#   git commit -m "Stop tracking 'config.py' to prevent accidental pushing of sensible data."

API_TOKEN = "<DMOJ ADMIN API TOKEN>"
DB_NAME = "dmoj.db"
STUDENTS = ["admin", "fer"]
REPORT_MIN_DATE = "2025-09-12"

def db_init():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,            
            date TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submission (
            id INTEGER PRIMARY KEY AUTOINCREMENT,        
            problem_id INTEGER,
            problem_name TEXT,
            date TEXT,
            language TEXT,
            time REAL,
            memory REAL,
            points INTEGER,
            result TEXT,
            contest_name TEXT,
            contest_points INTEGER,
            tracking_id INTEGER,
            FOREIGN KEY(tracking_id) REFERENCES tracking(id)
        )
    """)

    cursor.execute("""
        CREATE VIEW IF NOT EXISTS submissions_by_date AS  
            SELECT u.name as user, count(s.problem_name) as problems, substr(s.date,0,11) as date FROM submission s 
            LEFT JOIN tracking t ON s.tracking_id = t.id
            LEFT JOIN user u ON t.user_id = u.id
            GROUP BY u.name, substr(s.date,0,11);        
    """)

    conn.commit()
    conn.close()
