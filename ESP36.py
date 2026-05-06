import requests
import time
from datetime import datetime

url = "https://iot-pxrb.onrender.com/api/log"
override_url = "https://iot-pxrb.onrender.com/api/override"

# ============================================================
# Cấu hình thời gian đèn theo đề tài Mô hình 10
# ============================================================
NORMAL_GREEN    = 20
PEAK_GREEN      = 35
YELLOW_TIME     = 3
RED_TIME        = 20

def is_peak_hour():
    """Kiểm tra có phải giờ cao điểm không."""
    now = datetime.now()
    hour = now.hour
    # 7h–9h sáng hoặc 16h–19h chiều
    return (7 <= hour < 9) or (16 <= hour < 19)

def get_mode():
    """Lấy chế độ từ server. Ưu tiên chế độ được ghi đè (manual), sau đó mới tới giờ hệ thống"""
    try:
        response = requests.get(override_url, timeout=2)
        if response.status_code == 200:
            server_mode = response.json().get("mode")
            if server_mode != "auto":
                return server_mode
    except Exception:
        pass
        
    return "peak_hour" if is_peak_hour() else "normal"

def get_green_time(mode):
    return PEAK_GREEN if mode == "peak_hour" else NORMAL_GREEN

def send_log(mode, light, remaining):
    """Gửi trạng thái lên Flask server."""
    data = {
        "mode": mode,
        "light": light,
        "remaining": remaining
    }
    try:
        response = requests.post(url, json=data, timeout=3)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Mode={mode} | Light={light} | Remaining={remaining}s "
              f"| HTTP {response.status_code}")
    except Exception as e:
        print(f"Lỗi gửi dữ liệu: {e}")

def run_phase(light, duration, mode):
    """
    Chạy 1 pha đèn (xanh/vàng/đỏ), gửi log mỗi giây.
    """
    for remaining in range(duration, 0, -1):
        send_log(mode, light, remaining)
        time.sleep(1)

def traffic_light_loop():
    print("=" * 55)
    print("  Fake ESP32 - Đèn giao thông theo giờ cao điểm")
    print("  Giờ cao điểm: 7h-9h | 16h-19h")
    print("  Xanh bình thường: 20s | Xanh cao điểm: 35s")
    print("=" * 55)

    while True:
        mode = get_mode()
        green_time = get_green_time(mode)

        print(f"\n--- Chu kỳ mới | {mode.upper()} | "
              f"Xanh={green_time}s Vàng={YELLOW_TIME}s Đỏ={RED_TIME}s ---")

        # Pha XANH
        run_phase("green", green_time, mode)

        # Pha VÀNG
        run_phase("yellow", YELLOW_TIME, mode)

        # Pha ĐỎ
        run_phase("red", RED_TIME, mode)

if __name__ == "__main__":
    try:
        traffic_light_loop()
    except KeyboardInterrupt:
        print("\nĐã dừng chương trình.")