#src/api/controllers/rag_router.py
from fastapi import APIRouter, HTTPException
import logging

from src.api.models.schemas import QuestionRequest, QuestionResponse
from src.api.services.rag_service import RAGService
from src.repository.log_repository import LogRepository

# ตั้งค่า Logger ให้เรียกใช้ตัวเดียวกับในระบบ RAG
logger = logging.getLogger("rag")

router = APIRouter(prefix="/rag", tags=["RAG"])

rag_service = RAGService()
log_repo = LogRepository()

@router.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    try:
        # 1. เรียกการทำงาน (จะมีการประมวลผลผ่านคิว Ollama)
        answer = rag_service.ask_question(request.question)
        
        # 2. ดึง Log ล่าสุดมาเพื่อส่งกลับข้อมูลอ้างอิงและ Domain
        last_log = log_repo.get_last_log() or {}
        
        # 3. จัดโครงสร้างข้อมูลส่งกลับตาม QuestionResponse Schema
        return QuestionResponse(
            answer=answer,
            main_reference=last_log.get("main_reference"),
            refs=last_log.get("refs", []),
            domain=last_log.get("domain", "ทั่วไป"),
            status=last_log.get("status", "success")
        )
    except HTTPException as he:
        # ถ้าเป็น Error ที่ตั้งใจส่งออกมาจาก Service (เช่น 503 Timeout) ให้ส่งต่อไปเลย
        raise he
    except Exception as e:
        # บันทึก Error ลง Log ไฟล์เพื่อใช้ตรวจสอบภายหลัง
        logger.error(f"Router error: {str(e)}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดภายในระบบกรุณาลองใหม่")

@router.get("/history")
def get_history():
    return log_repo.get_all_logs()