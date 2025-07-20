from flask import Flask, render_template, request
import sqlite3
import glob

app = Flask(__name__)

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

@app.route("/", methods=["GET"])
def index():
    vehicle_number = request.args.get("vehicle_number", "").strip()
    total = sum([query_all_dbs("SELECT COUNT(*) FROM vehicles")[i][0] for i in range(len(db_files))])
    checked = sum([query_all_dbs("SELECT COUNT(*) FROM vehicles WHERE status = 'ตรวจสอบแล้ว'")[i][0] for i in range(len(db_files))])
    remaining = total - checked
    percent = round((checked / total) * 100, 2) if total else 0

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
