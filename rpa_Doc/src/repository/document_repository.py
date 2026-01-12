# src/repository/document_repository.py
import json
import os
import pickle
import re
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from src.config.settings import FILE_PATHS, SCRAPER_CONFIG

class DocumentRepository:
    def __init__(self):
        self.doc_file = FILE_PATHS.get("month_document_contents_filtered", FILE_PATHS["month_document_urls_filtered"])
        self.embed_file = FILE_PATHS["tfidf_embeddings"]
        self.debug = True

    def _clean_text(self, text: str) -> str:
        """ทำความสะอาดข้อความเพื่อเพิ่มประสิทธิภาพการค้นหา"""
        if not text: return ""
        # ลบ HTML Tags (ถ้ามี)
        text = re.sub(r'<[^>]+>', '', text)
        # ลบช่องว่างที่ซ้ำซ้อน
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_doc_id(self, doc_obj: Dict, title: str) -> str:
        """สกัดเลขที่หนังสือ (เช่น กค 0702/1234) โดยเช็คจาก field และ title"""
        # 1. ลองดึงจาก field โดยตรง (ถ้ามี)
        doc_id = doc_obj.get("เลขที่หนังสือ", "")
        if not doc_id:
            # ลองค้นหา key ที่อาจจะคล้ายกัน (กรณี encoding)
            for k in doc_obj.keys():
                if "เลขที่" in k:
                    doc_id = doc_obj[k]
                    break

        if doc_id: 
            return self._clean_text(doc_id)
        
        # 2. ถ้าไม่มี ให้ลองสกัดจาก Title ด้วย Regex
        if not title: return ""
        match = re.search(r'[ก-ฮ]{1,2}\s?\d{4,}/?\s?\d{0,}', title)
        if match:
            return match.group(0).strip()
        return ""

    def load_documents(self) -> List[Dict]:
        """โหลดเอกสารและแปลงเป็น Chunks สำหรับ Search"""
        if not os.path.exists(self.doc_file):
            raise FileNotFoundError(f"ไม่พบไฟล์เอกสาร: {self.doc_file}")

        with open(self.doc_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        chunks = []
        if isinstance(raw_data, list) and len(raw_data) > 0 and "month" in raw_data[0]:
            for month_data in raw_data:
                for doc in month_data.get("documents", []):
                    title = self._clean_text(doc.get('title', ''))
                    problem = self._clean_text(doc.get('ข้อหารือ', ''))
                    solution = self._clean_text(doc.get('แนววินิจฉัย', ''))
                    doc_id = self._extract_doc_id(doc, title)
                    
                    search_text = f"{title} {problem} {solution}"
                    chunks.append({
                        "search_text": search_text,
                        "title": title,
                        "doc_id": doc_id,
                        "content": f"ข้อหารือ: {problem}\nแนววินิจฉัย: {solution}",
                        "full_obj": doc
                    })
        else:
            for doc in raw_data:
                title = self._clean_text(doc.get('title', ''))
                content = self._clean_text(doc.get('content', ''))
                doc_id = self._extract_doc_id(doc, title)
                
                chunks.append({
                    "search_text": f"{title} {content}",
                    "title": title,
                    "doc_id": doc_id,
                    "content": content,
                    "full_obj": doc
                })
        
        return chunks

    def get_retriever(self, chunks: List[Dict]):
        """Load or Create TF-IDF Embeddings"""
        corpus = [c["search_text"] for c in chunks]
        
        if os.path.exists(self.embed_file):
            with open(self.embed_file, "rb") as f:
                vectorizer, matrix = pickle.load(f)
            if matrix.shape[0] == len(chunks):
                return vectorizer, matrix
        
        # ปรับจูน Vectorizer ให้เหมาะกับสเปคต่ำ (ประหยัด RAM/CPU)
        vectorizer = TfidfVectorizer(
            analyzer="char_wb", 
            ngram_range=(2, 4),
            max_features=10000  # จำกัดจำนวนฟีเจอร์เพื่อประหยัด RAM
        )
        matrix = vectorizer.fit_transform(corpus)
        
        os.makedirs(os.path.dirname(self.embed_file), exist_ok=True)
        with open(self.embed_file, "wb") as f:
            pickle.dump((vectorizer, matrix), f)
            
        return vectorizer, matrix
