import json
import os
from urllib.parse import urljoin
from playwright.sync_api import Page
from src.config.settings import FILE_PATHS, SCRAPER_CONFIG


def collect_years(page: Page):
    output_file = FILE_PATHS["years"]
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    years = []
    seen = set()

    page.goto(SCRAPER_CONFIG["base_url"])
    page.wait_for_selector(SCRAPER_CONFIG["year_selector"], timeout=SCRAPER_CONFIG["selector_timeout"])

    anchors = page.locator(SCRAPER_CONFIG["year_selector"]).all()

    for a in anchors:
        title = a.get_attribute("title")
        if title and title.isdigit() and len(title) == 4:
            if title in seen:
                continue

            href = a.get_attribute("href")
            full_url = urljoin(page.url, href)

            years.append({"year": title, "url": full_url})
            seen.add(title)

    years.sort(key=lambda x: int(x["year"]), reverse=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(years, f, ensure_ascii=False, indent=2)

    if years:
        print(f"[OK] Collected {len(years)} years -> {output_file}")
    else:
        print("[NOT_OK] No years collected")
