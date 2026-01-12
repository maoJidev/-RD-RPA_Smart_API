from typing import List, Dict, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from src.repository.document_repository import DocumentRepository

class RetrievalService:
    def __init__(self):
        self.doc_repo = DocumentRepository()
        self.top_k = 2
        self.min_similarity = 0.05

    def retrieve_hits(self, question: str) -> Tuple[List[Dict], List[Dict]]:
        chunks = self.doc_repo.load_documents()
        vectorizer, matrix = self.doc_repo.get_retriever(chunks)
        
        q_vec = vectorizer.transform([question])
        scores = cosine_similarity(q_vec, matrix).flatten()

        hits = [
            {"score": float(scores[i]), "doc": chunks[i]}
            for i in scores.argsort()[::-1][:self.top_k]
            if scores[i] >= self.min_similarity
        ]

        return chunks, hits

    def build_context(self, hits: List[Dict]) -> Tuple[str, List[Dict]]:
        ctx = ""
        detailed_refs = []
        for i, h in enumerate(hits):
            doc = h["doc"]
            ctx += f"\n--- เอกสาร: {doc['title']} ---\n{doc['content']}\n"
            detailed_refs.append({
                "title": doc['title'], 
                "score": round(h["score"], 4), 
                "is_primary": i == 0
            })
        
        # Max context length to avoid blowing up LLM limit
        return ctx[:1500], detailed_refs
