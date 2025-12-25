import json, os
from urllib.parse import urljoin
from playwright.sync_api import Page

def collect_years(page: Page):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "years.json")

    years = []
    seen = set()

    page.goto("https://www.rd.go.th/68047.html")

    # ✅ รอ sidebar จริงโหลด
    page.wait_for_selector("div.link-list-line div.list-menu ul li a[title]")

    anchors = page.locator(
        "div.link-list-line div.list-menu > ul > li > a[title]"
    ).all()

    for a in anchors:
        title = a.get_attribute("title")
        text = a.inner_text().strip()

        # ✔️ กรองเฉพาะปี พ.ศ.
        if title and title.isdigit() and len(title) == 4:
            if title in seen:
                continue

            href = a.get_attribute("href")
            full_url = urljoin(page.url, href)

            years.append({
                "year": title,
                "url": full_url
            })
            seen.add(title)

    # เรียงจากปีใหม่ → เก่า
    years.sort(key=lambda x: int(x["year"]), reverse=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(years, f, ensure_ascii=False, indent=2)

    print(f"✅ บันทึกปีทั้งหมด {len(years)} ปี -> {output_file}")
