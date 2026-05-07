import requests
import time
from datetime import datetime

url = "https://iot-pxrb.onrender.com/api/log"
override_url = "https://iot-pxrb.onrender.com/api/override"

NORMAL_GREEN    = 20
PEAK_GREEN      = 35
YELLOW_TIME     = 3
RED_TIME        = 20

def is_peak_hour():
    now = datetime.now()
    hour = now.hour
    return (7 <= hour < 9) or (16 <= hour < 19)

def get_mode():
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
    data = {"mode": mode, "light": light, "remaining": remaining}
    try:
        response = requests.post(url, json=data, timeout=3)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Mode={mode.upper()} | Light={light.upper()} | Remaining={remaining}s "
              f"| HTTP {response.status_code}")
    except Exception as e:
        print(f"Lỗi gửi dữ liệu: {e}")

def run_interruptible_phase(light, duration, start_mode):
    """Chạy đếm lùi, kiểm tra lệnh khẩn cấp và loại bỏ độ trễ mạng"""
    for remaining in range(duration, 0, -1):
        start_time = time.time() # Bắt đầu bấm giờ
        
        current_mode = get_mode()
        if current_mode in ["emergency_main", "emergency_sub"]:
            return current_mode
        
        send_log(current_mode, light, remaining)
        
        # Chỉ ngủ phần thời gian còn lại để tròn 1 giây
        elapsed_time = time.time() - start_time
        sleep_time = 1.0 - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)
            
    return "done"

def traffic_light_loop():
    print("=" * 65)
    print("  Hệ thống Giao thông Thông minh (Đã tối ưu độ trễ mạng)")
    print("=" * 65)

    while True:
        mode = get_mode()

        # --- ƯU TIÊN TUYẾN CHÍNH ---
        if mode == "emergency_main":
            print("\n🚨 [BÁO ĐỘNG] XE CỨU THƯƠNG - KÍCH HOẠT XANH TUYẾN CHÍNH 🚨")
            while get_mode() == "emergency_main":
                start_time = time.time()
                send_log("emergency_main", "green", 99) 
                
                elapsed_time = time.time() - start_time
                sleep_time = 1.0 - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
            print("\n✅ ĐÃ HẾT TÌNH TRẠNG KHẨN CẤP, KHÔI PHỤC...")
            continue 

        # --- ƯU TIÊN TUYẾN PHỤ ---
        if mode == "emergency_sub":
            print("\n🚨 [BÁO ĐỘNG] XE CỨU THƯƠNG - KÍCH HOẠT XANH TUYẾN PHỤ 🚨")
            while get_mode() == "emergency_sub":
                start_time = time.time()
                send_log("emergency_sub", "red", 99) 
                
                elapsed_time = time.time() - start_time
                sleep_time = 1.0 - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
            print("\n✅ ĐÃ HẾT TÌNH TRẠNG KHẨN CẤP, KHÔI PHỤC...")
            continue 

        # --- CHU KỲ BÌNH THƯỜNG / CAO ĐIỂM ---
        green_time = get_green_time(mode)
        print(f"\n--- Chu kỳ mới | {mode.upper()} | Xanh={green_time}s Vàng={YELLOW_TIME}s Đỏ={RED_TIME}s ---")

        if run_interruptible_phase("green", green_time, mode) in ["emergency_main", "emergency_sub"]: continue
        if run_interruptible_phase("yellow", YELLOW_TIME, mode) in ["emergency_main", "emergency_sub"]: continue
        if run_interruptible_phase("red", RED_TIME, mode) in ["emergency_main", "emergency_sub"]: continue

if __name__ == "__main__":
    try:
        traffic_light_loop()
    except KeyboardInterrupt:
        print("\nĐã dừng chương trình.")