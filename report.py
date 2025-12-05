import sqlite3
import csv
from datetime import datetime, timedelta
from config import STUDENTS, DB_NAME, REPORT_MIN_DATE, db_init

NO_DATA = "   NO DATA"
DONE = "   DONE"

def collect_data():
    # dates -> users -> submissions
    min = REPORT_MIN_DATE if REPORT_MIN_DATE else get_min_date()
    max = get_max_date()
    if not min or not max:
        print(NO_DATA)
        return

    min_date = datetime.fromisoformat(min).date()
    max_date = datetime.fromisoformat(max).date()
    total_days = (max_date - min_date).days

    dates = dict()
    for i in range(total_days + 1):
        current = (min_date + timedelta(days=i)).strftime("%Y-%m-%d")

        dates[current] = dict()
        for student in STUDENTS:
            dates[current][student] = 0

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = get_submission_query("*")
    cursor.execute(f"{query[0]} AND date >= ?", query[1] + (min_date.isoformat(),))
    rows = cursor.fetchall()

    if not rows:
        print(NO_DATA)
        conn.close()
        return

    for row in rows:
        user, problems, date = row
        dates[date][user] = problems

    conn.close()
    print(DONE)
    return dates

def export_csv(data, filename):
    if not data:
        print(NO_DATA)
        return

    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        header = list(data)
        header.insert(0, "user")
        writer.writerow(header)

        users = dict()
        for date in data:
            for user in data[date]:
                if not user in users: users[user] = []
                users[user].append(data[date][user])

    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for user in users:
            line = list(users[user])
            line.insert(0, user)
            writer.writerow(line)

    print(DONE)

def get_submission_query(select):
    placeholders = ",".join(["?"] * len(STUDENTS))
    return (f"SELECT {select} FROM submissions_by_date WHERE user in ({placeholders})", tuple(STUDENTS))

def get_min_date():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = get_submission_query("min(date)")
    cursor.execute(query[0], query[1])
    result = cursor.fetchone()

    conn.commit()
    conn.close()
    return result[0] if (result and result[0]) else None

def get_max_date():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(date) FROM tracking;")
    result = cursor.fetchone()

    conn.commit()
    conn.close()
    return result[0] if (result and result[0]) else None

if __name__ == "__main__":
    db_init()

    print("Generating report for the suplied students.")
    print("  - All data will be loaded from a SQLite BBDD.")
    print("  - A CSV file will be created into the current folder.\n")

    print("[1/2]: Collecting data from the BBDD.")
    data = collect_data()

    print("\n[2/2]: Creating the CSV file.")
    export_csv(data, f"{datetime.today().strftime("%Y-%m-%d")}.csv")