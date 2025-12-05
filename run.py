import requests
import sqlite3
from datetime import datetime, timezone

TOKEN_API = "<DMOJ ADMIN API TOKEN>"
DB_NAME = "dmoj.db"
STUDENTS = [
    "admin", "fer"
]

def db_init():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,            
            date TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
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
    ''')

    conn.commit()
    conn.close()

def get_or_create_user(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
              SELECT id 
              FROM user u
              WHERE u.name = ?
          """, (user,))
    result = cursor.fetchone()

    if result:
        conn.close()
        return result[0]
    else:
        cursor.execute("""
               INSERT INTO user (name)
               VALUES (?)
           """, (user,))
        uid = cursor.lastrowid
        conn.commit()
        conn.close()
        return uid

def get_user_last_tracking(uid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
    """
            SELECT max(date) 
            FROM tracking        
            WHERE user_id = ?
        """, (uid,)
   )
    result = cursor.fetchone()

    conn.commit()
    conn.close()
    return result[0] if (result and result[0]) else "1900-01-01"

def get_user_last_submission(uid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
    """
            SELECT max(s.date) 
            FROM submission s 
            LEFT JOIN tracking t ON s.tracking_id = t.id        
            LEFT JOIN user u ON t.user_id = u.id
            WHERE user_id = ?
        """, (uid,)
   )
    result = cursor.fetchone()

    conn.commit()
    conn.close()
    return result[0] if (result and result[0]) else None

def create_tracking(uid):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
    """
           INSERT INTO tracking (date, user_id)
           VALUES (?, ?)
        """, (datetime.now(timezone.utc).isoformat(),uid,)
    )
    tid = cursor.lastrowid

    conn.commit()
    conn.close()
    return tid

def create_submission(tid, submit):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    contest_name = None if not submit.get('contest') else submit.get('contest').get('key')
    contest_points = None if not submit.get('contest') else submit.get('contest').get('points')

    cursor.execute(
    """
           INSERT INTO submission (problem_id, problem_name, date, language, time, memory, points, result, contest_name, contest_points, tracking_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submit.get('id'), submit.get('problem'), submit.get('date'), submit.get('language'), submit.get('time'),
            submit.get('memory'), submit.get('points'), submit.get('result'), contest_name, contest_points, tid,
        )
    )

    conn.commit()
    conn.close()

def get_submit_data_by_user(user):
    url = f"https://dmoj.elpuig.xeill.net/api/v2/submissions?user={user}"

    try:
        response = requests.get(url, headers={
            "Authorization": f"Bearer {TOKEN_API}"
        })

        if response.status_code == 200:
            content = response.json()

            # TODO: if total_pages > 1, loop adding &page=x to the api query
            submits = content.get("data", {}).get("objects", [])

            uid = get_or_create_user(user)
            last_tracking = get_user_last_tracking(uid)
            tid = create_tracking(uid)

            recent = [s for s in submits if s.get('date') and s['date'] > last_tracking]
            for submit in recent:
                create_submission(tid, submit)

            if not recent: return {
                "total": 0,
                "last": get_user_last_submission(uid),
                "error": None
            }

            dates = [submit['date'] for submit in recent if submit['date'] is not None]
            return {
                "total": len(recent),
                "last": max(dates),
                "error": None
            }

    except requests.exceptions.RequestException as e:
        return {
            "total": 0,
            "last": None,
            "error": e
        }

if __name__ == "__main__":
    db_init()

    print("Requesting data for the suplied students.")
    print("  - All data will be stored into a SQLite BBDD.")
    print("  - The most recent data will de displayed and formatted to copy/paste it into a spreadsheet.\n")
    print("USER\tNEW SUBMISSIONS\tLAST SUBMISSION")

    for user in STUDENTS:
        data = get_submit_data_by_user(user)
        print(f"{user}\t"
              f"{data["total"]}\t"
              f"{"Never" if data["last"] is None else data["last"][:19].replace("T", " ")}"
              f"{"\t" if data["error"] is not None else ""}"
              f"{data["error"] if data["error"] is not None else ""}")

    print("\nDONE")