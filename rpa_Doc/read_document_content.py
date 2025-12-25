import json
import os
from playwright.sync_api import Page, TimeoutError

OUTPUT_DIR = "output"
INPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_urls.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_contents.json")


def extract_field_from_table(page: Page, label: str) -> str:
    """
    ดึงข้อมูลจาก table row <tr> ที่มี label
    label เช่น 'เรื่อง', 'เลขที่หนังสือ', 'ข้อหารือ'
    """
    try:
        # หา tr ที่มี label
        row = page.locator(f"xpath=//tr[td/strong[contains(normalize-space(), '{label}')]]").first
        if row.count() == 0:
            return ""
        # ดึง td ตัวที่สอง ซึ่งเป็น content
        content = row.locator("td").nth(1).inner_text().strip()
        # ลบ colon ข้างหน้า
        if content.startswith(":"):
            content = content[1:].strip()
        return content
    except Exception as e:
        print(f"⚠️ ไม่สามารถดึงข้อมูล '{label}' ได้: {e}")
        return ""


def read_single_document(page: Page, url: str, fallback_title: str) -> dict:
    """
    อ่านข้อมูลเอกสารจาก URL
    """
    try:
        page.goto(url, timeout=20000)
        page.wait_for_load_state("domcontentloaded")
    except TimeoutError:
        print(f"⚠️ โหลดหน้าเว็บ {url} timeout")
        return {"title": fallback_title, "url": url}

    data = {
        "title": fallback_title,
        "url": url,
        "เลขที่หนังสือ": extract_field_from_table(page, "เลขที่หนังสือ"),
        "วันที่": extract_field_from_table(page, "วันที่"),
        "เรื่อง": extract_field_from_table(page, "เรื่อง"),
        "ข้อกฎหมาย": extract_field_from_table(page, "ข้อกฎหมาย"),
        "ข้อหารือ": extract_field_from_table(page, "ข้อหารือ"),
        "แนววินิจฉัย": extract_field_from_table(page, "แนววินิจฉัย"),
    }

    return data


def run_read_document_content(page: Page):
    """
    อ่านเนื้อหาเอกสารทั้งหมดจากไฟล์ month_document_urls.json
    และบันทึกเป็น month_document_contents.json
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # โหลด JSON input
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        months = json.load(f)

    results = []

    for m in months:
        print(f"\n📄 อ่านเอกสาร: {m['year']} {m['month']}")

        docs = []

        for item in m.get("links", []):
            print(f"   🔗 {item['url']}")
            doc = read_single_document(page, item["url"], item.get("title", ""))
            docs.append(doc)

        results.append({
            "year": m["year"],
            "month": m["month"],
            "month_no": m.get("month_no", ""),
            "documents": docs
        })

    # บันทึกผลลัพธ์
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 บันทึกเนื้อหาเอกสาร -> {OUTPUT_FILE}")


# ตัวอย่างเรียกใช้งาน (ในไฟล์จริงให้ใช้ context/page ของ Playwright)
if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_read_document_content(page)
        browser.close()
