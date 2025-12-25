import json
import os
import re
from urllib.parse import urljoin
from playwright.sync_api import Page

OUTPUT_DIR = "output"
MONTHS_FILE = os.path.join(OUTPUT_DIR, "months.json")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "month_document_urls.json")

DOC_PATTERN = re.compile(r"/\d+\.html$")


def collect_all_document_links(page: Page, month_url: str):
    links = []
    collected_urls = set()
    visited_pages = set()

    page.goto(month_url, timeout=20000)
    page.wait_for_load_state("domcontentloaded")

    while True:
        if page.url in visited_pages:
            break
        visited_pages.add(page.url)

        page.wait_for_selector("table")

        rows = page.locator("table tr").all()

        for row in rows:
            tds = row.locator("td").all()
            if len(tds) < 2:
                continue

            anchors = tds[1].locator("a").all()

            for a in anchors:
                try:
                    title = a.inner_text().strip()
                    href = a.get_attribute("href")

                    if not title or not href:
                        continue

                    if not DOC_PATTERN.search(href):
                        continue

                    full_url = urljoin(page.url, href)

                    if full_url in collected_urls:
                        continue

                    collected_urls.add(full_url)
                    links.append({
                        "title": title,
                        "url": full_url
                    })
                except:
                    continue

        # 🔁 pagination (เฉพาะหัวตาราง)
        next_page = None
        pager_links = page.locator(
            "p.text-right a, div[align='right'] a"
        ).all()

        for a in pager_links:
            txt = a.inner_text().strip()
            href = a.get_attribute("href")

            if txt.isdigit() and href:
                candidate = urljoin(page.url, href)
                if candidate not in visited_pages:
                    next_page = candidate
                    break

        if next_page:
            page.goto(next_page, timeout=20000)
            page.wait_for_load_state("domcontentloaded")
        else:
            break

    return links


def run_collect_month_urls(page: Page):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(MONTHS_FILE, "r", encoding="utf-8") as f:
        months = json.load(f)

    results = []

    for m in months:
        print(f"\n📄 {m['year']} {m['month']}")

        links = collect_all_document_links(page, m["url"])
        print(f"   🔎 พบ {len(links)} เรื่อง")

        results.append({
            "year": m["year"],
            "month": m["month"],
            "month_no": m["month_no"],
            "month_url": m["url"],
            "total_links": len(links),
            "links": links
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 บันทึก URL ทั้งหมด -> {OUTPUT_FILE}")
