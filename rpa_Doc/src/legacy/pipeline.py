# src/rag/pipeline.py
"""
Backward Compatibility Layer:
This file is kept to ensure that older components (like Streamlit UI) 
can still call run_pipeline without breaking.
"""
from src.api.services.rag_service import RAGService

# Singleton instance
_service = RAGService()

def run_pipeline(question: str, **kwargs) -> str:
    """
    Wrapper around the new RAGService for backward compatibility.
    """
    return _service.ask_question(question)

# For direct testing
if __name__ == "__main__":
    print(run_pipeline("นำเข้าอาหารสัตว์ต้องเสีย vat ไหม"))