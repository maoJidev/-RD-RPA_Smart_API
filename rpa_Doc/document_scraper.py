import json
import os
import random
import time
from urllib.parse import urljoin
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

# =========================
# CONFIG
# =========================
OUTPUT_DIR = "output"
MONTHS_FILE = os.path.join(OUTPUT_DIR, "months.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "rd_discussion_with_count.json")

MAX_DOCS_PER_MONTH = 20     # 👈 ทดสอบ 10 เรื่องก่อน (ปรับได้)
FAST_MODE = True

SLEEP_SHORT = (400, 800)
SLEEP_DETAIL = (800, 1500)
ERROR_SLEEP_SEC = 3


# =========================
# UTILS
# =========================
def human_sleep(page: Page, ms_range):
    page.wait_for_timeout(random.randint(*ms_range))


# =========================
# PARSE DETAIL
# =========================
def parse_document_detail(page: Page) -> dict:
    page.wait_for_selector("table", timeout=10000)

    data = {
        "เลขที่หนังสือ": "",
        "วันที่": "",
        "เรื่อง": "",
        "ข้อกฎหมาย": "",
        "ข้อหารือ": "",
        "แนววินิจฉัย": ""
    }

    rows = page.locator("table tr").all()  # ✅ ไม่ใช้ tbody

    for row in rows:
        tds = row.locator("td").all()
        if len(tds) < 2:
            continue

        key = tds[0].inner_text().strip()
        val = tds[1].inner_text().strip()

        if "เลขที่หนังสือ" in key:
            data["เลขที่หนังสือ"] = val
        elif "วันที่" in key:
            data["วันที่"] = val
        elif key.startswith("เรื่อง"):
            data["เรื่อง"] = val
        elif "ข้อกฎหมาย" in key:
            data["ข้อกฎหมาย"] = val
        elif "ข้อหารือ" in key:
            data["ข้อหารือ"] = val
        elif "แนววินิจฉัย" in key:
            data["แนววินิจฉัย"] = val

    return data



# =========================
# COLLECT LINKS (ALL PAGES)
# =========================
def collect_all_document_links(page: Page, month_url: str):
    links = []
    visited_pages = set()
    collected_urls = set()

    page.goto(month_url, timeout=20000)
    page.wait_for_load_state("domcontentloaded")

    while True:
        if page.url in visited_pages:
            break
        visited_pages.add(page.url)

        page.wait_for_selector("a", timeout=10000)

        # ✅ เก็บ <a> ทุกตัวที่ชี้ไป .html
        anchors = page.locator("a[href$='.html']").all()

        for a in anchors:
            try:
                title = a.inner_text().strip()
                href = a.get_attribute("href")

                if not title or not href:
                    continue

                # ❌ ตัด pagination / เลขหน้า
                if title.isdigit():
                    continue

                full_url = urljoin(page.url, href)

                # ❌ กันซ้ำ
                if full_url in collected_urls:
                    continue

                collected_urls.add(full_url)

                links.append({
                    "title": title,
                    "url": full_url
                })
            except:
                continue

        # 🔁 หา pagination page ถัดไป (แบบ generic)
        next_page_found = False
        for a in anchors:
            txt = a.inner_text().strip()
            href = a.get_attribute("href")

            if not href or not txt.isdigit():
                continue

            next_url = urljoin(page.url, href)
            if next_url not in visited_pages:
                page.goto(next_url, timeout=20000)
                page.wait_for_load_state("domcontentloaded")
                next_page_found = True
                break

        if not next_page_found:
            break

    return links


# =========================
# MAIN
# =========================
def scrape_documents_with_count(page: Page):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    months = [
        {
            "year": "2545",
            "month": "ตุลาคม",
            "month_no": 10,
            "url": "https://www.rd.go.th/24852.html"
        },
        {
            "year": "2545",
            "month": "กรกฎาคม",
            "month_no": 7,
            "url": "https://www.rd.go.th/24843.html"
        },
        {
            "year": "2545",
            "month": "มิถุนายน",
            "month_no": 6,
            "url": "https://www.rd.go.th/24844.html"
        },
        {
            "year": "2545",
            "month": "พฤษภาคม",
            "month_no": 5,
            "url": "https://www.rd.go.th/24845.html"
        },
        {
            "year": "2545",
            "month": "เมษายน",
            "month_no": 4,
            "url": "https://www.rd.go.th/24846.html"
        },
        {
            "year": "2545",
            "month": "มีนาคม",
            "month_no": 3,
            "url": "https://www.rd.go.th/24847.html"
        }
    ]

    all_results = []

    for m in months:
        print(f"\n📄 {m['year']} {m['month']}")

        try:
            links = collect_all_document_links(page, m["url"])
        except Exception as e:
            print(f"⚠️ ดึงลิงก์ไม่ได้: {e}")
            continue

        print(f"   🔎 พบทั้งหมด {len(links)} เรื่อง")

        documents = []

        for item in links[:MAX_DOCS_PER_MONTH]:
            try:
                print(f"   ▶ {item['title']}")
                page.goto(item["url"], timeout=20000)
                human_sleep(page, SLEEP_DETAIL)

                detail = parse_document_detail(page)

                full_text = (
                    detail["ข้อกฎหมาย"]
                    + detail["ข้อหารือ"]
                    + detail["แนววินิจฉัย"]
                )

                documents.append({
                    "เรื่อง": detail["เรื่อง"] or item["title"],
                    "เลขที่หนังสือ": detail["เลขที่หนังสือ"],
                    "วันที่": detail["วันที่"],
                    "ข้อกฎหมาย": detail["ข้อกฎหมาย"],
                    "ข้อหารือ": detail["ข้อหารือ"],
                    "แนววินิจฉัย": detail["แนววินิจฉัย"],
                    "content_length": len(full_text),
                    "content_lines": len(full_text.splitlines()),
                    "url": item["url"]
                })

            except Exception as e:
                print(f"⚠️ ข้ามเรื่อง: {e}")
                time.sleep(ERROR_SLEEP_SEC)

        all_results.append({
            "year": m["year"],
            "month": m["month"],
            "month_no": m["month_no"],
            "url": m["url"],
            "total_topics": len(documents),
            "documents": documents
        })

        print(f"   ✅ บันทึก {len(documents)} เรื่อง")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 เสร็จสิ้น -> {OUTPUT_FILE}")
