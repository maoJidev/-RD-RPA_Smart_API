import requests
import re
import threading
import queue
import logging
from datetime import datetime
from typing import List, Dict

from fastapi import HTTPException
from sklearn.metrics.pairwise import cosine_similarity

from src.config.settings import RAG_CONFIG, OLLAMA_BASE_URL
from src.repository.document_repository import DocumentRepository
from src.repository.log_repository import LogRepository

logger = logging.getLogger("rag")

class OllamaQueue:
    def __init__(self, maxsize=1):
        self.q = queue.Queue(maxsize=maxsize)
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def submit(self, func):
        try:
            result_q = queue.Queue(maxsize=1)
            self.q.put_nowait((func, result_q))
        except queue.Full:
            raise HTTPException(status_code=503, detail="ระบบหนาแน่น โปรดลองใหม่ในครู่เดียว")

        try:
            # เพิ่มเวลารอให้เหมาะสมกับข้อมูลที่เยอะขึ้น (เป็น 300 วินาที)
            return result_q.get(timeout=300)
        except queue.Empty:
            raise HTTPException(status_code=503, detail="ประมวลผลนานเกินไป (Timeout)")

    def _worker_loop(self):
        while True:
            func, result_q = self.q.get()
            try:
                result_q.put(func())
            except Exception as e:
                logger.error(f"Worker Error: {e}")
                result_q.put(e)
            finally:
                self.q.task_done()

class RAGService:
    def __init__(self):
        self.doc_repo = DocumentRepository()
        self.log_repo = LogRepository()
        self.ollama_url = f"{OLLAMA_BASE_URL}/api/generate"
        self.model = RAG_CONFIG["model"]

        # กลับมาใช้ 2 เอกสารเพื่อให้ครอบคลุมข้อมูล
        self.top_k = 2 
        self.min_similarity = 0.05
        self.connect_timeout = 10
        self.read_timeout = 240 

        self.ollama_queue = OllamaQueue(maxsize=1)

    def ask_question(self, question: str) -> str:
        start_time = datetime.now()
        try:
            chunks = self.doc_repo.load_documents()
            domain = self._detect_domain(question)

            vectorizer, matrix = self.doc_repo.get_retriever(chunks)
            q_vec = vectorizer.transform([question])
            scores = cosine_similarity(q_vec, matrix).flatten()

            hits = [
                {"score": float(scores[i]), "doc": chunks[i]}
                for i in scores.argsort()[::-1][:self.top_k]
                if scores[i] >= self.min_similarity
            ]

            if not hits:
                return self._finalize(start_time, question, domain, [], [], "ไม่พบข้อมูลในฐานข้อมูล", "fail", "document")

            # ขยาย Context กลับมาที่ 1,500 ตัวอักษร เพื่อให้ได้เนื้อหาที่ครบถ้วน
            context, detailed_refs = self._build_context(hits)
            prompt = self._build_document_prompt(context, question)

            answer = self._call_ollama(prompt)
            return self._finalize(start_time, question, domain, [], detailed_refs, answer, "success", "document")

        except HTTPException: raise
        except Exception as e:
            logger.exception("RAG Error")
            raise HTTPException(status_code=500, detail="ระบบขัดข้อง")

    def _call_ollama(self, prompt: str) -> str:
        def _request():
            r = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1, 
                        "num_ctx": 1024,     # ขยายให้พอดีกับบริบทที่ส่งไป
                        "num_predict": 512,  # เผื่อคำตอบยาวขึ้น
                        "num_thread": 4      # เพิ่มการใช้ Core ถ้าเครื่องไหว
                    }
                },
                timeout=(self.connect_timeout, self.read_timeout)
            )
            r.raise_for_status()
            return r.json().get("response", "").strip()

        result = self.ollama_queue.submit(_request)
        if isinstance(result, Exception):
            raise HTTPException(status_code=503, detail="Ollama Error")
        return result

    def _detect_domain(self, q: str):
        return "ภาษีมูลค่าเพิ่ม" if any(x in q.lower() for x in ["vat", "ภาษีมูลค่าเพิ่ม"]) else "ทั่วไป"

    def _build_context(self, hits: List[Dict]):
        ctx = ""
        detailed_refs = []
        for i, h in enumerate(hits):
            doc = h["doc"]
            ctx += f"\n--- เอกสาร: {doc['title']} ---\n{doc['content']}\n"
            detailed_refs.append({"title": doc['title'], "score": round(h["score"], 4), "is_primary": i==0})
        # ขยายความยาวเป็น 1,500 เพื่อไม่ให้เนื้อหาส่วนสำคัญขาดหาย
        return ctx[:1500], detailed_refs 

    def _build_document_prompt(self, context, question):
        return (
            "คุณคือผู้เชี่ยวชาญด้านกฎหมายภาษี สรุปคำตอบจากเอกสารอ้างอิงที่ให้มาเท่านั้น\n"
            "หากในเอกสารกล่าวถึงการยกเว้นภาษีหรือเงื่อนไขใดๆ ให้ระบุมาให้ชัดเจน\n"
            "ข้อมูลอ้างอิง:\n"
            f"{context}\n\n"
            f"คำถาม: {question}\n"
            "คำตอบ (อ้างอิงเลขที่หนังสือด้วย):"
        )

    def _finalize(self, start_time, question, domain, docs, refs, answer, status, source):
        main_ref = next((r['title'] for r in refs if r.get('is_primary')), None)
        log_data = {
            "timestamp": start_time.isoformat(), 
            "question": question, 
            "domain": domain, 
            "main_reference": main_ref, 
            "refs": refs, 
            "answer": answer, 
            "status": status, 
            "answer_source": source
                }
        self.log_repo.save_log(log_data)
        return answer