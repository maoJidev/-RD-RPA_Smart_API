import re
from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from src.repository.document_repository import DocumentRepository

class RetrievalService:
    def __init__(self):
        self.doc_repo = DocumentRepository()
        self.top_k_docs = 2 # เพิ่มเป็น 2 เพื่อให้ครอบคลุมขึ้น
        self.min_similarity = 0.15 # ปรับเกณฑ์ขั้นต่ำให้สูงขึ้นเพื่อลด Noise
        self.window_size = 600 # ขยายหน้าต่างข้อมูลเป็น 600 ตัวอักษร
        self.overlap = 100 # เพิ่ม overlap เป็น 100

    def retrieve_hits(self, question: str) -> Tuple[List[Dict], List[Dict]]:
        """ดึงเอกสารและทำการซอยเป็นส่วนย่อยเพื่อหาความแม่นยำสูงสุด (Low-Spec Optimized)"""
        all_chunks = self.doc_repo.load_documents()
        vectorizer, matrix = self.doc_repo.get_retriever(all_chunks)
        
        q_vec = vectorizer.transform([question])
        scores = cosine_similarity(q_vec, matrix).flatten()

        # Step 1: หา 1-2 เอกสารที่คะแนนดีที่สุด
        doc_indices = scores.argsort()[::-1][:self.top_k_docs]
        
        final_hits = []
        for idx in doc_indices:
            if scores[idx] < self.min_similarity: continue
            
            doc = all_chunks[idx]
            # Step 2: ทำ Sliding Window (ซอยเนื้อหาเอกสารเป็นส่วนย่อย)
            sub_segments = self._split_with_overlap(doc["content"], self.window_size, self.overlap)
            
            # Step 3: หา segment ที่ตรงที่สุดในเอกสารนั้น
            if sub_segments:
                seg_matrix = vectorizer.transform(sub_segments)
                seg_scores = cosine_similarity(q_vec, seg_matrix).flatten()
                
                best_seg_idx = seg_scores.argmax()
                best_content = sub_segments[best_seg_idx]
                
                final_hits.append({
                    "score": float(scores[idx]),
                    "doc": {
                        "title": doc["title"],
                        "doc_id": doc["doc_id"], # ส่งต่อ ID ไปด้วย
                        "content": best_content
                    }
                })

        return all_chunks, final_hits

    def _split_with_overlap(self, text: str, size: int, overlap: int) -> List[str]:
        """แบ่งข้อความแบบมีส่วนซ้อนทับป้องกันข้อมูลตกหล่น"""
        if len(text) <= size: return [text]
        
        segments = []
        start = 0
        while start < len(text):
            end = start + size
            segments.append(text[start:end])
            start += (size - overlap)
            if end >= len(text): break
        return segments

    def build_context(self, hits: List[Dict]) -> Tuple[str, List[Dict]]:
        ctx = ""
        detailed_refs = []
        for i, h in enumerate(hits):
            doc = h["doc"]
            doc_id_label = f" ({doc['doc_id']})" if doc['doc_id'] else ""
            ctx += f"\n--- เอกสาร: {doc['title']}{doc_id_label} ---\n{doc['content']}\n"
            detailed_refs.append({
                "title": doc['title'],
                "doc_id": doc.get('doc_id'),
                "score": round(h["score"], 4), 
                "is_primary": i == 0
            })
        
        # สำหรับสเปคต่ำ จำกัด Context เพียง 1,000 ตัวอักษร ให้ AI สรุปได้เร็ว
        return ctx[:1000], detailed_refs
