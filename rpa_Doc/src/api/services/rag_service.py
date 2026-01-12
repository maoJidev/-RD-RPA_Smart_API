import logging
from datetime import datetime
from fastapi import HTTPException
from src.repository.log_repository import LogRepository
from src.api.services.llm_service import LLMService
from src.api.services.retrieval_service import RetrievalService

logger = logging.getLogger("rag")

class RAGService:
    def __init__(self):
        self.log_repo = LogRepository()
        self.llm = LLMService()
        self.retrieval = RetrievalService()

    def ask_question(self, question: str) -> str:
        start_time = datetime.now()
        try:
            domain = self._detect_domain(question)
            
            # 1. Retrieval
            chunks, hits = self.retrieval.retrieve_hits(question)
            
            if not hits:
                return self._finalize(start_time, question, domain, [], "ไม่พบข้อมูลในฐานข้อมูล", "fail", "document")

            # 2. Context Construction
            context, detailed_refs = self.retrieval.build_context(hits)
            
            # 3. Prompt Construction
            prompt = self.llm.build_document_prompt(context, question)

            # 4. LLM Call
            answer = self.llm.call_ollama(prompt)
            
            return self._finalize(start_time, question, domain, detailed_refs, answer, "success", "document")

        except HTTPException: 
            raise
        except Exception as e:
            logger.exception("RAG Error")
            raise HTTPException(status_code=500, detail="ระบบขัดข้อง")

    def _detect_domain(self, q: str) -> str:
        return "ภาษีมูลค่าเพิ่ม" if any(x in q.lower() for x in ["vat", "ภาษีมูลค่าเพิ่ม"]) else "ทั่วไป"

    def _finalize(self, start_time, question, domain, refs, answer, status, source):
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