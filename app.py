from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)
DB_NAME = "traffic.db"

# Biến lưu trữ trạng thái override
override_status = {"mode": "auto"}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            mode TEXT,
            light TEXT,
            remaining INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            login_time TEXT
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', '123456', 'admin')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('khach', '123456', 'viewer')")
    
    conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    
    if user:
        role = user[0]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO login_history (username, login_time) VALUES (?, ?)", (username, now))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Xin chào, {username}!", "role": role, "username": username}), 200
    
    conn.close()
    return jsonify({"message": "Sai tài khoản hoặc mật khẩu!"}), 401

@app.route("/api/log", methods=["POST"])
def save_log():
    data = request.json
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO traffic_log (time, mode, light, remaining) VALUES (?, ?, ?, ?)", 
                   (now, data.get("mode"), data.get("light"), data.get("remaining")))
    conn.commit()
    conn.close()
    return jsonify({"message": "Saved successfully"}), 200

@app.route("/api/logs", methods=["GET"])
def get_logs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM traffic_log ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    
    logs = []
    for r in rows:
        light_state = r[3].lower()
        display_light = "yellow" if light_state == "yellow" else light_state
            
        logs.append({
            "id": r[0],
            "time": r[1],
            "mode": r[2],
            "light": display_light,
            "remaining": r[4]
        })
    return jsonify(logs), 200

@app.route("/api/override", methods=["POST"])
def set_override():
    global override_status
    data = request.json
    mode = data.get("mode")
    username = data.get("username")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or user[0] != 'admin':
        return jsonify({"message": "LỖI: Bạn không có quyền Admin!"}), 403

    # DANH SÁCH CÁC CHẾ ĐỘ ĐƯỢC PHÉP (Đã thêm cả 2 chế độ emergency)
    if mode in ["peak_hour", "normal", "auto", "emergency_main", "emergency_sub"]:
        override_status["mode"] = mode
        return jsonify({"message": f"Chuyển chế độ: {mode.upper()}", "status": override_status}), 200
    
    # Nếu gửi lên mã không nằm trong danh sách trên, sẽ báo lỗi này:
    return jsonify({"message": "Chế độ không hợp lệ"}), 400

@app.route("/api/override", methods=["GET"])
def get_override():
    global override_status
    return jsonify(override_status), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)