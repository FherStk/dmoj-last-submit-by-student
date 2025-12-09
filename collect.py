import requests
import sqlite3
import csv
from datetime import datetime, timezone
from config import API_TOKEN, STUDENTS, DB_NAME, db_init

NO_DATA = "   NO DATA"
DONE = "   DONE"

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

def api_request(user, page=0):
    url = f"https://dmoj.elpuig.xeill.net/api/v2/submissions?user={user}"
    if page > 0: url = f"{url}&page={page}"

    response = requests.get(url, headers={
        "Authorization": f"Bearer {API_TOKEN}"
    })

    if response.status_code == 200: return response.json()
    else: return None

def get_submit_data_by_user(user):
    try:
        content = api_request(user)
        if content:
            total_pages = content.get("data", {}).get("total_pages")

            for current_page in range(total_pages):
                content = api_request(user, current_page+1)
                submits = content.get("data", {}).get("objects", [])

                uid = get_or_create_user(user)
                last_tracking = get_user_last_tracking(uid)
                tid = create_tracking(uid)

                recent = [s for s in submits if s.get('date') and s['date'] > last_tracking]
                for submit in recent:
                    create_submission(tid, submit)

                if not recent: return [user, 0, get_user_last_submission(uid), None]

                dates = [submit['date'] for submit in recent if submit['date'] is not None]
                return [user, len(recent), dates if len(dates) == 1 else max(dates), None]

    except requests.exceptions.RequestException as e:
        return [user, 0, None, e]

def export_csv(data, filename):
    if not data:
        print(NO_DATA)
        return

    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["USER", "NEW SUBMISSIONS SINCE LAST COLLECTION", "LAST SUBMISSION", "ERROR MESSAGE"])

    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for line in data:
            writer.writerow(line)

    print(DONE)

if __name__ == "__main__":
    db_init()

    print("Requesting data for the suplied students.")
    print("  - All data will be stored into a SQLite BBDD.")
    print("  - A CSV file will be created into the current folder, containing the amount of submissions (and the last submission date) by user since the last collect.\n")

    data = []
    print("[1/2]: Collecting data from the DMOJ and storing into the BBDD.")
    print(f"   ", end="")
    for i, user in enumerate(STUDENTS):
        print(".", end="")
        data.append(get_submit_data_by_user(user))
    print(DONE.lstrip()) if len(data) > 1 else print(NO_DATA.lstrip())

    print("\n[2/2]: Creating the CSV file.")
    export_csv(data, f"collect-{datetime.today().strftime("%Y-%m-%d")}.csv")
