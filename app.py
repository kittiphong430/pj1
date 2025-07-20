
import csv
from datetime import datetime

def log_upload(filename, updated_count):
    log_file = "upload_log.csv"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([now, filename, updated_count])


from flask import Flask, render_template, request, redirect, flash
import sqlite3
import glob
import os
import pandas as pd
from flask_caching import Cache

from flask import Flask, render_template, request
import sqlite3
import glob
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# โหลดไฟล์ฐานข้อมูลทั้งหมด
db_files = sorted(glob.glob("vehicles_part*_updated.db"))

def query_all_dbs(query, params=()):
    results = []
    for db_file in db_files:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute(query, params)
        results.extend(cur.fetchall())
        conn.close()
    return results

def get_total_stats():
    total = sum([query_all_dbs("SELECT COUNT(*) FROM vehicles")[i][0] for i in range(len(db_files))])
    checked = sum([query_all_dbs("SELECT COUNT(*) FROM vehicles WHERE status = 'ตรวจสอบแล้ว'")[i][0] for i in range(len(db_files))])
    remaining = total - checked
    percent = round((checked / total) * 100, 2) if total else 0
    return total, checked, remaining, percent

@app.route("/", methods=["GET"])
def index():
    vehicle_number = request.args.get("vehicle_number", "").strip()

    # ดึงจาก cache ถ้ามี
    stats = cache.get("homepage_stats")
    if not stats:
        stats = get_total_stats()
        cache.set("homepage_stats", stats, timeout=300)  # แคชไว้ 5 นาที

    total, checked, remaining, percent = stats

    search_result = None
    if vehicle_number:
        rows = query_all_dbs("SELECT vehicle_number, status FROM vehicles WHERE vehicle_number = ?", (vehicle_number,))
        if rows:
            status = rows[0][1]
            if status == "ตรวจสอบแล้ว":
                msg = f"หมายเลข {vehicle_number} ได้รับการตรวจสอบแล้ว ✅"
            else:
                msg = f"หมายเลข {vehicle_number} ยังไม่ได้รับการตรวจสอบ ❌"
            search_result = {"status": status, "message": msg}
        else:
            search_result = {"status": "ไม่อยู่ในกลุ่มเป้าหมาย", "message": f"หมายเลข {vehicle_number} ไม่ได้อยู่ในกลุ่มเป้าหมาย 🔍"}

    return render_template("index.html", total=total, checked=checked, remaining=remaining,
                           percent=percent, search_result=search_result)

@app.route("/search")
def search():
    query = request.args.get("vehicle_number", "").strip()
    result = None
    if query:
        rows = query_all_dbs("SELECT vehicle_number, status FROM vehicles WHERE vehicle_number = ?", (query,))
        if rows:
            result = {"หมายเลขโครงรถ": rows[0][0], "สถานะ": rows[0][1]}
    return render_template("search.html", result=result)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    message = None
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
            updated = 0
            if "หมายเลขโครงรถ" in df.columns and "สถานะ" in df.columns:
                for db_file in db_files:
                    conn = sqlite3.connect(db_file)
                    cur = conn.cursor()
                    for _, row in df.iterrows():
                        vehicle_number = row["หมายเลขโครงรถ"]
                        status = row["สถานะ"]
                        cur.execute("UPDATE vehicles SET status = ? WHERE vehicle_number = ?", (status, vehicle_number))
                        updated += cur.rowcount
                    conn.commit()
                    conn.close()
                cache.delete("homepage_stats")  # เคลียร์ cache
                log_upload(uploaded_file.filename, updated)
                message = f"อัปเดตข้อมูลสำเร็จ {updated:,} รายการ"
            else:
                message = "ไฟล์ต้องมีคอลัมน์ 'หมายเลขโครงรถ' และ 'สถานะ'"
        else:
            message = "กรุณาอัปโหลดไฟล์ Excel (.xlsx) เท่านั้น"
    return render_template("upload.html", message=message)
