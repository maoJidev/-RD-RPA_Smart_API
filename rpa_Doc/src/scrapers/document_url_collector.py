import json
import os
import re
from urllib.parse import urljoin
from playwright.sync_api import Page
from src.config.settings import FILE_PATHS, SCRAPER_CONFIG

MONTHS_FILE = FILE_PATHS["months"]
OUTPUT_FILE = FILE_PATHS["month_document_urls"]
DOC_PATTERN = re.compile(r"/\d+\.html$")


def run_collect_month_urls(page: Page):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(MONTHS_FILE, "r", encoding="utf-8") as f:
        months = json.load(f)

    results = []
    total_documents = 0

    for m in months:
        print(f"[INFO] Processing {m['year']} {m['month']}")
        page.goto(m["url"], timeout=SCRAPER_CONFIG["page_timeout"])
        page.wait_for_load_state("domcontentloaded")

        links = []
        anchors = page.locator("a").all()
        for a in anchors:
            title = a.inner_text().strip()
            href = a.get_attribute("href")
            if title and href and DOC_PATTERN.search(href):
                links.append({
                    "title": title,
                    "url": urljoin(page.url, href)
                })

        if links:
            print(f"[OK] Found {len(links)} documents")
        else:
            print("[NOT_OK] No documents found")

        total_documents += len(links)
        results.append({
            "year": m["year"],
            "month": m["month"],
            "month_no": m["month_no"],
            "month_url": m["url"],
            "total_documents": len(links),
            "documents": links
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[OK] Output saved -> {OUTPUT_FILE}")
