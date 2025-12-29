# src/utils/cleanup.py
import os
import glob
from src.config.settings import OUTPUT_DIR

def clean_logs():
    """
    ลบไฟล์ขยะที่เกิดจากการรัน Robocorp (log files, temp files)
    """
    patterns = [
        "*.robolog",
        "*.run",
        "log.html",
        "output.robolog"
    ]
    
    print(f"เริ่มทำความสะอาดโฟลเดอร์: {OUTPUT_DIR}")
    
    files_deleted = 0
    for pattern in patterns:
        full_pattern = os.path.join(OUTPUT_DIR, pattern)
        for file_path in glob.glob(full_pattern):
            try:
                os.remove(file_path)
                print(f"ลบ: {os.path.basename(file_path)}")
                files_deleted += 1
            except Exception as e:
                print(f"ไม่สามารถลบ {os.path.basename(file_path)} ได้: {e}")
                
    print(f"ทำความสะอาดเรียบร้อย! ลบไปทั้งหมด {files_deleted} ไฟล์")

if __name__ == "__main__":
    clean_logs()
