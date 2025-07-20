from flask import Flask, render_template, request
import sqlite3
from datetime import datetime
import os
import glob

app = Flask(__name__)

# ใช้ path แบบ absolute เพื่อให้หา .db เจอบน Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_files():
    return sorted(glob.glob(os.path.join(BASE_DIR, "vehicles_part*.db")))

def get_all_connections():
    for db_file in get_db_files():
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        yield conn

# ฟังก์ชันสร้างตาราง vehicles หากยังไม่มี
def ensure_db_schema():
    for conn in get_all_connections():
        cur = conn.cursor()
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_number TEXT,
                    status TEXT
                )
            """)
            # เพิ่มข้อมูลตัวอย่างหากว่างเปล่า
            cur.execute("SELECT COUNT(*) FROM vehicles")
            if cur.fetchone()[0] == 0:
                cur.executemany("INSERT INTO vehicles (vehicle_number, status) VALUES (?, ?)", [
                    ("ABC123", "ตรวจสอบแล้ว"),
                    ("DEF456", "ยังไม่ตรวจ"),
                    ("GHI789", "ตรวจสอบแล้ว"),
                ])
            conn.commit()
        except Exception as e:
            print("DB init error:", e)
        finally:
            conn.close()

# เรียกเมื่อเริ่มต้น
ensure_db_schema()

@app.route('/')
def index():
    total = 0
    checked = 0
    for conn in get_all_connections():
        cur = conn.cursor()
        try:
            total += cur.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
            checked += cur.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'ตรวจสอบแล้ว'").fetchone()[0]
        except sqlite3.OperationalError as e:
            print(f"Database error in {conn}: {e}")
        conn.close()
    remaining = total - checked
    percent = round((checked / total) * 100, 2) if total else 0
    return render_template('index.html', total=total, checked=checked, remaining=remaining, percent=percent)

@app.route('/search')
def search():
    vehicle_number = request.args.get('vehicle_number')
    result = None
    for conn in get_all_connections():
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM vehicles WHERE vehicle_number = ?", (vehicle_number,))
            row = cur.fetchone()
            if row:
                result = dict(row)
                break
        except sqlite3.OperationalError as e:
            print(f"Database error in {conn}: {e}")
        finally:
            conn.close()
    return render_template('search.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
