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
                        "temperature": 0.1,
                        "num_ctx": 1024,
                        "num_predict": 512,
                        "num_thread": 4
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
            "คุณคือผู้เชี่ยวชาญด้านกฎหมายภาษี สรุปคำตอบจากเอกสารอ้างอิงที่ให้มาเท่านั้น\n"
            "หากในเอกสารกล่าวถึงการยกเว้นภาษีหรือเงื่อนไขใดๆ ให้ระบุมาให้ชัดเจน\n"
            "ข้อมูลอ้างอิง:\n"
            f"{context}\n\n"
            f"คำถาม: {question}\n"
            "คำตอบ (อ้างอิงเลขที่หนังสือด้วย):"
        )
