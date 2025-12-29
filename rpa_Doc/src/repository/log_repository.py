# src/repository/log_repository.py
import json
import os
from typing import List, Dict

class LogRepository:
    def __init__(self):
        self.log_file = "output/pipeline_feedback.json"

    def save_log(self, entry: Dict):
        """Append log to JSON file"""
        logs = self.get_all_logs()
        logs.append(entry)
        # Keep last 50 logs only
        logs = logs[-50:]
        
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def get_all_logs(self) -> List[Dict]:
        """ดึงประวัติการถาม-ตอบ ทั้งหมด"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def get_last_log(self) -> Dict:
        """ดึง Log ล่าสุด"""
        logs = self.get_all_logs()
        return logs[-1] if logs else {}
