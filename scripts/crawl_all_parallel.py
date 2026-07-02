import subprocess
import sys
import os
import time

scripts = [
    "scripts/crawl_lich_tuan.py",
    "scripts/crawl_thong_bao.py",
    "scripts/crawl_dao_tao.py",
    "scripts/crawl_tuyen_sinh.py",
    "scripts/crawl_nckh.py",
    "scripts/crawl_tuyen_dung.py",
    "scripts/crawl_sinh_vien.py"
]

def run_all():
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    
    print("🚀 Bắt đầu khởi chạy tuần tự các chuyên mục cào dữ liệu (Áp dụng Skip-Existing)...")
    for idx, script in enumerate(scripts):
        print(f"\n▶️ [{idx+1}/{len(scripts)}] Khởi chạy script: {script}")
        # Chạy tuần tự và đợi hoàn thành
        p = subprocess.Popen([sys.executable, script], env=env)
        p.wait()
        # Delay 2 giây giữa các chuyên mục để tránh dồn dập request
        time.sleep(2)
        
    print("\n🎉 Tất cả chuyên mục chưa cào đã được hoàn tất thành công!")

if __name__ == "__main__":
    run_all()
