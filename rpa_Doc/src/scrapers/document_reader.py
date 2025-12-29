import json
import os
from urllib.parse import urljoin
from playwright.sync_api import Page, TimeoutError
from src.config.settings import FILE_PATHS, SCRAPER_CONFIG

INPUT_FILE = FILE_PATHS["month_document_urls"]
OUTPUT_FILE = FILE_PATHS["month_document_contents"]

def extract_field_from_table(page: Page, label: str) -> str:
    """Helper: ดึง text จาก table row ที่มี label ระบุ"""
    try:
        # หา tr ที่มี td ที่มี strong/span ตรงกับ label
        xpath = f"//tr[td[contains(., '{label}')]]"
        row = page.locator(xpath).first
        if row.count() > 0:
            # สมมุติโครงสร้าง: <td>Label</td> <td>Content</td>
            content = row.locator("td").nth(1).inner_text().strip()
            # ลบ colon นำหน้าถ้ามี (เช่น ": ข้อความ")
            if content.startswith(":"):
                content = content[1:].strip()
            return content
    except:
        pass
    return ""

def read_single_document(page: Page, url: str):
    """อ่านข้อมูลจากหน้าเอกสารรายตัว"""
    try:
        page.goto(url, timeout=SCRAPER_CONFIG["page_timeout"])
        page.wait_for_load_state("domcontentloaded")
        
        # ตรวจสอบว่าเป็นหน้า List ย่อยหรือไม่ (กรณี 1 link มีหลายเรื่อง)
        # ถ้ามีคำว่า "เรื่อง" โผล่มาใน table header ส่วนมากจะเป็น list
        # แต่วิธีที่ง่ายสุดคือดึงข้อมูลแบบหน้าเดี่ยวก่อน ถ้าไม่เจอค่อยว่ากัน
        
        doc_data = {
            "title": "",
            "url": url,
            "เลขที่หนังสือ": extract_field_from_table(page, "เลขที่หนังสือ"),
            "วันที่": extract_field_from_table(page, "วันที่"),
            "เรื่อง": extract_field_from_table(page, "เรื่อง"),
            "ข้อกฎหมาย": extract_field_from_table(page, "ข้อกฎหมาย"),
            "ข้อหารือ": extract_field_from_table(page, "ข้อหารือ"),
            "แนววินิจฉัย": extract_field_from_table(page, "แนววินิจฉัย")
        }
        
        # Fallback for title if empty
        if not doc_data["title"]:
             doc_data["title"] = doc_data["เรื่อง"]
             
        return doc_data

    except TimeoutError:
        print(f"[WARN] Timeout reading content: {url}")
        return None
    except Exception as e:
        print(f"[ERR] Error reading {url}: {e}")
        return None

def run_read_document_content(page: Page):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        months = json.load(f)

    results = []
    total_docs = 0

    for m in months:
        print(f"[INFO] Processing Content: {m['year']} {m['month']}")
        documents = []

        for item in m.get("documents", []):
            url = item["url"]
            print(f"   Reading -> {url}")
            
            data = read_single_document(page, url)
            if data and (data["ข้อหารือ"] or data["แนววินิจฉัย"]):
                # ใช้ Title เดิมถ้าดึงไม่ได้
                if not data["title"]:
                    data["title"] = item.get("title", "")
                documents.append(data)
                total_docs += 1
            else:
                print(f"   [SKIP] No content found or empty.")

        if documents:
            results.append({
                "year": m["year"],
                "month": m["month"],
                "documents": documents
            })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[OK] Total Documents with Content: {total_docs}")
    print(f"[OK] Saved to -> {OUTPUT_FILE}")
