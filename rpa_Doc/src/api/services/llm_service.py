import requests
import logging
from typing import Dict, Any
from src.config.settings import RAG_CONFIG, OLLAMA_BASE_URL
from src.core.ollama_queue import OllamaQueue

logger = logging.getLogger("rag.llm")

class LLMService:
    def __init__(self):
        self.ollama_url = f"{OLLAMA_BASE_URL}/api/generate"
        self.model = RAG_CONFIG["model"]
        self.connect_timeout = 10
        self.read_timeout = 240
        self.ollama_queue = OllamaQueue()

    def call_ollama(self, prompt: str) -> str:
        def _request():
            r = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0, # ลดความเพ้อเจ้อ (Creativity) เพื่อให้แม่นยำ
                        "num_ctx": 2048,    # 3b รับได้สบาย และพอดีกับ context
                        "num_predict": 400, # จำกัดความยาวคำตอบไม่ให้เวิ่นเว้อ
                        "top_k": 20,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                },
                timeout=(self.connect_timeout, self.read_timeout)
            )
            r.raise_for_status()
            return r.json().get("response", "").strip()

        # submit returns result_q.get() directly in our src/core/ollama_queue.py
        result = self.ollama_queue.submit(_request)
        if isinstance(result, Exception):
            logger.error(f"LLM Error: {result}")
            raise result
        return result

    def build_document_prompt(self, context: str, question: str) -> str:
        return (
            "### คำสั่ง: คุณคือผู้เชี่ยวชาญด้านกฎหมายภาษี\n"
            "ตอบคำถามโดยใช้ข้อมูลจาก 'ข้อมูลอ้างอิง' เท่านั้น ห้ามใช้ความรู้ภายนอก\n"
            "หากไม่พบคำตอบในข้อมูลอ้างอิง ให้แจ้งว่า 'ไม่พบข้อมูลที่เกี่ยวข้อง'\n"
            "ต้องระบุเลขที่หนังสืออ้างอิงในรูปแบบ 'เลขที่หนังสือ: [กคxxxx/xxxx]' เสมอ\n\n"
            "### ข้อมูลอ้างอิง:\n"
            f"{context}\n\n"
            f"### คำถาม:\n{question}\n\n"
            "### คำตอบ (สั้นและได้ใจความ):"
        )
