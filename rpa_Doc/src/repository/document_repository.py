# src/repository/document_repository.py
import json
import os
import pickle
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from src.config.settings import FILE_PATHS, SCRAPER_CONFIG

class DocumentRepository:
    def __init__(self):
        self.doc_file = FILE_PATHS.get("month_document_contents_filtered", FILE_PATHS["month_document_urls_filtered"])
        self.embed_file = FILE_PATHS["tfidf_embeddings"]
        self.debug = True

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
                    search_text = f"{doc.get('title', '')} {doc.get('ข้อหารือ', '')} {doc.get('แนววินิจฉัย', '')}"
                    chunks.append({
                        "search_text": search_text,
                        "title": doc.get("title", ""),
                        "content": f"ข้อหารือ: {doc.get('ข้อหารือ', '')}\nแนววินิจฉัย: {doc.get('แนววินิจฉัย', '')}",
                        "full_obj": doc
                    })
        else:
            for doc in raw_data:
                chunks.append({
                    "search_text": f"{doc.get('title', '')} {doc.get('content', '')}",
                    "title": doc.get("title", ""),
                    "content": doc.get("content", ""),
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
        
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        matrix = vectorizer.fit_transform(corpus)
        
        os.makedirs(os.path.dirname(self.embed_file), exist_ok=True)
        with open(self.embed_file, "wb") as f:
            pickle.dump((vectorizer, matrix), f)
            
        return vectorizer, matrix
