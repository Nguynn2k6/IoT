from flask import Flask, request, jsonify
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
    
    # 1. Bảng lưu log đèn giao thông
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            mode TEXT,
            light TEXT,
            remaining INTEGER
        )
    """)
    
    # 2. Bảng lưu tài khoản người dùng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    
    # 3. Bảng lưu lịch sử đăng nhập
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            login_time TEXT
        )
    """)
    
    # Tạo sẵn 2 tài khoản mẫu nếu database chưa có
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', '123456', 'admin')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('khach', '123456', 'viewer')")
    
    conn.commit()
    conn.close()

init_db()

# --- CÁC API ĐĂNG NHẬP ---

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
        # Lưu lịch sử đăng nhập
        cursor.execute("INSERT INTO login_history (username, login_time) VALUES (?, ?)", (username, now))
        conn.commit()
        conn.close()
        return jsonify({"message": f"Xin chào, {username}!", "role": role, "username": username}), 200
    
    conn.close()
    return jsonify({"message": "Sai tài khoản hoặc mật khẩu!"}), 401


# --- CÁC API HỆ THỐNG GIAO THÔNG ---

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
    logs = [{"id": r[0], "time": r[1], "mode": r[2], "light": r[3], "remaining": r[4]} for r in rows]
    return jsonify(logs), 200

@app.route("/api/override", methods=["POST"])
def set_override():
    global override_status
    data = request.json
    mode = data.get("mode")
    username = data.get("username") # Lấy tên user gửi lên từ giao diện
    
    # Kiểm tra quyền trong Database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or user[0] != 'admin':
        return jsonify({"message": "LỖI: Bạn không có quyền Admin!"}), 403

    if mode in ["peak_hour", "normal", "auto"]:
        override_status["mode"] = mode
        return jsonify({"message": f"Chuyển chế độ: {mode.upper()}", "status": override_status}), 200
    return jsonify({"message": "Chế độ không hợp lệ"}), 400

@app.route("/api/override", methods=["GET"])
def get_override():
    global override_status
    return jsonify(override_status), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)