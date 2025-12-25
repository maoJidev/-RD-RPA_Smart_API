import json
import os
import sys
import pickle
import subprocess

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- CONFIG ----------------
DOC_FILE = "output/month_document_contents_filtered.json"
EMBED_FILE = "output/tfidf_embeddings.pkl"
TOP_K = 2
OLLAMA_MODEL = "llama3.2:1b"   # ต้องมีในเครื่อง (ollama pull llama3)
# ----------------------------------------

def load_documents():
    if not os.path.exists(DOC_FILE):
        print(f"❌ ไม่พบไฟล์ {DOC_FILE}")
        sys.exit(1)

    with open(DOC_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    for month in data:
        for doc in month.get("documents", []):
            text = (
                f"เลขที่หนังสือ: {doc.get('เลขที่หนังสือ','')}\n"
                f"เรื่อง: {doc.get('เรื่อง','')}\n"
                f"ข้อกฎหมาย: {doc.get('ข้อกฎหมาย','')}\n"
                f"ข้อหารือ: {doc.get('ข้อหารือ','')}\n"
                f"แนววินิจฉัย: {doc.get('แนววินิจฉัย','')}"
            )
            chunks.append(text)

    print(f"📌 โหลดเอกสารทั้งหมด: {len(chunks)} chunks")
    return chunks

def load_or_create_embeddings(chunks):
    if os.path.exists(EMBED_FILE):
        with open(EMBED_FILE, "rb") as f:
            vectorizer, X = pickle.load(f)
        print("📌 โหลด embeddings ที่เคยสร้างไว้แล้ว")
    else:
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(chunks)

        os.makedirs(os.path.dirname(EMBED_FILE), exist_ok=True)
        with open(EMBED_FILE, "wb") as f:
            pickle.dump((vectorizer, X), f)

        print("📌 สร้าง embeddings ใหม่ และบันทึกเรียบร้อย")

    return vectorizer, X

def search_chunks(question, vectorizer, X, chunks, k=TOP_K):
    q_vec = vectorizer.transform([question])
    scores = cosine_similarity(q_vec, X)[0]
    top_ids = scores.argsort()[::-1][:k]
    
    results = []
    for i in top_ids:
        results.append({
            "text": chunks[i],
            "score": scores[i]
        })
    return results

def ask_ollama(prompt):
    print("🤖 กำลังคิดคำตอบ (อาจใช้เวลา 10–30 วินาที)...")

    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60   # ⏱️ สำคัญ
        )

        if result.returncode != 0:
            print("❌ Ollama error:")
            print(result.stderr)
            return None

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        print("❌ Ollama ใช้เวลานานเกินไป")
        return None

def main():
    chunks = load_documents()
    vectorizer, X = load_or_create_embeddings(chunks)

    print("🎉 ChatBot พร้อมใช้งาน! พิมพ์ 'exit' เพื่อออก")

    while True:
        question = input("\nถามเอกสารราชการ: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        search_results = search_chunks(question, vectorizer, X, chunks)
        
        context_text = ""
        print("\n🔍 ระบบค้นหาข้อมูลที่ใกล้เคียงที่สุด:")
        for i, res in enumerate(search_results):
            score_pct = res['score'] * 100
            # ดึงเลขที่หนังสือมาโชว์ใน Terminal เพื่อความโปร่งใส
            book_id = "ไม่ระบุ"
            for line in res['text'].split('\n'):
                if "เลขที่หนังสือ:" in line:
                    book_id = line.replace("เลขที่หนังสือ:", "").strip()
            
            print(f" {i+1}. [{book_id}] - ความมั่นใจ: {score_pct:.2f}%")
            context_text += f"--- ข้อมูลที่ {i+1} ---\n{res['text']}\n\n"

        prompt = (
            "คุณคือผู้ช่วยด้านกฎหมายและเอกสารราชการ\n"
            "ตอบคำถามโดยอ้างอิงจากข้อมูลด้านล่างเท่านั้น\n"
            "สำคัญ: ต้องระบุ 'เลขที่หนังสือ' ที่ใช้อ้างอิงในคำตอบด้วยทุกครั้ง\n\n"
            "========== ข้อมูลอ้างอิง ==========\n"
            + context_text
            + "========== คำถาม ==========\n"
            + question
            + "\n\n========== คำตอบ ==========\n"
        )

        answer = ask_ollama(prompt)
        if answer:
            print("\n🤖 คำตอบจาก AI:")
            print("-" * 30)
            print(answer)
            print("-" * 30)
        else:
            print("⚠️ ไม่สามารถขอคำตอบจาก AI ได้")

if __name__ == "__main__":
    main()
