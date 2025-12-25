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
OLLAMA_MODEL = "llama3.2:1b"
# ----------------------------------------


# ---------------- UTILS ----------------
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    print("=" * 60)
    print("🤖 ระบบค้นหาเอกสารราชการ (RAG + Ollama)")
    print("พิมพ์คำถามได้เหมือน ChatGPT")
    print("คำสั่งพิเศษ: /help  /clear  /exit")
    print("=" * 60)


def read_multiline_input(prompt="You: "):
    """
    รับ input หลายบรรทัด
    จบด้วยบรรทัดว่าง
    """
    print(prompt, end="", flush=True)
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()


# ---------------- LOAD DATA ----------------
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

    print(f"📌 โหลดเอกสารทั้งหมด: {len(chunks)} เรื่อง")
    return chunks


def load_or_create_embeddings(chunks):
    if os.path.exists(EMBED_FILE):
        with open(EMBED_FILE, "rb") as f:
            vectorizer, X = pickle.load(f)
        print("📌 โหลด embeddings ที่มีอยู่แล้ว")
    else:
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(chunks)

        os.makedirs(os.path.dirname(EMBED_FILE), exist_ok=True)
        with open(EMBED_FILE, "wb") as f:
            pickle.dump((vectorizer, X), f)

        print("📌 สร้าง embeddings ใหม่เรียบร้อย")

    return vectorizer, X


# ---------------- SEARCH ----------------
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


# ---------------- OLLAMA ----------------
def ask_ollama(prompt):
    print("\n🤖 AI กำลังประมวลผล...\n")

    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60
        )

        if result.returncode != 0:
            print("❌ Ollama error:")
            print(result.stderr)
            return None

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        print("❌ Ollama ใช้เวลานานเกินไป")
        return None


# ---------------- MAIN CHAT LOOP ----------------
def main():
    clear_screen()
    print_header()

    chunks = load_documents()
    vectorizer, X = load_or_create_embeddings(chunks)

    while True:
        question = read_multiline_input("\nYou:\n")

        if not question:
            continue

        if question.lower() in ["/exit", "exit", "quit"]:
            print("\n👋 ออกจากระบบ")
            break

        if question.lower() == "/clear":
            clear_screen()
            print_header()
            continue

        if question.lower() == "/help":
            print("\n📖 วิธีใช้งาน")
            print("- พิมพ์คำถามได้หลายบรรทัด")
            print("- กด Enter บรรทัดว่างเพื่อส่งคำถาม")
            print("- /clear ล้างหน้าจอ")
            print("- /exit ออก")
            continue

        # --------- SEARCH ---------
        search_results = search_chunks(question, vectorizer, X, chunks)

        print("\n🔍 เอกสารที่ระบบเลือกมาอ้างอิง:")
        context_text = ""

        for i, res in enumerate(search_results):
            score_pct = res["score"] * 100
            book_id = "ไม่ระบุ"

            for line in res["text"].split("\n"):
                if "เลขที่หนังสือ:" in line:
                    book_id = line.replace("เลขที่หนังสือ:", "").strip()

            print(f" {i+1}. {book_id} ({score_pct:.2f}%)")
            context_text += f"--- เอกสารที่ {i+1} ---\n{res['text']}\n\n"

        # --------- PROMPT ---------
        prompt = (
            "คุณคือผู้ช่วยด้านกฎหมายและเอกสารราชการ\n"
            "ตอบคำถามโดยอ้างอิงจากข้อมูลด้านล่างเท่านั้น\n"
            "สำคัญ: ต้องระบุ 'เลขที่หนังสือ' ที่ใช้อ้างอิงในคำตอบทุกครั้ง\n\n"
            "========== ข้อมูลอ้างอิง ==========\n"
            + context_text +
            "========== คำถาม ==========\n"
            + question +
            "\n\n========== คำตอบ ==========\n"
        )

        answer = ask_ollama(prompt)

        if answer:
            print("\nAI:")
            print("-" * 60)
            print(answer)
            print("-" * 60)
        else:
            print("⚠️ ไม่สามารถสร้างคำตอบได้")


if __name__ == "__main__":
    main()
